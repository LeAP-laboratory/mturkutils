#!/usr/bin/env python3
#
# Copyright (c) 2012-2017 Andrew Watts and the University of Rochester BCS Department
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Load HITs to Mechanical Turk."""

import argparse
from datetime import timedelta
from pprint import pprint
from typing import Dict, List, Tuple, Union

import boto3

from ruamel.yaml import load, safe_dump, CLoader

from xmltodict import unparse

__author__ = 'Andrew Watts <awatts2@ur.rochester.edu>'


def create_external_question(url: str, height: int) -> str:
    """Create XML for an MTurk ExternalQuestion."""
    return unparse({
        'ExternalQuestion': {
            '@xmlns': 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd',
            'ExternalURL': url,
            'FrameHeight': height
        }
    }, full_document=False)


def format_locations(locations: Union[str, List, Tuple]) -> List[Dict[str, str]]:
    """
    Format locations from YAML file into the list format expected by boto3.

    Possible inputs are:
      a) A 2 letter country code string, e.g. "US"
      b) A 2-tuple (or 2 item list) of 2 letter country and subdivision codes , e.g ("US", "NY")
      c) A list of two or more instances of a) and/or b)
    """
    if isinstance(locations, str):
        return [{'Country': locations}]
    elif isinstance(locations, list) or isinstance(locations, tuple):
        return [{'Country': l[0], 'Subdivision': l[1]} if isinstance(l, (tuple, list))
             else {'Country': l} for l in locations]
    else:
        raise TypeError


def format_keywords(keywords: Union[str, List]) -> str:
    """
    Format keywords fromm YAML file into the comma string list expected by boto3.

    Possible inputs are:
      a) A comma string list, e.g. 'foo, bar, baz, qux'
      b) A list of strings, e.g. ['foo', 'bar', 'baz', 'qux']
    """
    if isinstance(keywords, str):
        return keywords
    elif isinstance(keywords, list):
        return ','.join(keywords)


builtin_requirements = {
    'AdultRequirement': '00000000000000000060',
    'LocaleRequirement': '00000000000000000071',
    'NumberHitsApprovedRequirement': '00000000000000000040',
    'PercentAssignmentsAbandonedRequirement': '00000000000000000070',
    'PercentAssignmentsApprovedRequirement': '000000000000000000L0',
    'PercentAssignmentsRejectedRequirement': '000000000000000000S0',
    'PercentAssignmentsReturnedRequirement': '000000000000000000E0',
    'PercentAssignmentsSubmittedRequirement': '00000000000000000000',
}

parser = argparse.ArgumentParser(description='Load a HIT into Amazon Mechanical Turk')
parser.add_argument('-c', '--config', required=True, help='YAML file with HIT configuration')
parser.add_argument('-s', '--sandbox', action='store_true',
                    help='Run the command in the Mechanical Turk Sandbox (used for testing purposes)')
parser.add_argument('-p', '--profile', help='Run commands using specific aws credentials rather the default.'
                                            'To set-up alternative credentials see '
                                            'http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

with open(args.config, 'r') as hitfile:
    hitfile_name = hitfile.name
    hitdata = load(hitfile, Loader=CLoader)

required_keys = ('description', 'title', 'assignments', 'keywords', 'reward', 'question')

abort = False
for k in required_keys:
    if k not in hitdata:
        print('{} is a required key in HIT file!'.format(k))
        abort = True
if abort:
    print('At least one required key missing; aborting HIT load')
    import sys
    sys.exit()

if 'input' in hitdata['question']:
    qurls = [hitdata['question']['url'].format(**row) for row in hitdata['question']['input']]
else:
    qurls = [hitdata['question']['url']]

questions = [create_external_question(url, hitdata['question']['height']) for url in qurls]

qualifications = []

if 'builtin' in hitdata['qualifications']:
    for b in hitdata['qualifications']['builtin']:
        if b['qualification'] == 'AdultRequirement':
            q = {
                'QualificationTypeId': builtin_requirements['AdultRequirement'],
                'Comparator': b['comparator'],
                'IntegerValue': 1,
                'RequiredToPreview': b['private']
            }
        elif b['qualification'] == 'LocaleRequirement':
            q = {
                'QualificationTypeId': builtin_requirements['LocaleRequirement'],
                'Comparator': b['comparator'],
                'LocaleValues': format_locations(b['locale']),
                'RequiredToPreview': b['private']
            }
        else:
            q = {
                'QualificationTypeId': builtin_requirements[b['qualification']],
                'Comparator': b['comparator'],
                'IntegerValues': [b['value']],
                'RequiredToPreview': b['private']
                 }
        qualifications.append(q)

if 'custom' in hitdata['qualifications']:
    for c in hitdata['qualifications']['custom']:
        q = {
            'QualificationTypeId': c['qualification'],
            'Comparator': c['comparator'],
            'RequiredToPreview': c.get('private', False)
        }
        if c['comparator'] not in ('Exists', 'DoesNotExist'):
            if isinstance(c['value'], (tuple, list)):
                q['IntegerValues'] = c['value']
            else:
                q['IntegerValues'] = [c['value']]

        qualifications.append(q)

endpoint = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com' if args.sandbox else 'https://mturk-requester.us-east-1.amazonaws.com'
# If you want to use profiles, you have to create a Session with one before connecting a client
session = boto3.Session(profile_name=args.profile)
# Only region w/ MTurk endpoint currently is us-east-1
mtc = session.client('mturk', endpoint_url=endpoint, region_name='us-east-1')

# Time defaults in boto are WAY too long
duration = timedelta(minutes=60).total_seconds()
if 'assignmentduration' in hitdata:
    duration = timedelta(seconds=hitdata['assignmentduration']).total_seconds()
lifetime = timedelta(days=2).total_seconds()
if 'hitlifetime' in hitdata:
    lifetime = timedelta(seconds=hitdata['hitlifetime']).total_seconds()
approvaldelay = timedelta(days=14).total_seconds()
if 'autoapprovaldelay' in hitdata:
    approvaldelay = timedelta(seconds=hitdata['autoapprovaldelay']).total_seconds()


created_hits = []
for q in questions:
    hit = mtc.create_hit(
        MaxAssignments=hitdata['assignments'],
        AutoApprovalDelayInSeconds=int(approvaldelay),
        LifetimeInSeconds=int(lifetime),
        AssignmentDurationInSeconds=int(duration),
        Reward=f"{hitdata['reward']:.2f}",
        Title=hitdata['title'],
        Keywords=format_keywords(hitdata['keywords']),
        Description=hitdata['description'],
        Question=q,
        RequesterAnnotation='',  # FIXME: get annotation if exists
        QualificationRequirements=qualifications
    )
    created_hits.append(hit.get('HIT', {}))

pprint(created_hits)

hit_list = [{'HITId': y['HITId'], 'HITTypeId': y['HITTypeId']} for y in created_hits]

outfilename = hitfile_name.split('.')
outfilename.insert(-1, 'success')
outfilename = '.'.join(outfilename)
with open(outfilename, 'w') as successfile:
    safe_dump(hit_list, stream=successfile, default_flow_style=False)

# TODO: integrate SQS notification stuff into here.

preview_url = 'https://workersandbox.mturk.com/mturk/preview?groupId={}' if args.sandbox else 'https://www.mturk.com/mturk/preview?groupId={}'

for hittypeid in {x['HITTypeId'] for x in hit_list}:
    print('You can preview your new HIT at:\n\t{}'.format(preview_url.format(hittypeid)))
    print('${0} is the final balance'.format(mtc.get_account_balance().get('AvailableBalance', 0)))

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

import argparse

import boto3

from ruamel.yaml import load, CLoader

from unicodecsv import DictWriter

import xmltodict

__author__ = 'Andrew Watts <awatts2@ur.rochester.edu>'


def manage_url(hitid: str, mturk_website: str) -> str:
    return 'https://{}/mturk/manageHIT?HITId={}'.format(
        mturk_website, hitid)


def process_assignment(assignment: dict, hitinfo: dict) -> dict:
    """Turn an Assignment dict as returned by boto3 into a row for results file."""
    optional_assignment_keys = {
        'AcceptTime': 'assignmentaccepttime', 'RejectTime': 'assignmentrejecttime', 'Deadline': 'deadline',
        'RequesterFeedback': 'feedback', 'ApprovalTime': 'assignmentapprovaltime'
    }
    print(f'Processing AssignmentId: {assignment["AssignmentId"]} for Worker: {assignment["WorkerId"]}')
    row = {
        'assignmentid': assignment['AssignmentId'],
        'assignmentstatus': assignment['AssignmentStatus'],
        'autoapprovaltime': assignment['AutoApprovalTime'],
        'hitid': assignment['HITId'],
        'viewhit': manage_url(assignment['HITId'], mturk_website),  # FIXME: use of global `mturk_website` impure!
        'assignmentsubmittime': assignment['SubmitTime'],
        'workerid': assignment['WorkerId'],
        # these assignment keys are optional
        'assignmentaccepttime': '',
        'assignmentapprovaltime': '',
        'assignmentrejecttime': '',
        'deadline': '',
        'feedback': '',
        # 'reject' is for processing results files to mark which rows are to be rejected with an x
        'reject': '',
        # HIT keys.
        'hittypeid': hitinfo['HITTypeId'],
        'hitgroupid': hitinfo['HITGroupId'],
        'title': hitinfo['Title'],
        'description': hitinfo['Description'],
        'keywords': hitinfo['Keywords'],
        'reward': '$' + hitinfo['Reward'],
        'creationtime': hitinfo['CreationTime'],
        'assignments': hitinfo['MaxAssignments'],
        'numavailable': hitinfo['NumberOfAssignmentsAvailable'],
        'numpending': hitinfo['NumberOfAssignmentsPending'],
        'numcomplete': hitinfo['NumberOfAssignmentsCompleted'],
        'hitstatus': hitinfo['HITStatus'],
        'reviewstatus': hitinfo['HITReviewStatus'],
        'assignmentduration': hitinfo['AssignmentDurationInSeconds'],
        'autoapprovaldelay': hitinfo['AutoApprovalDelayInSeconds'],
        'hitlifetime': hitinfo['Expiration'],
        'annotation': ''
    }

    # populate the optional keys if they exist
    for k, v in optional_assignment_keys.items():
        if k in assignment:
            row[v] = assignment[k]

    if 'QualificationRequirements' in hitinfo:
        for i, qual in enumerate(['|'.join(['{}:{}'.format(k, v) for k, v in x.items()]) for x in hitinfo['QualificationRequirements']]):
            qualkey = 'Qualification.{}'.format(i)
            row[qualkey] = qual
            answer_keys.add(qualkey)  # FIXME: more functional impurity!

    if 'RequesterAnnotation' in hitinfo:
        row['annotation'] = hitinfo['RequesterAnnotation']

    # answers are in assignment['Answer'] as an MTurk QuestionFormAnswers XML string
    ordered_answers = xmltodict.parse(assignment.get('Answer')).get('QuestionFormAnswers').get('Answer')
    # FIXME: answer might not be FreeText, but that's what I'm handling for now
    # http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QuestionFormAnswersDataStructureArticle.html
    # http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd
    user_answers = {'Answer.{}'.format(d['QuestionIdentifier']): d['FreeText'] for d in ordered_answers}
    answer_keys.update(set(user_answers.keys()))  # FIXME: more functional impurity!
    row.update(user_answers)

    return row


parser = argparse.ArgumentParser(description='Get results from Amazon Mechanical Turk')
parser.add_argument('-f', '--successfile', required=True, help='YAML file with HIT information')
parser.add_argument('-r', '--resultsfile', required=True, help='Filename for tab delimited CSV file')
parser.add_argument('-s', '--sandbox', action='store_true',
                    help='Run the command in the Mechanical Turk Sandbox (used for testing purposes)')
parser.add_argument('-p', '--profile',
                    help='Run commands using specific aws credentials rather the default. To set-up alternative credentials see http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

endpoint = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com' if args.sandbox else 'https://mturk-requester.us-east-1.amazonaws.com'
mturk_website = 'requestersandbox.mturk.com' if args.sandbox else 'requester.mturk.com'

with open(args.successfile, 'r') as successfile:
    hitdata = load(successfile, Loader=CLoader)
print('Loaded successfile')

# If you want to use profiles, you have to create a Session with one before connecting a client
session = boto3.Session(profile_name=args.profile)
# Only region w/ MTurk endpoint currently is us-east-1
mtc = session.client('mturk', endpoint_url=endpoint, region_name='us-east-1')

all_results = []
outkeys = ['hitid', 'hittypeid', 'hitgroupid', 'title', 'description', 'keywords', 'reward',
           'creationtime', 'assignments', 'numavailable', 'numpending', 'numcomplete',
           'hitstatus', 'reviewstatus', 'annotation', 'assignmentduration',
           'autoapprovaldelay', 'hitlifetime', 'viewhit', 'assignmentid', 'workerid',
           'assignmentstatus', 'autoapprovaltime', 'assignmentaccepttime',
           'assignmentsubmittime', 'assignmentapprovaltime', 'assignmentrejecttime',
           'deadline', 'feedback', 'reject']
answer_keys = set()


hits = {h['HITId']: mtc.get_hit(HITId=h['HITId']).get('HIT') for h in hitdata}

print('Processing results')
for h in hitdata:
    print(f'Processing HIT: {h["HITId"]}')
    response = mtc.list_assignments_for_hit(HITId=h['HITId'])
    assignments = response.get('Assignments')
    while response.get('NumResults', 0) >= 10:  # I assume 10 is the biggest number they show, but it'd be nice if it decreased
        response = mtc.list_assignments_for_hit(HITId=h['HITId'], NextToken=response.get('NextToken'))
        assignments.extend(response.get('Assignments'))
    for assignment in assignments:
        all_results.append(process_assignment(assignment, hits[h["HITId"]]))

outkeys.extend(list(sorted(answer_keys)))

print(f'Writing {len(all_results)} results')
with open(args.resultsfile, 'wb') as outfile:
    dw = DictWriter(outfile, fieldnames=outkeys, delimiter='\t')
    dw.writeheader()

    for row in all_results:
        dw.writerow(row)

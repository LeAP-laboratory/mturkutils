#!/usr/bin/env python

#Author: Andrew Watts
#
#    Copyright 2012 Andrew Watts and
#        the University of Rochester BCS Department
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License version 2.1 as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.
#    If not, see <http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>.
#

"""
Get information about a HIT, including its completion status.
"""

from __future__ import print_function
import datetime
import calendar
from boto import config
from boto.mturk.connection import MTurkConnection
from csv import DictReader
import argparse
from os.path import expanduser

########################################################################
# A couple of functions borrowed from boto's "mturk" command line app

mturk_website = None

time_units = dict(
    s = 1,
    min = 60,
    h = 60 * 60,
    d = 24 * 60 * 60)

def preview_url(hit):
    return 'https://{}/mturk/preview?groupId={}'.format(
        mturk_website, hit.HITTypeId)

def display_duration(n):
    for unit, m in sorted(time_units.items(), key = lambda x: -x[1]):
        if n % m == 0:
            return '{} {}'.format(n / m, unit)

def parse_timestamp(s):
    '''Takes a timestamp like "2012-11-24T16:34:41Z".

Returns a datetime object in the local time zone.'''
    return datetime.datetime.fromtimestamp(
        calendar.timegm(
        datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').timetuple()))

def display_datetime(dt):
    return dt.strftime('%e %b %Y, %l:%M %P')

# Adapted from boto's "mturk" command line app
def display_hit(hit, verbose = False):
    et = parse_timestamp(hit.Expiration)
    return '\n'.join([
        '{} ({}, {}, {})'.format(
            hit.Title,
            hit.FormattedPrice,
            display_duration(int(hit.AssignmentDurationInSeconds)),
            hit.HITStatus),
        'HIT ID: ' + hit.HITId,
        'Type ID: ' + hit.HITTypeId,
        'Group ID: ' + hit.HITGroupId,
        'Preview: ' + preview_url(hit),
        'Created {}   {}'.format(
            display_datetime(parse_timestamp(hit.CreationTime)),
            'Expired' if et <= datetime.datetime.now() else
                'Expires ' + display_datetime(et)),
        'Assignments: {} -- {} avail, {} pending, {} reviewable, {} reviewed'.format(
            hit.MaxAssignments,
            hit.NumberOfAssignmentsAvailable,
            hit.NumberOfAssignmentsPending,
            int(hit.MaxAssignments) - (int(hit.NumberOfAssignmentsAvailable) + int(hit.NumberOfAssignmentsPending) + int(hit.NumberOfAssignmentsCompleted)),
            hit.NumberOfAssignmentsCompleted)
            if hasattr(hit, 'NumberOfAssignmentsAvailable')
            else 'Assignments: {} total'.format(hit.MaxAssignments),
            # For some reason, SearchHITs includes the
            # NumberOfAssignmentsFoobar fields but GetHIT doesn't.
        ] + ([] if not verbose else [
            '\nDescription: ' + hit.Description,
            '\nKeywords: ' + hit.Keywords
        ])) + '\n'

########################################################################

parser = argparse.ArgumentParser(description='Get information about a HIT from Amazon Mechanical Turk')
parser.add_argument('-successfile', required=True, help='(required) The file to which you\'d like your results saved')
parser.add_argument('-sandbox', type=bool, default=False, help='Run the command in the Mechanical Turk Sandbox (used for testing purposes) NOT IMPLEMENTED')
parser.add_argument('-p', '--profile',
        help='Run commands using specific aws credentials rather the default. To set-up alternative credentials see http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

if args.sandbox:
    if not config.has_section('MTurk'):
        config.add_section('MTurk')
    config.set('MTurk', 'sandbox', 'True')

hitids = None
with open(expanduser(args.successfile), 'r') as successfile:
    hitids = [row['hitid'] for row in DictReader(successfile, delimiter='\t')]

mtc = MTurkConnection(is_secure=True, profile_name=args.profile)

# To get any information about status, you have to get the HIT via get_all_hits
# If you just use get_hit() it gets minimal info
all_hits = mtc.get_all_hits()

currhits = []
for h in all_hits:
    if h.HITId in hitids:
        currhits.append(h)
    # get_all_hits iterates through all your current HITs, grabbing 100 at a time
    # best to break as soon as you get all the HITIds in your group
    if len(currhits) == len(hitids):
        break


for c in currhits:
    print(display_hit(c, verbose=True))
    #print('HITId: {}'.format(c.HITId))
    # print('HITTypeId: {}'.format(c.HITTypeId))
    # print('Title: {}'.format(c.Title))
    # print('Description: {}'.format(c.Description))
    # print('keywords: {}'.format(c.Keywords))
    # print('Reward: {}'.format(c.FormattedPrice))
    # print('Max Assignments: {}'.format(c.MaxAssignments))
    # print('Available: {}'.format(c.NumberOfAssignmentsAvailable))
    # print('Pending: {}'.format(c.NumberOfAssignmentsPending))
    # print('Complete: {}'.format(c.NumberOfAssignmentsCompleted))

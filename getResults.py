#!/usr/bin/env python
#
# Copyright (c) 2014, Andrew Watts and
#        the University of Rochester BCS Department
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import division
from __future__ import print_function

import argparse
from unicodecsv import DictWriter
from math import ceil

from boto.mturk.connection import MTurkConnection
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

__author__ = 'Andrew Watts <awatts2@ur.rochester.edu>'


def manage_url(hit, mturk_website):
    return 'https://{}/mturk/manageHIT?HITId={}'.format(
        mturk_website, hit.HITId)

# Structure of assignments
# each item in answers should be prefixed with 'Answer.' in outfile
# r0.AcceptTime        r0.AssignmentId      r0.HITId             r0.answers
# r0.ApprovalTime      r0.AssignmentStatus  r0.SubmitTime
# r0.Assignment        r0.AutoApprovalTime  r0.WorkerId


def process_assignments(page, allresults, hitinfo):
    """
    Take one page of ResultSets and add them to the results.
    """
    for assignment in page:
        row = {}
        print("Processing AssignmentId: {} for Worker: {}".format(assignment.AssignmentId, assignment.WorkerId))
        try:
            row['assignmentaccepttime'] = assignment.AcceptTime
        except AttributeError:
            row['assignmentaccepttime'] = ''
        try:
            row['assignmentrejecttime'] = assignment.RejectTime
        except AttributeError:
            row['assignmentrejecttime'] = ''
        try:
            row['deadline'] = assignment.Deadline
        except AttributeError:
            row['deadline'] = ''
        try:
            row['feedback'] = assignment.RequesterFeedback
        except AttributeError:
            row['feedback'] = ''
        # I have no idea what 'reject' is, but it came from past MTurk results files
        row['reject'] = ''
        try:
            row['assignmentapprovaltime'] = assignment.ApprovalTime
        except AttributeError:
            row['assignmentapprovaltime'] = ''
        row['assignmentid'] = assignment.AssignmentId
        row['assignmentstatus'] = assignment.AssignmentStatus
        row['autoapprovaltime'] = assignment.AutoApprovalTime
        row['hitid'] = assignment.HITId
        row['assignmentsubmittime'] = assignment.SubmitTime
        row['workerid'] = assignment.WorkerId
        try:
            hit = hitinfo[row['hitid']]
        except KeyError as e:
            print('KeyError: {}'.format(e.args))
            continue
        row['hittypeid'] = hit.HITTypeId
        row['title'] = hit.Title
        row['description'] = hit.Description
        row['keywords'] = hit.Keywords
        row['reward'] = hit.FormattedPrice
        row['creationtime'] = hit.CreationTime
        row['assignments'] = hit.MaxAssignments
        row['numavailable'] = hit.NumberOfAssignmentsAvailable
        row['numpending'] = hit.NumberOfAssignmentsPending
        row['numcomplete'] = hit.NumberOfAssignmentsCompleted
        row['hitstatus'] = hit.HITStatus
        row['reviewstatus'] = hit.HITReviewStatus
        try:
            row['annotation'] = hit.RequesterAnnotation
        except AttributeError:
            row['annotation'] = ''
        row['assignmentduration'] = hit.AssignmentDurationInSeconds
        row['autoapprovaldelay'] = hit.AutoApprovalDelayInSeconds
        row['hitlifetime'] = hit.Expiration
        row['viewhit'] = manage_url(hit, mturk_website)

        for a in assignment.answers:
            for q in a:
                newkey = 'Answer.{}'.format(q.qid)
                answer_keys.add(newkey)
                row[newkey] = ','.join(q.fields)
        allresults.append(row)

parser = argparse.ArgumentParser(description='Get results from Amazon Mechanical Turk')
parser.add_argument('-f', '--successfile', required=True, help='YAML file with HIT information')
parser.add_argument('-r', '--resultsfile', required=True, help='Filename for tab delimited CSV file')
parser.add_argument('-s', '--sandbox', action='store_true',
                    help='Run the command in the Mechanical Turk Sandbox (used for testing purposes)')
parser.add_argument('-p', '--profile',
                    help='Run commands using specific aws credentials rather the default. To set-up alternative credentials see http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

host = 'mechanicalturk.sandbox.amazonaws.com' if args.sandbox else 'mechanicalturk.amazonaws.com'
mturk_website = 'requestersandbox.mturk.com' if args.sandbox else 'requester.mturk.com'

with open(args.successfile, 'r') as successfile:
    hitdata = load(successfile, Loader=Loader)

mtc = MTurkConnection(is_secure=True, host=host, profile_name=args.profile)

all_results = []
outkeys = ['hitid', 'hittypeid', 'title', 'description', 'keywords', 'reward',
           'creationtime', 'assignments', 'numavailable', 'numpending', 'numcomplete',
           'hitstatus', 'reviewstatus', 'annotation', 'assignmentduration',
           'autoapprovaldelay', 'hitlifetime', 'viewhit', 'assignmentid', 'workerid',
           'assignmentstatus', 'autoapprovaltime', 'assignmentaccepttime',
           'assignmentsubmittime', 'assignmentapprovaltime', 'assignmentrejecttime',
           'deadline', 'feedback', 'reject']
answer_keys = set()

hitids = []
assignments = []
for h in hitdata:
    hitid = h['HITId']
    hitids.append(hitid)
    page1 = mtc.get_assignments(hitid)
    total_results = int(page1.TotalNumResults)
    assignments += page1
    if total_results > 10:
        pages = int(ceil(total_results / 10))
        for i in range(1, pages):
            assignments += mtc.get_assignments(hitid, page_number=i+1)

print('{} HITIds: {}'.format(len(hitids), sorted(hitids)))
# print('Assignments: {}'.format(assignments))

# To get any information about status, you have to get the HIT via get_all_hits
# If you just use get_hit() it gets minimal info
# currhits = {}
# for h in mtc.get_all_hits():
#     if h.HITId in hitids:
#         print(h.HITId)
#         currhits[h.HITId] = h
#         print('{}: {}'.format(len(currhits), currhits))
#     # get_all_hits iterates through all your current HITs, grabbing 100 at a time
#     # best to break as soon as you get all the HITIds in your group
#     if len(currhits) == len(hitids):
#         break

currhits = {h.HITId: h for h in mtc.get_all_hits() if h.HITId in hitids}
print('{} Current HITs: {}'.format(len(currhits), sorted(currhits.keys())))


process_assignments(assignments, all_results, currhits)
outkeys.extend(list(sorted(answer_keys)))

# Structure of hits
# foo.Amount                        foo.Expiration                    foo.IntegerValue                  foo.QualificationTypeId
# foo.AssignmentDurationInSeconds   foo.FormattedPrice                foo.Keywords                      foo.RequesterAnnotation
# foo.AutoApprovalDelayInSeconds    foo.HIT                           foo.LocaleValue                   foo.RequiredToPreview
# foo.Comparator                    foo.HITGroupId                    foo.MaxAssignments                foo.Reward
# foo.Country                       foo.HITId                         foo.NumberOfAssignmentsAvailable  foo.Title
# foo.CreationTime                  foo.HITReviewStatus               foo.NumberOfAssignmentsCompleted
# foo.CurrencyCode                  foo.HITStatus                     foo.NumberOfAssignmentsPending    foo.expired
# foo.Description                   foo.HITTypeId                     foo.QualificationRequirement

with open(args.resultsfile, 'w') as outfile:
    dw = DictWriter(outfile, fieldnames=outkeys, delimiter='\t')
    dw.writeheader()

    for row in all_results:
        dw.writerow(row)

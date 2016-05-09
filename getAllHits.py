#!/usr/bin/env python

# Author: Andrew Watts <awatts2@ur.rochester.edu>
#
#    Copyright 2012-2016 Andrew Watts and
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

from __future__ import print_function, division
import argparse
from datetime import datetime
from boto import config
from boto.mturk.connection import MTurkConnection
import pandas as pd

parser = argparse.ArgumentParser(description='Get all current HITs for an account and dump to a CSV file.')
parser.add_argument('-s', '--sandbox', action='store_true',
                    help='Run the command in the Mechanical Turk Sandbox (used for testing purposes)')
parser.add_argument('-p', '--profile',
        help='Run commands using specific aws credentials rather the default. To set-up alternative credentials see http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

if args.sandbox:
    if not config.has_section('MTurk'):
        config.add_section('MTurk')
    config.set('MTurk', 'sandbox', 'True')

mtc = MTurkConnection(is_secure=True, profile_name=args.profile)

all_hits = mtc.get_all_hits()

hit_keys = ('HITTypeId', 'HITGroupId', 'HITId', 'HITStatus', 'HITReviewStatus',
            'Title', 'Description', 'Keywords', 'Amount', 'Reward', 'FormattedPrice',
            'CurrencyCode', 'CreationTime', 'AutoApprovalDelayInSeconds',
            'AssignmentDurationInSeconds', 'Expiration', 'expired', 'NumberOfAssignmentsAvailable',
            'NumberOfAssignmentsCompleted', 'NumberOfAssignmentsPending',
            'MaxAssignments', 'QualificationTypeId', 'QualificationRequirement',
            'RequiredToPreview', 'Comparator', 'IntegerValue', 'Country', 'LocaleValue')

hit_info = [{key: h.__getattribute__(key) for key in hit_keys if hasattr(h, key)} for h in all_hits]
pd.DataFrame(hit_info).to_csv('all_hits-{}.csv'.format(datetime.now().isoformat()), index=False, columns=hit_keys)

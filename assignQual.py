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

from __future__ import print_function
from __future__ import division

__author__ = 'Andrew Watts <awatts@bcs.rochester.edu>'

import argparse
from csv import DictReader
from boto.mturk.connection import MTurkConnection, MTurkRequestError
from boto import config

parser = argparse.ArgumentParser(description='Assign a qualification to Amazon Mechanical Turk workers')
parser.add_argument('-q', '--qualification', required=True, help='Qualification ID')
parser.add_argument('-r', '--resultsfile', required=True, help='Filename of tab delimited CSV file with results')
parser.add_argument('-s', '--sandbox', action='store_true',
                    help='Run the command in the Mechanical Turk Sandbox (used for testing purposes)')
args = parser.parse_args()

if args.sandbox:
    if not config.has_section('MTurk'):
        config.add_section('MTurk')
    config.set('MTurk', 'sandbox', 'True')
    mturk_website = 'requestersandbox.mturk.com'

with open(args.resultsfile, 'r') as infile:
    results = list(DictReader(infile, delimiter='\t'))

mtc = MTurkConnection(is_secure=True)

for row in results:
    try:
        mtc.assign_qualification(args.qualification, row['workerid'], value=1, send_notification=False)
        print("Assigning {} to {}".format(args.qualification, row['workerid']))
    except MTurkRequestError as e:
        print("Skipping {} for {}".format(args.qualification, row['workerid']))

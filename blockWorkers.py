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

from __future__ import print_function
from boto.mturk.connection import MTurkConnection
from csv import DictReader
import argparse
from os.path import expanduser

parser = argparse.ArgumentParser(description='Block a worker from doing your HITs on Amazon Mechanical Turk')
parser.add_argument('-blockfile', required=True, help="(required) File with comma separated 'worker' and 'reason' columns")
parser.add_argument('-p', '--profile',
        help='Run commands using specific aws credentials rather the default. To set-up alternative credentials see http://boto3.readthedocs.org/en/latest/guide/configuration.html#shared-credentials-file')
args = parser.parse_args()

mtc = MTurkConnection(is_secure=True, profile_name=args.profile)

with open(args.blockfile, 'r') as blockfile:
    toblock = DictReader(blockfile)
    for row in toblock:
        print("Blocking '{}' for '{}'".format(row['workerid'], row['reason']))
        mtc.block_worker(row['workerid'], row['reason'])

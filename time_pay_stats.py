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
Calculate the min, max, mean, and median time workers took to do a particular
HIT and what the corresponding hourly rates are
"""

from __future__ import print_function, division
from csv import DictReader
import argparse
from dateutil.parser import parse
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import bayes_mvs

HOUR = 3600

def filter_outliers(arr):
    """
    Given an array, return the array minus outliers, where outliers are those
    values greater than two standard deviations from the mean
    """
    nparr = arr if isinstance(arr, np.ndarray) else np.array(arr)
    twosigup = nparr.mean() + nparr.std() *2
    twosigdown = nparr.mean() - nparr.std() *2

    return [x for x in nparr if (x < twosigup) and (x > twosigdown)]

def submit_time_histogram(arr):
    """
    Use Matplotlib to plot a normalized histogram of submit times
    """
    from math import ceil, log
    try:
        import matplotlib.mlab as mlab
        from prettyplotlib import plt
    except ImportError:
        print('You must have Matplotlib and Prettyplotlib installed to plot a histogram.')

    # Use Sturges' formula for number of bins: k = ceiling(log2 n + 1)
    k = ceil(log(len(arr), 2) + 1)
    n, bins, patches = plt.hist(arr, k, normed=1, facecolor='green', alpha=0.75)
    # throw a PDF plot on top of it
    #y = mlab.normpdf(bins, np.mean(arr), np.std(arr))
    #l = plt.plot(bins, y, 'r--', linewidth=1)

    # Get a Bayesian confidence interval for mean, variance, standard deviation
    dmean, dvar, dsd = bayes_mvs(deltas)

    # drop a line in at the mean for fun
    plt.axvline(dmean[0], color='blue', alpha=0.5)
    plt.axvspan(dmean[1][0], dmean[1][1], color='blue', alpha=0.5)
    plt.axvline(np.median(deltas), color='y', alpha=0.5)

    # Caclulate a Kernel Density Estimate
    density = gaussian_kde(deltas)
    xs = np.arange(0., np.max(deltas), 0.1) 
    density.covariance_factor = lambda : .25
    density._compute_covariance()
    plt.plot(xs,density(xs), color='m')

    #FIXME: come up with better legend names
    #plt.legend(('Normal Curve', 'Mean', 'Median', 'KDE'))
    plt.legend(('Mean', 'Median', 'KDE'))

    plt.xlabel('Submit Times (in Seconds)')
    plt.ylabel('Probability')
    plt.title('Histogram of Worker submit times')
    plt.grid(True)

    plt.show()

parser = argparse.ArgumentParser(description='Calculate the min, max, mean, and'
                                              'median time workers took to do a'
                                              'particular HIT and what the'
                                              'corresponding hourly rates are')
parser.add_argument('-r', '--resultsfiles', nargs='*', required=True, help='(required) Results file to use')
parser.add_argument('-p', '--pay', type=float, required=True, help='Pay per HIT')
parser.add_argument('-o', '--removeoutliers', required=False, action="store_true",
                    default=False, help='Remove outlier values?')
parser.add_argument('-j', '--removerejected', required=False, action="store_true",
                    default=False, help='Remove rejected workers?')
parser.add_argument('-t', '--plot', required=False, action="store_true",
                    default=False, help='Plot a histogram of submit times')
args = parser.parse_args()

results = []
for r in args.resultsfiles:
    with open(r, 'r') as resfile:
        results = list(DictReader(resfile, delimiter='\t'))

if args.removerejected:
    print("Workers before filtering rejected: {}".format(len(results)))
    results = [x for x in results if x['assignmentstatus'] != 'Rejected']
    print("Workers after filtering rejected: {}".format(len(results)))

deltas = []
for row in results:
    delta = parse(row['assignmentsubmittime']) - parse(row['assignmentaccepttime'])
    deltas.append(delta.total_seconds())

if args.removeoutliers:
    print("Workers before filtering outliers: {}".format(len(deltas)))
    deltas = filter_outliers(deltas)
    print("Workers after filtering outliers: {}".format(len(deltas)))

minsubmit = np.min(deltas)
print("\nFastest time: {:.2f} seconds ({:.2f} minutes)".format(minsubmit, minsubmit / 60))
maxsubmit = np.max(deltas)
print("Slowest time: {:.2f} seconds ({:.2f} minutes)".format(maxsubmit, maxsubmit / 60))
medsubmit = np.median(deltas)
print("Median time: {:.2f} seconds ({:.2f} minutes)".format(medsubmit, medsubmit / 60))
meansubmit = np.mean(deltas)
print("Mean time: {:.2f} seconds ({:.2f} minutes)".format(meansubmit, meansubmit / 60))
stdsubmit = np.std(deltas)
print("Standard deviation: {:.2f} seconds ({:.2f} minutes)".format(stdsubmit, stdsubmit / 60))
twostd = stdsubmit * 2
lowsub = meansubmit - twostd
highsub = meansubmit + twostd
print("98% of workers should be between {:.2f} seconds ({:.2f} minutes) and {:.2f} seconds ({:.2f} minutes)".format(lowsub, lowsub / 60, highsub, highsub / 60))

minpay = (HOUR / maxsubmit) * args.pay
print("\nMinimum hourly pay: ${:.2f}".format(minpay))
meanpay = (HOUR / meansubmit) * args.pay
print("Mean hourly pay: ${:.2f}".format(meanpay))
medpay = (HOUR / medsubmit) * args.pay
print("Median hourly pay: ${:.2f}".format(medpay))
maxpay = (HOUR / minsubmit) * args.pay
print("Maximum hourly pay: ${:.2f}".format(maxpay))

if args.plot:
    submit_time_histogram(deltas)

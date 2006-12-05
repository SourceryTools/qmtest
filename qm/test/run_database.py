########################################################################
#
# File:   run_database.py
# Author: Mark Mitchell
# Date:   2005-08-08
#
# Contents:
#   QMTest RunDatabase class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.extension import Extension
from qm.test.result import Result
from qm.common import parse_time_iso

########################################################################
# Classes
########################################################################

class RunDatabase(Extension):
    """A 'RunDatabase' stores 'TestRun's.

    A 'RunDatabase' provides a mechanism for selecting 'TestRun's that
    meet particular criteria."""

    def GetAllRuns(self):
        """Return all the 'TestRun's in the database.

        returns -- A sequence consisting of all of the 'TestRun's in
        the database."""

        raise NotImplementedError
    
        
    def GetRuns(self, predicate):
        """Return the set of 'TestRun's satisfying 'predicate'

        'predicate' -- A callable that can be passed one 'TestRun'
        argument.

        returns -- A sequence of 'TestRun's consisting only of those
        'TestRun's in the database for which 'predicate' returns a
        true value."""

        return filter(self.GetAllRuns(), predicate)


    def GetAnnotations(self, key):
        """Return the set of annotations for 'key' from all test runs.

        'key' -- A string used to look up the annotations.

        returns -- A set of (distinct) annotations for 'key' from all
        test runs."""

        # We can't use sets since we want to remain python 2.2 compatible.
        annotations = []
        for r in self.GetAllRuns():
            value = r.GetAnnotation(key)
            if value not in annotations:
                annotations.append(value)
        return annotations


    def GetTimeframe(self, time_key, is_iso_time = True):
        """Return a pair of min / max values found for the given time_key
        across all test runs.

        'time_key' -- Annotation key referring to a string convertible to
        either iso-formatted time or floating point number.

        returns -- minimum, maximum."""

        minimum = None
        maximum = None
        for r in self.GetAllRuns():
            time_string = r.GetAnnotation(time_key)
            if not time_string:
                continue
            if is_iso_time:
                time = parse_time_iso(time_string)
            else:
                time = float(time_string)
            if not minimum or minimum > time:
                minimum = time
            if not maximum or maximum < time:
                # Make sure the largest value is still inside the interval.
                maximum = time + 0.1
        return minimum, maximum


    def GetRunInTimeframe(self, key, value, time_key, minimum, maximum, is_iso_time = True):
        """Return a test run id matching the key and timeframe."""

        for i in range(len(self.GetAllRuns())):
            r = self.GetAllRuns()[i]
            if r.GetAnnotation(key) != value:
                continue
            time_string = r.GetAnnotation(time_key)
            if not time_string:
                continue
            if is_iso_time:
                time = parse_time_iso(time_string)
            else:
                time = float(time_string)
            if time >= minimum and time < maximum:
                return i
        # No match.
        return None
    

    def GetRunsByAnnotations(self, annotation_filter):
        """Return the 'TestRun's matching 'annotation_filter'.

        'annotation_filter' -- A dictionary mapping annotation keys
        (strings) to values (either strings or callables).

        returns -- A sequence of 'TestRun's consisting only of those
        'TestRun's in the database that match the
        'annotation_filter'.  A 'TestRun' matches the
        'annotation_filter' if it matches each of the key-value pairs
        in the filter.  If the value in such a pair is a string, then
        the annotation in the 'TestRun' must exactly match the value.  
        If the value is a callable, rather than a string, then when
        passed the value from the 'TestRun', the predicate must return
        a true value."""
        
        def predicate(run):
            for key, pattern in annotation_filter.iteritems():
                value = run.GetAnnotation(key)
                if callable(pattern):
                    if not pattern(value):
                        return False
                elif value != pattern:
                    return False
            return True

        return self.GetRuns(predicate)


    def GetOutcomes(self, id, kind = Result.TEST):
        """Return an outcome dictionary for the indicated test.

        'id' -- The name of a test, suite, or resource item.

        'kind' -- The kind of the item to retrieve the outcome for.

        returns -- A dictionary indicating the number of outcomes per category."""
        
        outcomes = {Result.PASS: 0,
                    Result.FAIL: 0,
                    Result.ERROR: 0,
                    Result.UNTESTED: 0}
        for r in self.GetAllRuns():
            result = r.GetResult(id, kind)
            if result:
                outcomes[result.GetOutcome()] += 1
            else:
                outcomes[Result.UNTESTED] += 1
        return outcomes

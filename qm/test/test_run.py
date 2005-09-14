########################################################################
#
# File:   test_run.py
# Author: Mark Mitchell
# Date:   2005-08-08
#
# Contents:
#   QMTest TestRun class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.test.result import Result

########################################################################
# Classes
########################################################################

class TestRun(object):
    """A 'TestRun' stores the 'Result's from a single test run.

    The primary contents of a 'TestRun' are the the 'Result's of the
    run.  In addition, each 'TestRun' has an associated set of
    annotations, which are used to store global information about the
    'TestRun'."""

    def GetResult(self, id, kind = Result.TEST):
        """Return the 'Result' for the indicated test.

        'id' -- The name of a test or resource.
        
        'kind' -- The kind of result to retrieve.  See 'Result' for a
        list of the available result kinds.
        
        returns -- The 'Result' corresponding to 'test_id'.

        raises -- 'KeyError' if there is no result of the given 'kind'
        for 'id' in the test run."""

        raise NotImplementedError
    

    def GetAnnotation(self, key):
        """Return the annotation associated with 'key'.

        'key' -- A string giving the name of an annotation.

        returns -- A string giving the value of the annotation, or
        'None' if there is no such annotation."""

        raise NotImplementedError


    def GetAllResults(self, directory = "", kind = Result.TEST):
        """Return 'Result's from the given directory..

        'directory' -- A path to a directory in the test database.

        'kind' -- The kind of results to return.
        
        returns -- All the results within 'directory' (including its
        subdirectories)."""

        raise NotImplementedError
    

    def GetResultsByOutcome(self, outcome = None, directory = "",
                            kind = Result.TEST):
        """Return 'Result's with a particular outcome.

        'outcome' -- One of the 'Result.outcomes', or 'None'.

        'directory' -- A path to a directory in the test database.

        'kind' -- The kind of results to return.
        
        returns -- All the results within 'directory' (including its
        subdirectories) that have the indicated 'outcome', or, if
        'outcome' is 'None', all test results from 'directory'."""

        results = []
        for result in self.GetAllResults(directory, kind):
            # Check the outcome.
            if outcome and result.GetOutcome() != outcome:
                continue
            results.append(result)
        return results
        

    def CountOutcomes(self, directory = "", outcome = None):
        """Return statistics about the outcomes of tests.

        'directory' -- A path to a directory in the test database.

        'outcome' -- If not 'None', one of the 'Result.outcomes'.

        returns -- A dictionary mapping outcomes to the number of test
        results with that outcome located within 'directory' and its
        subdirectories.  If 'outcome' is not 'None', the dictionary
        will have an entry only for the 'outcome' specified."""

        if not outcome:
            outcomes = Result.outcomes
        else:
            outcomes = (outcome,)
        counts = {}
        for o in outcomes:
            counts[o] = len(self.GetResultsByOutcome(o, directory))
        return counts

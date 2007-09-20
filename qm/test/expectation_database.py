########################################################################
#
# File:   expectation_database.py
# Author: Stefan Seefeld
# Date:   2006-11-05
#
# Contents:
#   QMTest ExpectationDatabase class.
#
# Copyright (c) 2006 by CodeSourcery, Inc.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.extension import Extension
from qm.fields import PythonField
from qm.test.result import Result

########################################################################
# Classes
########################################################################

class ExpectationDatabase(Extension):
    """An 'ExpectationDatabase' stores result expectations.

    An 'ExpectationDatabase' provides a mechanism to store and make
    accessible expectations for test outcomes.
    By default, all tests are expected to pass.
    """


    kind = 'expectation_database'


    test_database = PythonField()
    testrun_parameters = PythonField()


    def Lookup(self, test_id):
        """Look up the expected outcome for the given test.

        'test_id' -- test-id for which the outcome is queried.

        returns -- a Result object associated with this test_id."""

        return Result(Result.TEST, test_id)


    def GetExpectedOutcomes(self):
        """Return a dict object mapping test ids to expected outcomes."""

        outcomes = {}
        if self.test_database:
            for test_id in self.test_database.GetTestIds():
                outcomes[test_id] = self.Lookup(test_id).GetOutcome()
        return outcomes

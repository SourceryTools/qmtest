########################################################################
#
# File:   run.py
# Author: Alex Samuel
# Date:   2001-09-08
#
# Contents:
#   Web interface for running tests and displaying results.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

"""Web forms for test runs and test results."""

# FIXME: Security: How do we control who can run tests?

########################################################################
# imports
########################################################################

import qm.test.base
from   qm.test.result import *
import qm.test.run
import qm.web
import string
import web

########################################################################
# classes
########################################################################

class TestResultsPage(web.DtmlPage):
    """DTML page for displaying test results."""

    def __init__(self, test_results, expected_outcomes):
        """Construct a new 'TestResultsPage'.

        'test_results' -- A map from test IDs to 'Result' objects.

        'expected_outcomes' -- A map from test IDs to outcomes."""
        
        # Initialize the base classes.
        web.DtmlPage.__init__(self, "results.dtml")

        self.test_results = test_results
        self.expected_outcomes = expected_outcomes
        

    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        ResultStream.Summarize(self)

      
    def FormatResult(self, result):
         """Return HTML for displaying a test result.

         'result' -- A 'Result'.

         returns -- HTML displaying the result."""

         text = result.AsStructuredText("full")
         return qm.structured_text.to_html(text)

         
    def GetClassForResult(self, result):
        """Return the CSS class for displaying a 'result'.

        returns -- The name of a CSS class.  These are used with <span>
        elements.  See 'qm.css'."""

        outcome = result.GetOutcome()
        return {
            Result.PASS: "pass",
            Result.FAIL: "fail",
            Result.UNTESTED: "untested",
            Result.ERROR: "error",
            }[outcome]


    def GetOutcomes(self):
        """Return the list of result outcomes.

        returns -- A sequence of result outcomes."""

        return Result.outcomes


    def GetTotal(self):
        """Return the total number of tests.

        returns -- The total number of tests."""

        return len(self.test_results)


    def GetTotalUnexpected(self):
        """Return the total number of unexpected results.

        returns -- The total number of unexpected results."""

        return len(self.GetRelativeResults(self.test_results.values(),
                                           0))


    def GetResultsWithOutcome(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The results with the given 'outcome'."""

        return filter(lambda r, o=outcome: r.GetOutcome() == o,
                          self.test_results.values())
    
        
    def GetCount(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The number of tests with the given 'outcome'."""

        return len(self.GetResultsWithOutcome(outcome))


    def GetUnexpectedCount(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The number of tests with the given 'outcome' that
        were expected to have some other outcome."""

        results = self.GetResultsWithOutcome(outcome)
        results = self.GetRelativeResults(results, 0)
        return len(results)

    
    def GetTestIds(self, expected):
        """Return a sequence of test IDs whose results are to be shown.

        returns -- The test ids for tests whose outcome is as expected,
        if 'expected' is true, or unexpected, if 'expected' is false."""

        results = self.GetRelativeResults(self.test_results.values(),
                                          expected)
        return map(lambda r: r.GetId(), results)


    def GetRelativeResults(self, results, expected):
        """Return the results that match, or fail to match, expectations.

        'results' -- A sequence of 'Result' objects.

        'expected' -- A boolean.  If true, expected results are
        returned.  If false, unexpected results are returned."""

        if expected:
            return filter(lambda r, er=self.expected_outcomes: \
                              r.GetOutcome() == er.get(r.GetId(),
                                                        Result.PASS),
                          results)
        else:
            return filter(lambda r, er=self.expected_outcomes: \
                              r.GetOutcome() != er.get(r.GetId(),
                                                        Result.PASS),
                          results)


    def GetDetailUrl(self, test_id):
        """Return the detail URL for a test.

        'test_id' -- The name of the test.

        returns -- The URL that contains details about the 'test_id'."""

        return qm.web.WebRequest("show-result",
                                 base = self.request,
                                 id=test_id).AsUrl()
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

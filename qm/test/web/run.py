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
from   qm.test.result_stream import *
import qm.test.run
import qm.web
import string
import web

########################################################################
# classes
########################################################################

class TestResultsPage(web.DtmlPage, ResultStream):
    """DTML page for displaying test results."""

    def __init__(self):
        """Construct a new 'TestResultsPage'."""
        
        # Initialize the base classes.
        web.DtmlPage.__init__(self, "results.dtml")
        ResultStream.__init__(self)

        self.test_results = {}
        

    def WriteResult(self, result):
        """Output a test result.

        'result' -- A 'Result'."""

        # Record the results as they are received.  Resource results
        # are ignored.
        if result.GetKind() == Result.TEST:
            self.test_results[result.GetId()] = result

        
    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        pass

      
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


    def GetTestIds(self):
        """Return a sequence of test IDs whose results are to be shown.

        The IDs are in the order in which their results should be
        shown."""

        test_ids = self.test_results.keys()
        test_ids.sort()
        return test_ids



########################################################################
# functions
########################################################################

def handle_run_tests(request):
    """Respond to a request to run tests.

    Runs the tests specified in the request, and returns a page
    displaying the results of the run.

    These fields in 'request' are used:

      'ids' -- A comma-separated list of test and suite IDs.  These IDs
      are expanded into the list of IDs of tests to run.

    """

    # Extract and expand the IDs of tests to run.
    ids = string.split(request["ids"], ",")
    test_ids, suite_ids = qm.test.base.expand_ids(ids)
    
    # FIXME: Put other things in the context?
    context = qm.test.base.Context()
    # FIXME: Determine target group.
    target_specs = [
        qm.test.run.TargetSpec("local",
                               "qm.test.run.SubprocessTarget",
                               "",
                               1,
                               {}),
        ]

    results_page = TestResultsPage()
    
    # Run the tests.
    qm.test.run.test_run(test_ids, context, target_specs, [results_page])

    # Display the results.
    return results_page(request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   test_result_stream.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest TextResultStream class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import formatter
import htmllib
import StringIO
from   qm.test.base import *
from   qm.test.result import *
from   qm.test.result_stream import *

########################################################################
# classes
########################################################################

class TextResultStream(ResultStream):
    """A 'TextResultStream' displays test results textually.

    A 'TextResultStream' displays information textually, in human
    readable form.  This 'ResultStream' is used when QMTest is run
    without a graphical user interface."""

    def __init__(self, file, format, expected_outcomes, database,
                 suite_ids):
        """Construct a 'TextResultStream'.

        'file' -- The file object to which the results should be
        written.

        'format' -- A string indicating the format to use when
        displaying results.

        'expected_outcomes' -- A map from test IDs to expected outcomes,
        or 'None' if there are no expected outcomes.

        'database' -- The 'Database' out of which the tests will be
        run.
        
        'suite_ids' -- The suites that will be executed during the
        test run."""

        # Initialize the base class.
        ResultStream.__init__(self)
        
        self.__file = file
        self.__format = format
        self.__expected_outcomes = expected_outcomes
        self.__suite_ids = suite_ids
        self.__database = database
        self.__test_results = []
        self.__resource_results = []
        self._DisplayHeading("TEST RESULTS")
        
        
    def WriteResult(self, result):
        """Output a test or resource result.

        'result' -- A 'Result'."""

        # Record the results as they are received.
        if result.GetKind() == Result.TEST:
            self.__test_results.append(result)
        else:
            self.__resource_results.append(result)

	# Display the result.
	self._DisplayResult(result, "brief")

        # Display annotations associated with the test.
        if (self.__format == "full"
            or (self.__format == "brief"
                and result.GetOutcome() != Result.PASS)):
            self._DisplayAnnotations(result)


    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""
        
        self.__file.write("\n")
        self._DisplayHeading("STATISTICS")

        # Summarize the test statistics.
        if self.__expected_outcomes:
            self._SummarizeRelativeTestStats(self.__test_results)
        else:
            self._SummarizeTestStats(self.__test_results)

        # Summarize test results by test suite.
        if self.__format in ("full", "stats") \
           and len(self.__suite_ids) > 0:
            # Print statistics by test suite.
            self._DisplayHeading("STATISTICS BY TEST SUITE")
            self._SummarizeTestSuiteStats()

        if self.__format in ("full", "brief"):
            compare_ids = lambda r1, r2: cmp(r1.GetId(), r2.GetId())

            # Sort test results by ID.
            self.__test_results.sort(compare_ids)
            # Print individual test results.
            if self.__expected_outcomes:
                # Show tests that produced unexpected outcomes.
                bad_results = split_results_by_expected_outcome(
                    self.__test_results, self.__expected_outcomes)[1]
                self._DisplayHeading("TESTS WITH UNEXPECTED OUTCOMES")
                self._SummarizeResults(bad_results)
            if not self.__expected_outcomes or self.__format == "full":
                # No expected outcomes were specified, so show all tests
                # that did not pass.
                bad_results = filter(
                    lambda r: r.GetOutcome() != Result.PASS,
                    self.__test_results)
                if bad_results:
                    self._DisplayHeading("TESTS THAT DID NOT PASS")
                    self._SummarizeResults(bad_results)

            # Sort resource results by ID.
            self.__resource_results.sort(compare_ids)
            bad_results = filter(
                lambda r: r.GetOutcome() != Result.PASS,
                self.__resource_results)
            if len(bad_results) > 0:
                # Print individual resource results.
                self._DisplayHeading("RESOURCES THAT DID NOT PASS")
                self._SummarizeResults(bad_results)

        # Invoke the base class method.
        ResultStream.Summarize(self)


    def _SummarizeTestStats(self, results):
        """Generate statistics about the overall results.

        'results' -- The sequence of 'Result' objects to summarize."""

        num_tests = len(results)
        self.__file.write("  %6d        tests total\n" % num_tests)

        # If there are no tests, there is no need to go into detail.
        if num_tests == 0:
            return

        counts_by_outcome = self._CountOutcomes(results)
        for outcome in Result.outcomes:
            count = counts_by_outcome[outcome]
            if count > 0:
                self.__file.write("  %6d (%3.0f%%) tests %s\n"
                                  % (count, (100. * count) / num_tests,
                                     outcome))
        self.__file.write("\n")

        
    def _SummarizeRelativeTestStats(self, results):
        """Generate statistics showing results relative to expectations.

        'results' -- The sequence of 'Result' objects to summarize."""

        # Indicate the total number of tests.
        num_tests = len(results)
        self.__file.write("  %6d        tests total\n" % num_tests)

        # If there are no tests, there is no need to go into detail.
        if num_tests == 0:
            return

        # Split the results into those that produced expected outcomes, and
        # those that didn't.
        expected, unexpected = \
            split_results_by_expected_outcome(results,
                                              self.__expected_outcomes)
        # Report the number that produced expected outcomes.
        self.__file.write("  %6d (%3.0f%%) tests as expected\n"
                          % (len(expected),
                             (100. * len(expected)) / num_tests))
        # For results that produced unexpected outcomes, break them down by
        # actual outcome.
        counts_by_outcome = self._CountOutcomes(unexpected)
        for outcome in Result.outcomes:
            count = counts_by_outcome[outcome]
            if count > 0:
                self.__file.write("  %6d (%3.0f%%) tests unexpected %s\n"
                                  % (count, (100. * count) / num_tests,
                                     outcome))
        self.__file.write("\n")


    def _CountOutcomes(self, results):
        """Count results by outcome.

        'results' -- A sequence of 'Result' objects.

        returns -- A map from outcomes to counts of results with that
        outcome.""" 

        counts = {}
        for outcome in Result.outcomes:
            counts[outcome] = 0
        for result in results:
            outcome = result.GetOutcome()
            counts[outcome] = counts[outcome] + 1
        return counts
        
        
    def _SummarizeTestSuiteStats(self):
        """Generate statistics showing results by test suite."""

        database = self.__database

        for suite_id in self.__suite_ids:
            # Expand the contents of the suite.
            suite = database.GetSuite(suite_id)
            ids_in_suite = suite.GetAllTestAndSuiteIds()[0]
            # Determine the results belonging to tests in the suite.
            results_in_suite = []
            for result in self.__test_results:
                if result.GetId() in ids_in_suite:
                    results_in_suite.append(result)
            # If there aren't any, skip.
            if len(results_in_suite) == 0:
                continue

            self.__file.write("  %s\n" % suite.GetId())
            if self.__expected_outcomes is None:
                self._SummarizeTestStats(results_in_suite)
            else:
                self._SummarizeRelativeTestStats(results_in_suite)

        
    def _SummarizeResults(self, results):
        """Summarize each of the results.

        'results' -- The sequence of 'Result' objects to summarize."""

        if len(results) == 0:
            self.__file.write("  None.\n\n")
            return

        # Generate them.
	for result in results:
            self._DisplayResult(result, self.__format)


    def _DisplayResult(self, result, format):
	"""Display 'result'.

	'result' -- The 'Result' of a test or resource execution.

        'format' -- The format to use when displaying results."""

	id_ = result.GetId()
        kind = result.GetKind()
	outcome = result.GetOutcome()

	# Print the ID and outcome.
	if self.__expected_outcomes:
	    # If expected outcomes were specified, print the expected
	    # outcome too.
	    expected_outcome = \
	        self.__expected_outcomes.get(id_, Result.PASS)
            if (outcome == Result.PASS
                and expected_outcome == Result.FAIL):
                self._WriteOutcome(id_, kind, "XPASS")
            elif (outcome == Result.FAIL
                  and expected_outcome == Result.FAIL):
                self._WriteOutcome(id_, kind, "XFAIL")
            elif outcome != expected_outcome:
                self._WriteOutcome(id_, kind, outcome, expected_outcome)
            else:
                self._WriteOutcome(id_, kind, outcome)
	else:
            self._WriteOutcome(id_, kind, outcome)

        # Print the cause of the failure.
        if result.has_key(Result.CAUSE):
            self.__file.write('    ' + result[Result.CAUSE] + '\n')
            
        self.__file.write('\n')


    def _DisplayAnnotations(self, result):
        """Display the annotations associated with 'result'.

        'result' -- The 'Result' to dispay."""

        keys = result.keys()
        keys.sort()
        for name in keys:
            # The CAUSE property has already been displayed."
            if name == Result.CAUSE:
                continue
            # Add an item to the list
            self.__file.write("    %s:\n" % name)

            # Convert the HTML to text.
            s = StringIO.StringIO()
            w = formatter.DumbWriter(s)
            f = formatter.AbstractFormatter(w)
            p = htmllib.HTMLParser(f)
            p.feed(result[name])
            p.close()

            # Write out the text.
            for l in s.getvalue().splitlines():
                self.__file.write("      " + l + "\n")
            self.__file.write("\n")
        

    def _WriteOutcome(self, name, kind, outcome, expected_outcome=None):
        """Write a line indicating the outcome of a test or resource.

        'name' -- The name of the test or resource.

        'kind' -- The kind of result being displayed.
        
        'outcome' -- A string giving the outcome.

        'expected_outcome' -- If not 'None', the expected outcome."""

        if kind == Result.RESOURCE_SETUP:
            name = "Setup " + name
        elif kind == Result.RESOURCE_CLEANUP:
            name = "Cleanup " + name
        
        if expected_outcome:
	    self.__file.write("  %-46s: %-8s, expected %-8s\n"
			      % (name, outcome, expected_outcome))
	else:
	    self.__file.write("  %-46s: %-8s\n" % (name, outcome))

            
    def _DisplayHeading(self, heading):
        """Display 'heading'.

        'heading' -- The string to use as a heading for the next
        section of the report."""

        self.__file.write("--- %s %s\n\n" %
                          (heading, "-" * (73 - len(heading))))

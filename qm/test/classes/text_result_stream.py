########################################################################
#
# File:   test_result_stream.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest TextResultStream class.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
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
from   qm.test.file_result_stream import FileResultStream

########################################################################
# classes
########################################################################

class TextResultStream(FileResultStream):
    """A 'TextResultStream' displays test results textually.

    A 'TextResultStream' displays information textually, in human
    readable form.  This 'ResultStream' is used when QMTest is run
    without a graphical user interface."""

    arguments = [
        qm.fields.EnumerationField(
            name = "format",
            title = "Format",
            description = """The output format used by this result stream.

            There are three sections to the output:

            (S) Summary statistics.

            (I) Individual test-by-test results.

            (U) Individual test-by-test results for tests with unexpected
                outcomes.

            For each of the sections of individual test-by-test results, the
            results can be shown either in one of three modes:

            (A) Show all annotations.

            (N) Show no annotations.

            (U) Show annotations only if the test has an unexpected outcome.

            In the "brief" format, results for all tests are shown as
            they execute, with unexpected results displayed in full
            detail, followed by a list of all the tests with
            unexpected results in full detail, followed by the summary
            information.  This format is useful for interactive use:
            the user can see that the tests are running as they go,
            can attempt to fix failures while letting the remainder of
            the tests run, and can easily see the summary of the
            results later if the window in which the run is occurring
            is left unattended.

            In the "batch" format, statistics are displayed first
            followed by full results for tests with unexpected
            outcomes.  The batch format is useful when QMTest is run
            in batch mode, such as from an overnight job.  The first
            few lines of the results (often presented by email) give
            an overview of the results; the remainder of the file
            gives details about any tests with unexpected outcomes.

            The "full" format is like "brief" except that all
            annotations are shown for tests as they are run.

            The "stats" format omits the failing tests section."""),
        ]
    
    def __init__(self, arguments):
        """Construct a 'TextResultStream'.

        'arguments' -- The arguments to this result stream.

        'suite_ids' -- The suites that will be executed during the
        test run."""

        # Initialize the base class.
        super(TextResultStream, self).__init__(arguments)

        # Pick a default format.
        if not self.format:
            self.format = "batch"
            try:
                if self.file.isatty():
                    self.format = "brief"
            except:
                pass
            
        self.__test_results = []
        self.__resource_results = []
        self.__first_test = 1
        
        
    def WriteResult(self, result):
        """Output a test or resource result.

        'result' -- A 'Result'."""

        # Record the results as they are received.
        if result.GetKind() == Result.TEST:
            self.__test_results.append(result)
        else:
            self.__resource_results.append(result)

        # In batch mode, no results are displayed as tests are run.
        if self.format == "batch":
            return
        
        # Display a heading before the first result.
        if self.__first_test:
            self._DisplayHeading("TEST RESULTS")
            self.__first_test = 0
        
	# Display the result.
	self._DisplayResult(result, self.format)

        # Display annotations associated with the test.
        if (self.format == "full"
            or (self.format == "brief"
                and result.GetOutcome() != Result.PASS)):
            self._DisplayAnnotations(result)


    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        if self.format == "batch":
            self._DisplayStatistics()

        # Show results for tests with unexpected outcomes.
        if self.format in ("full", "brief", "batch"):
            compare_ids = lambda r1, r2: cmp(r1.GetId(), r2.GetId())

            # Sort test results by ID.
            self.__test_results.sort(compare_ids)
            # Print individual test results.
            if self.expected_outcomes:
                # Show tests that produced unexpected outcomes.
                bad_results = split_results_by_expected_outcome(
                    self.__test_results, self.expected_outcomes)[1]
                self._DisplayHeading("TESTS WITH UNEXPECTED OUTCOMES")
                self._SummarizeResults(bad_results)
            if not self.expected_outcomes or self.format == "full":
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

        if self.format != "batch":
            self._DisplayStatistics()
        
        # Invoke the base class method.
        super(TextResultStream, self).Summarize()


    def _DisplayStatistics(self):
        """Write out statistical information about the results.

        Write out statistical information about the results."""

        self.file.write("\n")
        self._DisplayHeading("STATISTICS")

        # Summarize the test statistics.
        if self.expected_outcomes:
            self._SummarizeRelativeTestStats(self.__test_results)
        else:
            self._SummarizeTestStats(self.__test_results)

        # Summarize test results by test suite.
        if self.format in ("full", "stats") \
           and len(self.suite_ids) > 0:
            # Print statistics by test suite.
            self._DisplayHeading("STATISTICS BY TEST SUITE")
            self._SummarizeTestSuiteStats()

        
    def _SummarizeTestStats(self, results):
        """Generate statistics about the overall results.

        'results' -- The sequence of 'Result' objects to summarize."""

        num_tests = len(results)
        self.file.write("  %6d        tests total\n" % num_tests)

        # If there are no tests, there is no need to go into detail.
        if num_tests == 0:
            return

        counts_by_outcome = self._CountOutcomes(results)
        for outcome in Result.outcomes:
            count = counts_by_outcome[outcome]
            if count > 0:
                self.file.write("  %6d (%3.0f%%) tests %s\n"
                                % (count, (100. * count) / num_tests,
                                   outcome))
        self.file.write("\n")

        
    def _SummarizeRelativeTestStats(self, results):
        """Generate statistics showing results relative to expectations.

        'results' -- The sequence of 'Result' objects to summarize."""

        # Indicate the total number of tests.
        num_tests = len(results)
        self.file.write("  %6d        tests total\n" % num_tests)

        # If there are no tests, there is no need to go into detail.
        if num_tests == 0:
            return

        # Split the results into those that produced expected outcomes, and
        # those that didn't.
        expected, unexpected = \
            split_results_by_expected_outcome(results,
                                              self.expected_outcomes)
        # Report the number that produced expected outcomes.
        self.file.write("  %6d (%3.0f%%) tests as expected\n"
                        % (len(expected),
                           (100. * len(expected)) / num_tests))
        # For results that produced unexpected outcomes, break them down by
        # actual outcome.
        counts_by_outcome = self._CountOutcomes(unexpected)
        for outcome in Result.outcomes:
            count = counts_by_outcome[outcome]
            if count > 0:
                self.file.write("  %6d (%3.0f%%) tests unexpected %s\n"
                                % (count, (100. * count) / num_tests,
                                   outcome))
        self.file.write("\n")


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

        for suite_id in self.suite_ids:
            # Expand the contents of the suite.
            suite = self.database.GetSuite(suite_id)
            ids_in_suite = suite.GetAllTestAndSuiteIds()[0]
            # Determine the results belonging to tests in the suite.
            results_in_suite = []
            for result in self.__test_results:
                if result.GetId() in ids_in_suite:
                    results_in_suite.append(result)
            # If there aren't any, skip.
            if len(results_in_suite) == 0:
                continue

            self.file.write("  %s\n" % suite.GetId())
            if self.expected_outcomes is None:
                self._SummarizeTestStats(results_in_suite)
            else:
                self._SummarizeRelativeTestStats(results_in_suite)

        
    def _SummarizeResults(self, results):
        """Summarize each of the results.

        'results' -- The sequence of 'Result' objects to summarize."""

        if len(results) == 0:
            self.file.write("  None.\n\n")
            return

        # Generate them.
	for result in results:
            self._DisplayResult(result, self.format)


    def _DisplayResult(self, result, format):
	"""Display 'result'.

	'result' -- The 'Result' of a test or resource execution.

        'format' -- The format to use when displaying results."""

	id_ = result.GetId()
        kind = result.GetKind()
	outcome = result.GetOutcome()

	# Print the ID and outcome.
	if self.expected_outcomes:
	    # If expected outcomes were specified, print the expected
	    # outcome too.
	    expected_outcome = \
	        self.expected_outcomes.get(id_, Result.PASS)
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
            self.file.write('    ' + result[Result.CAUSE] + '\n')
            
        self.file.write('\n')


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
            self.file.write("    %s:\n" % name)

            # Convert the HTML to text.
            s = StringIO.StringIO()
            w = formatter.DumbWriter(s)
            f = formatter.AbstractFormatter(w)
            p = htmllib.HTMLParser(f)
            p.feed(result[name])
            p.close()

            # Write out the text.
            for l in s.getvalue().splitlines():
                self.file.write("      " + l + "\n")
            self.file.write("\n")
        

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
	    self.file.write("  %-46s: %-8s, expected %-8s\n"
                            % (name, outcome, expected_outcome))
	else:
	    self.file.write("  %-46s: %-8s\n" % (name, outcome))

            
    def _DisplayHeading(self, heading):
        """Display 'heading'.

        'heading' -- The string to use as a heading for the next
        section of the report."""

        self.file.write("--- %s %s\n\n" %
                        (heading, "-" * (73 - len(heading))))

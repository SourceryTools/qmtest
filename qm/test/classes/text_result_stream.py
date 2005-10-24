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

import qm.common
import qm.fields
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

            In the "stats" format only the summary statistics are
            displayed.""",
            enumerals = ["brief", "batch", "full", "stats"]),
        qm.fields.TextField(
            name = "statistics_format",
            title = "Statistics Format",
            verbatim = "true",
            multiline = "true",
            description = """The format string used to display statistics.

            The format string is an ordinary Python format string.
            The following fill-ins are available:

            'TOTAL' -- The total number of tests.

            'EXPECTED' -- The total number of tests that had an
            expected outcome.

            'EXPECTED_PERCENT' -- The percentage of tests with
            expected outcomes.

            'UNEXPECTED' -- The total number of tests that had an 
            unexpected outcome.

            For each outcome 'O', there are additional fill-ins:

            'O' -- The total number of tests with outcome 'O'.
            
            'O_PERCENT' -- The percentage of tests with outcome 'O' to
            total tests, as a floating point value.

            'O_UNEXPECTED' -- The total number of tests with an
            unexpected outcome of 'O'.

            'O_UNEXEPECTED_PERCENT' -- The ratio of tests without an
            unexpected outcome of 'O' to total tests, as a floating
            point value."""),
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
            
        self.__first_test = 1
        # Keep track of tests and resources that had unexpected outcomes.
        self.__unexpected_test_results = []
        self.__unexpected_resource_results = []
        # And how many tests were run.
        self.__num_tests = 0
        # And how many tests there are with each outcome.
        self.__outcome_counts = {}
        for o in Result.outcomes:
            self.__outcome_counts[o] = 0
        # And how many unexpected tests there are with each outcome.
        self.__unexpected_outcome_counts = {}
        for o in Result.outcomes:
            self.__unexpected_outcome_counts[o] = 0


    def WriteResult(self, result):
        """Output a test or resource result.

        'result' -- A 'Result'."""

        # Record the results as they are received.
        if result.GetKind() == Result.TEST:
            # Remember how many tests we have processed.
            self.__num_tests += 1
            # Increment the outcome count.
            outcome = result.GetOutcome()
            self.__outcome_counts[outcome] += 1
            # Remember tests with unexpected results so that we can
            # display them at the end of the run.
            test_id = result.GetId()
            expected_outcome = self._GetExpectedOutcome(result.GetId())
            if self.format != "stats" and outcome != expected_outcome:
                self.__unexpected_outcome_counts[outcome] += 1
                self.__unexpected_test_results.append(result)
        else:
            if (self.format != "stats"
                and result.GetOutcome() != result.PASS):
                self.__unexpected_resource_results.append(result)
            
        # In some modes, no results are displayed as the tests are run.
        if self.format == "batch" or self.format == "stats":
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
            self.__unexpected_test_results.sort(compare_ids)
            # Print individual test results.
            if self.expected_outcomes:
                self._DisplayHeading("TESTS WITH UNEXPECTED OUTCOMES")
            else:
                self._DisplayHeading("TESTS THAT DID NOT PASS")
            self._SummarizeResults(self.__unexpected_test_results)

            if self.__unexpected_resource_results:
                # Sort resource results by ID.
                self.__unexpected_resource_results.sort(compare_ids)
                # Print individual resource results.
                self._DisplayHeading("RESOURCES THAT DID NOT PASS")
                self._SummarizeResults(self.__unexpected_resource_results)

        if self.format != "batch":
            self._DisplayStatistics()
        
        # Invoke the base class method.
        super(TextResultStream, self).Summarize()


    def _DisplayStatistics(self):
        """Write out statistical information about the results.

        Write out statistical information about the results."""

        # Summarize the test statistics.
        if self.statistics_format:
            self._FormatStatistics(self.statistics_format)
        elif self.expected_outcomes:
            self._SummarizeRelativeTestStats()
        else:
            self._SummarizeTestStats()


    def _SummarizeTestStats(self):
        """Generate statistics about the overall results."""

        # Print a header.
        self.file.write("\n")
        self._DisplayHeading("STATISTICS")

        # Build the format string.  If there are no tests we do not
        # provide any output.
        if self.__num_tests != 0:
            # Indicate the total number of tests.
            format = "  %(TOTAL)6d        tests total\n"
            # Include a line for each outcome.
            for o in Result.outcomes:
                if self.__outcome_counts[o] != 0:
                    format += ("  %%(%s)6d (%%(%s)3.0f%%%%) tests %s\n"
                               % (o, o + "_PERCENT", o))
            format += "\n"
        else:
            format = ""

        self._FormatStatistics(format)

        
    def _SummarizeRelativeTestStats(self):
        """Generate statistics showing results relative to expectations."""

        # Print a header.
        self.file.write("\n")
        self._DisplayHeading("STATISTICS")

        # Build the format string.  If there are no tests we do not
        # provide any output.
        if self.__num_tests != 0:
            # Indicate the total number of tests.
            format = ("  %(EXPECTED)6d (%(EXPECTED_PERCENT)3.0f%%) "
                      "tests as expected\n")
            # Include a line for each outcome.
            for o in Result.outcomes:
                if self.__unexpected_outcome_counts[o] != 0:
                    format += ("  %%(%s)6d (%%(%s)3.0f%%%%) tests "
                               "unexpected %s\n"
                               % (o + "_UNEXPECTED",
                                  o + "_UNEXPECTED_PERCENT",
                                  o))
            format += "\n"
        else:
            format = ""

        self._FormatStatistics(format)


    def _FormatStatistics(self, format):
        """Output statistical information.

        'format' -- A format string with (optional) fill-ins
        corresponding to statistical information.

        The formatted string is written to the result file."""

        # Build the dictionary of format fill-ins.
        num_tests = self.__num_tests
        unexpected = len(self.__unexpected_test_results)
        expected = num_tests - unexpected
        values = { "TOTAL" : num_tests,
                   "EXPECTED" : expected,
                   "UNEXPECTED" : unexpected }
        if num_tests:
            values["EXPECTED_PERCENT"] = (100. * expected) / num_tests
        else:
            values["EXPECTED_PERCENT"] = 0.0
        for o in Result.outcomes:
            count = self.__outcome_counts[o]
            values[o] = count
            if num_tests:
                values[o + "_PERCENT"] = (100. * count) / num_tests
            else:
                values[o + "_PERCENT"] = 0.0
            count = self.__unexpected_outcome_counts[o]
            values[o + "_UNEXPECTED"] = count
            if num_tests:
                values[o + "_UNEXPECTED_PERCENT"] = (100. * count) / num_tests
            else:
                values[o + "_UNEXPECTED_PERCENT"] = 0.0

        self.file.write(format % values)

        
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
        cause = result.GetCause()
        if cause:
            cause = qm.common.html_to_text(cause)
            for l in cause.splitlines():
                self.file.write("    " + l + "\n")
            
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
            text = qm.common.html_to_text(result[name])

            # Write out the text.
            for l in text.splitlines():
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

########################################################################
#
# File:   cmdline.py
# Author: Alex Samuel
# Date:   2001-03-16
#
# Contents:
#   QMTest command processing
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

########################################################################
# imports
########################################################################

import base
import os
import qm.cmdline
import qm.xmlutil
import string
import sys
import xmldb

########################################################################
# classes
########################################################################

class Command:
    """A QMTest command."""

    db_path_environment_variable = "QMTEST_DB_PATH"

    help_option_spec = (
        "h",
        "help",
        None,
        "Display usage summary."
        )

    verbose_option_spec = (
        "v",
        "verbose",
        None,
        "Display informational messages."
        )

    db_path_option_spec = (
        "D",
        "db-path",
        "PATH",
        "Path to the test database."
        )

    output_option_spec = (
        "o",
        "output",
        "FILE",
        "Write test results to FILE (- for stdout)."
        )

    no_output_option_spec = (
        None,
        "no-output",
        None,
        "Don't generate test results."
        )

    summary_option_spec = (
        "s",
        "summary",
        "FILE",
        "Write test summary to FILE (- for stdout)."
        )

    no_summary_option_spec = (
        "S",
        "no-summary",
        None,
        "Don't generate test summary."
        )

    outcomes_option_spec = (
        "O",
        "outcomes",
        "FILE",
        "Load expected outcomes from FILE."
        )

    context_option_spec = (
        "c",
        "context",
        "KEY=VALUE",
        "Add or override a context property.  You may specify this "
        "option more than once."
        )

    # Groups of options that should not be used together.
    conflicting_option_specs = (
        ( output_option_spec, no_output_option_spec ),
        ( summary_option_spec, no_summary_option_spec ),
        )

    global_options_spec = [
        help_option_spec,
        verbose_option_spec,
        db_path_option_spec,
        ]

    commands_spec = [
        ("run",
         "Run one or more tests.",
         "ID ...",
         "This command runs tests, prints their outcomes, and writes "
         "test results.  Specify one or more test IDs and "
         "suite IDs as arguments.",
         ( help_option_spec, output_option_spec, no_output_option_spec,
           summary_option_spec, no_summary_option_spec,
           outcomes_option_spec, context_option_spec )
         ),

        ]


    def __init__(self, program_name, argument_list):
        """Initialize a command.

        Parses the argument list but does not execute the command.

        'program_name' -- The name of the program, as invoked by the
        user.

        'argument_list' -- A sequence conaining the specified argument
        list."""

        # Build a command-line parser for this program.
        self.__parser = qm.cmdline.CommandParser(program_name,
                                                 self.global_options_spec,
                                                 self.commands_spec,
                                                 self.conflicting_option_specs)
        # Parse the command line.
        components = self.__parser.ParseCommandLine(argument_list)
        # Unpack the results.
        ( self.__global_options,
          self.__command,
          self.__command_options,
          self.__arguments
          ) = components


    def GetGlobalOption(self, option):
        """Return the value of global 'option', or 'None' it wasn't given."""

        for opt, opt_arg in self.__global_options:
            if opt == option:
                return opt_arg
        return None


    def GetCommandOption(self, option):
        """Return the value of command 'option', or 'None' it wasn't given."""

        for opt, opt_arg in self.__command_options:
            if opt == option:
                return opt_arg
        return None


    def Execute(self, output):
        """Execute the command.

        'output' -- The file object to send output to."""

        # If the global help option was specified, display it and stop.
        if self.GetGlobalOption("help") is not None:
            output.write(self.__parser.GetBasicHelp())
            return
        # If the command help option was specified, display it and stop.
        if self.GetCommandOption("help") is not None:
            output.write(self.__parser.GetCommandHelp(self.__command))
            return

        # Handle the verbose option.  The verbose level is the number of
        # times the verbose option was specified.
        self.__verbose = self.__global_options.count(("verbose", ""))

        # Make sure a command was specified.
        if self.__command == "":
            raise qm.cmdline.CommandError, qm.error("missing command")

        # Figure out the path to the test database.
        db_path = self.GetGlobalOption("db-path")
        if db_path is None:
            # The db-path option wasn't specified.  Try the environment
            # variable.
            try:
                db_path = os.environ[self.db_path_environment_variable]
            except KeyError:
                raise RuntimeError, \
                      qm.error("no db specified",
                               envvar=self.db_path_environment_variable)
        self.__database = xmldb.Database(db_path)

        # Dispatch to the appropriate method.
        method = {
            "run" : self.__ExecuteRun,
            }[self.__command]
        method(output)


    def GetDatabase(self):
        """Return the test database to use."""
        
        return self.__database


    def MakeContext(self):
        """Construct a 'Context' object for running tests."""

        context = base.Context(
            path=qm.rc.Get("path", os.environ["PATH"])
            )

        # Look for all occurrences of the '--context' option.
        for option, argument in self.__command_options:
            if option == "context":
                # Make sure the argument is correctly-formatted.
                if not "=" in argument:
                    raise qm.cmdline.CommandError, \
                          qm.error("invalid context assignment",
                                   argument=argument)
                # Parse the assignment.
                name, value = string.split(argument, "=", 1)
                try:
                    # Insert it into the context.
                    context[name] = value
                except ValueError, msg:
                    # The format of the context key is invalid, but
                    # raise a 'CommandError' instead.
                    raise qm.cmdline.CommandError, msg

        return context


    def __ExecuteRun(self, output):
        """Execute a 'run' command."""
        
        # Handle result options.
        result_file_name = self.GetCommandOption("output")
        if result_file_name is None:
            # By default, no result output.
            result_file = None
        elif result_file_name == "-":
            # Use standard output.
            result_file = sys.stdout
        else:
            # A named file.
            result_file = open(result_file_name, "w")

        # Handle summary options.
        summary_file_name = self.GetCommandOption("summary")
        # The default is generate a summary to standard output.
        if self.GetCommandOption("no-summary") is not None:
            # User asked to supress summary.
            summary_file = None
        elif summary_file_name is None:
            # User didn't specify anything, so by default write summary
            # to standard output.
            summary_file = sys.stdout
        elif summary_file_name == "-":
            # User specified standard output explicitly.
            summary_file = sys.stdout
        else:
            summary_file = open(summary_file_name, "w")

        # Handle the outcome option.
        outcomes_file_name = self.GetCommandOption("outcomes")
        if outcomes_file_name is not None:
            outcomes = base.load_outcomes(outcomes_file_name)
        else:
            outcomes = None

        database = self.GetDatabase()
        # Make sure some arguments were specified.  The arguments are
        # the IDs of tests and suites to run.
        if len(self.__arguments) == 0:
            raise qm.cmdline.CommandError, qm.error("no ids specified")
        try:
            test_ids = []
            # Validate test IDs and expand test suites in the arguments.
            base.expand_and_validate_ids(database,
                                         self.__arguments,
                                         test_ids)

            # Set up a test engine for running tests.
            engine = base.Engine(database)
            context = self.MakeContext()
            self.__output = output
            if self.__verbose > 0:
                # If running verbose, specify a callback function to
                # display test results while we're running.
                callback = self.__ProgressCallback
            else:
                # Otherwise no progress messages.
                callback = None
                
            # Run the tests.
            results = engine.RunTests(test_ids, context, callback)

            run_test_ids = results.keys()
            # Summarize outcomes.
            if summary_file is not None:
                self.__WriteSummary(test_ids, results, outcomes, summary_file)
                # Close it unless it's standard output.
                if summary_file is not sys.stdout:
                    summary_file.close()
            # Write out results.
            if result_file is not None:
                self.__WriteResults(test_ids, results, result_file)
                # Close it unless it's standard output.
                if result_file is not sys.stdout:
                    result_file.close()
        except:
            # FIXME: What exceptions need to be handled here?
            raise
                                                    

    def __ProgressCallback(self, test_id, result):
        """Display testing progress.

        'test_id' -- The ID of the test being run.

        'result' -- If 'None', the test is about to be run.  Otherwise
        the result of running the test."""
        
        if result is None:
            self.__output.write("%-38s: " % test_id)
        else:
            self.__output.write("%s\n" % result.GetOutcome())
        self.__output.flush()


    def __WriteSummary(self, test_ids, results, expected_outcomes, output):
        """Generate test result summary.

        'test_ids' -- The test IDs that were requested for the test run.

        'results' -- A mapping from test ID to result for tests that
        were actually run.

        'expected_outcomes' -- A map from test IDs to expected outcomes,
        or 'None' if there are no expected outcomes.

        'output' -- A file object to which to write the summary."""

        def divider(text):
            return "--- %s %s\n\n" % (text, "-" * (73 - len(text)))

        output.write("\n")
        output.write(divider("STATISTICS"))
        num_tests = len(results)
        output.write("  %6d        tests total\n\n" % num_tests)

        if expected_outcomes is not None:
            # Initialize a map with which we will count the number of
            # tests with each unexpected outcome.
            count_by_unexpected = {}
            for outcome in base.Result.outcomes:
                count_by_unexpected[outcome] = 0
            # Also, we'll count the number of tests that resulted in the
            # expected outcome, and the number for which we have no
            # expected outcome.
            count_expected = 0
            count_no_outcome = 0
            # Count tests by expected outcome.
            for test_id in results.keys():
                result = results[test_id]
                outcome = result.GetOutcome()
                # Do we have an expected outcome for this test?
                if expected_outcomes.has_key(test_id):
                    # Yes.
                    expected_outcome = expected_outcomes[test_id]
                    if outcome == expected_outcome:
                        # Outcome as expected.
                        count_expected = count_expected + 1
                    else:
                        # Unexpected outcome.  Count by actual (not
                        # expected) outcome.
                        count_by_unexpected[outcome] = \
                            count_by_unexpected[outcome] + 1
                else:
                    # No expected outcome for this test.
                    count_no_outcome = count_no_outcome + 1

            output.write("  %6d (%3.0f%%) tests as expected\n"
                         % (count_expected,
                            (100. * count_expected) / num_tests))
            for outcome in base.Result.outcomes:
                count = count_by_unexpected[outcome]
                if count > 0:
                    output.write("  %6d (%3.0f%%) tests unexpected %s\n"
                                 % (count, (100. * count) / num_tests,
                                    outcome))
            if count_no_outcome > 0:
                output.write("  %6d (%3.0f%%) tests with no "
                             "expected outcomes\n"
                             % (count_no_outcome,
                                (100. * count_no_outcome) / num_tests))
            output.write("\n")

        # Initialize a map with which we will count the number of tests
        # with each outcome.
        count_by_outcome = {}
        for outcome in base.Result.outcomes:
            count_by_outcome[outcome] = 0
        # Count tests by outcome.
        for result in results.values():
            outcome = result.GetOutcome()
            count_by_outcome[outcome] = count_by_outcome[outcome] + 1
        # Summarize these counts.
        for outcome in base.Result.outcomes:
            count = count_by_outcome[outcome]
            if count > 0:
                output.write("  %6d (%3.0f%%) tests %s\n"
                             % (count, (100. * count) / num_tests, outcome))
        output.write("\n")

        # If we have been provided with expected outcomes, report each
        # test whose outcome doesn't match the expected outcome.
        if expected_outcomes is not None:
            output.write(divider("TESTS WITH UNEXPECTED OUTCOMES"))
            # Scan over tests.
            for test_id in results.keys():
                result = results[test_id]
                outcome = result.GetOutcome()
                if not expected_outcomes.has_key(test_id):
                    # No expected outcome for this test; skip it.
                    continue
                expected_outcome = expected_outcomes[test_id]
                if outcome == expected_outcome:
                    # The outcome of this test is as expected; move on.
                    continue
                # This test produced an unexpected outcome, so report it.
                output.write("  %-32s: %-8s [expected %s]\n"
                             % (test_id, outcome, expected_outcome))
            output.write("\n")

        output.write(divider("TESTS THAT DID NOT PASS"))
        for test_id in results.keys():
            result = results[test_id]
            outcome = result.GetOutcome()
            extra = ""
            if outcome == base.Result.PASS:
                # Don't list tests that passed.
                continue
            elif outcome == base.Result.UNTESTED:
                # If the test was not run, print the failed prerequisite.
                prerequisite = result["failed_prerequisite"]
                prerequisite_outcome = results[prerequisite].GetOutcome()
                extra = "[%s was %s]" % (prerequisite, prerequisite_outcome)
            elif outcome == base.Result.FAIL:
                # If the result has a cause property, use it.
                if result.has_key("cause"):
                    extra = "[%s]" % result["cause"]
            output.write("  %-32s: %-8s %s\n" % (test_id, outcome, extra))
        output.write("\n")


    def __WriteResults(self, test_ids, results, output):
        """Generate full test results in XML format.

        'test_ids' -- The test IDs that were requested for the test run.

        'results' -- A mapping from test ID to result for tests that
        were actually run.

        'output' -- A file object to which to write the results."""

        document = qm.xmlutil.create_dom_document(
            public_id="-//Software Carpentry//QMTest Result V0.1//EN",
            dtd_file_name="result.dtd",
            document_element_tag="results"
            )
        # Add a result element for each test that was run.
        for test_id in results.keys():
            result = results[test_id]
            result_element = result.MakeDomElement(document)
            document.documentElement.appendChild(result_element)
        # Generate output.
        qm.xmlutil.write_dom_document(document, output)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

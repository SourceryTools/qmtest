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
import profile
import qm
import qm.cmdline
import qm.platform
import qm.xmlutil
import run
import string
import sys
import web.web
import whrandom

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
        None,
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
        "Add or override a context property."
        )

    context_file_spec = (
        "C",
        "load-context",
        "FILE",
        "Read context from a file (- for stdin)."
        )

    port_option_spec = (
        "P",
        "port",
        "PORT",
        "Server port number."
        )

    address_option_spec = (
        "A",
        "address",
        "ADDRESS",
        "Local address."
        )

    log_file_option_spec = (
        None,
        "log-file",
        "PATH",
        "Log file name."
        )

    start_browser_option_spec = (
        "b",
        "start-browser",
        None,
        "Open a browser window to the Web interface."
        )

    profile_option_spec = (
        None,
        "profile",
        "FILE",
        "Profile test execution to FILE."
        )

    concurrent_option_spec = (
        "j",
        "concurrency",
        "COUNT",
        "Execute tests in COUNT concurrent threads."
        )

    targets_option_spec = (
        "T",
        "targets",
        "FILE",
        "Load target specification from FILE."
        )

    seed_option_spec = (
        None,
        "seed",
        "INTEGER",
        "Seed the random number generator."
        )

    # Groups of options that should not be used together.
    conflicting_option_specs = (
        ( output_option_spec, no_output_option_spec ),
        ( summary_option_spec, no_summary_option_spec ),
        ( concurrent_option_spec, targets_option_spec ),
        )

    global_options_spec = [
        help_option_spec,
        verbose_option_spec,
        db_path_option_spec,
        ]

    commands_spec = [
        ("run",
         "Run one or more tests.",
         "[ ID ... ]",
         "This command runs tests, prints their outcomes, and writes "
         "test results.  You may specify test IDs and test suite IDs "
         "to run; omit arguments to run the entire test database.",
         (
           concurrent_option_spec,
           context_file_spec,
           context_option_spec,
           help_option_spec,
           no_output_option_spec,
           no_summary_option_spec,
           outcomes_option_spec,
           output_option_spec,
           profile_option_spec, 
           seed_option_spec,
           summary_option_spec,
           targets_option_spec,
           )
         ),

        ("server",
         "Start the web GUI server.",
         "",
         "Start the QMTest web GUI server.",
         [ help_option_spec, port_option_spec, address_option_spec,
           log_file_option_spec, start_browser_option_spec ]
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
        self.__parser = qm.cmdline.CommandParser(
            program_name,
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


    def HasGlobalOption(self, option):
        """Return true if global 'option' was specified."""

        for opt, opt_arg in self.__global_options:
            if opt == option:
                return 1
        return 0


    def GetGlobalOption(self, option, default=None):
        """Return the value of global 'option', or 'default' if omitted."""

        for opt, opt_arg in self.__global_options:
            if opt == option:
                return opt_arg
        return default


    def HasCommandOption(self, option):
        """Return true if command 'option' was specified."""

        for opt, opt_arg in self.__command_options:
            if opt == option:
                return 1
        return 0
    

    def GetCommandOption(self, option, default=None):
        """Return the value of command 'option', or 'default' if ommitted."""

        for opt, opt_arg in self.__command_options:
            if opt == option:
                return opt_arg
        return default


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
        qm.common.verbose = self.__global_options.count(("verbose", ""))

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
        try:
            base.load_database(db_path)
        except ValueError, exception:
            raise RuntimeError, str(exception)

        # Dispatch to the appropriate method.
        method = {
            "run" : self.__ExecuteRun,
            "server": self.__ExecuteServer,
            }[self.__command]
        method(output)


    def GetDatabase(self):
        """Return the test database to use."""
        
        return base.get_database()


    def MakeContext(self):
        """Construct a 'Context' object for running tests."""

        context = base.Context()

        for option, argument in self.__command_options:
            # Look for the '--context-file' option.
            if option == "context-file":
                if argument == "-":
                    # Read from standard input.
                    lines = sys.stdin.readlines()
                else:
                    # Read from a file.
                    try:
                        lines = open(argument, "r").readlines()
                    except:
                        raise qm.cmdline.CommandError, \
                              qm.error("could not read file",
                                       path=argument)
                lines = map(string.strip, lines)
                for line in lines:
                    if line == "":
                        # Blank line; skip it.
                        pass
                    elif qm.common.starts_with(line, "#"):
                        # Comment line; skip it.
                        pass
                    else:
                        self.__ParseContextAssignment(line, context)

            # Look for the '--context' option.
            elif option == "context":
                self.__ParseContextAssignment(argument, context)

        return context


    def __ParseContextAssignment(self, assignment, context):
        # Make sure the argument is correctly-formatted.
        if not "=" in assignment:
            raise qm.cmdline.CommandError, \
                  qm.error("invalid context assignment",
                           argument=assignment)
        # Parse the assignment.
        name, value = string.split(assignment, "=", 1)

        try:
            # Insert it into the context.
            context[name] = value
        except ValueError, msg:
            # The format of the context key is invalid, but
            # raise a 'CommandError' instead.
            raise qm.cmdline.CommandError, msg


    def __ExecuteRun(self, output):
        """Execute a 'run' command."""
        
        database = self.GetDatabase()

        # Handle 'result' options.
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

        # Handle 'summary' options.
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

        # Handle the 'outcome' option.
        outcomes_file_name = self.GetCommandOption("outcomes")
        if outcomes_file_name is not None:
            outcomes = base.load_outcomes(outcomes_file_name)
        else:
            outcomes = None
            
        # Handle the 'seed' option.  First create the random number
        # generator we will use.
        generator = whrandom.whrandom()
        seed = self.GetCommandOption("seed")
        if seed is None:
            # No seed was specified.  Seed the random number generator
            # from the system time. 
            generator.seed()
        else:
            # A seed was specified.  It should be an integer.
            try:
                seed = int(seed)
            except ValueError:
                raise qm.cmdline.CommandError, \
                      qm.error("seed not integer", seed=seed)
            # Use the specified seed.
            generator.seed(seed, 0, 0)

        # Make sure some arguments were specified.  The arguments are
        # the IDs of tests and suites to run.
        if len(self.__arguments) == 0:
            # No IDs specified; run the entire test database.
            self.__arguments.append(".")

        # Expand arguments in test IDs.
        try:
            test_ids, test_suites = base.expand_ids(self.__arguments)
        except (base.NoSuchTestError, base.NoSuchSuiteError), error:
            raise qm.cmdline.CommandError, str(error)

        if qm.common.verbose > 0:
            # If running verbose, specify a callback function to
            # display test results while we're running.
            message_function = self.__ProgressCallback
        else:
            # Otherwise no progress messages.
            message_function = None

        target_file_name = self.GetCommandOption("targets", None)
        if target_file_name is None:
            # No target file specified.  We'll use a single
            # 'SubprocessTarget' for running tests locally.  But perhaps
            # a concurrency value was specified.
            concurrency = self.GetCommandOption("concurrency", None)
            if concurrency is None:
                # No concurrency specified.  Run single-threaded.
                concurrency = 1
            else:
                # Convert the concurrency to an integer.
                try:
                    concurrency = int(concurrency)
                except ValueError:
                    raise qm.cmdline.CommandError, \
                          qm.error("concurrency not integer",
                                   value=concurrency)
            # Construct the target spec.
            # FIXME: Determine target group.
            target_specs = [
                run.TargetSpec("local",
                               "qm.test.run.SubprocessTarget",
                               "",
                               concurrency,
                               {}),
                ]
            
        else:
            # A target file was specified.  Load target specs from it.
            target_specs = run.load_target_specs(target_file_name)

        context = self.MakeContext()
        self.__output = output

        # Randomize the order of the tests.
        qm.common.shuffle(test_ids, generator=generator)

        # Run the tests.
        if self.HasCommandOption("profile"):
            # Profiling was requested.  Run in the profiler.
            profile_file = self.GetCommandOption("profile")
            p = profile.Profile()
            local_vars = locals()
            p = p.runctx(
                "results = run.test_run(test_ids, context, "
                "target_specs, message_function)",
                globals(), local_vars)
            results = local_vars["results"]
            p.dump_stats(profile_file)
        else:
            results = run.test_run(test_ids, context, target_specs,
                                   message_function)

        test_results, resource_results = results

        # Summarize outcomes.
        if summary_file is not None:
            self.__WriteSummary(test_ids, test_suites, test_results,
                                resource_results, outcomes, summary_file)
            # Close it unless it's standard output.
            if summary_file is not sys.stdout:
                summary_file.close()
        # Write out results.
        if result_file is not None:
            self.__WriteResults(test_ids, test_results,
                                resource_results, result_file)
            # Close it unless it's standard output.
            if result_file is not sys.stdout:
                result_file.close()
                                                    

    def __ProgressCallback(self, message):
        """Display testing progress.

        'message' -- A message indicating testing progress."""

        self.__output.write(message)
        self.__output.flush()


    def __ExecuteServer(self, output):
        """Process the server command."""

        database = self.GetDatabase()

        # Get the port number specified by a command option, if any.
        # Otherwise use a default value.
        port_number = self.GetCommandOption("port", default=8000)
        try:
            port_number = int(port_number)
        except ValueError:
            raise qm.cmdline.CommandError, qm.error("bad port number")
        # Get the local address specified by a command option, if any.
        # If not was specified, use the empty string, which corresponds
        # to all local addresses.
        address = self.GetCommandOption("address", default="")
        # Was a log file specified?
        log_file_path = self.GetCommandOption("log-file")
        if log_file_path == "-":
            # A hyphen path name means standard output.
            log_file = sys.stdout
        elif log_file_path is None:
            # No log file.
            log_file = None
        else:
            # Otherwise, it's a file name.  Open it for append.
            log_file = open(log_file_path, "a+")

        # Set up the server.
        server = web.web.make_server(database, port_number, address, log_file)

        # Construct the URL to the main page on the server.
        if address == "":
            url_address = qm.platform.get_host_name()
        else:
            url_address = address
        url = "http://%s:%d/test/dir" % (url_address, port_number)

        if self.HasCommandOption("start-browser"):
            # Now that the server is bound to its address, we can point
            # a browser at it safely.
            qm.platform.open_in_browser(url)
        else:
            message = qm.message("server url", url=url)
            qm.common.print_message(0, message + "\n")

        # Accept requests.
        server.Run()
    
    
    def __WriteSummary(self,
                       test_ids,
                       test_suites,
                       test_results,
                       resource_results,
                       expected_outcomes,
                       output):
        """Generate test result summary.

        'test_ids' -- The test IDs that were requested for the test run.

        'test_suites' -- IDs of test suites to report separately for the
        run. 

        'test_results' -- A mapping from test ID to result for tests that
        were actually run.

        'resource_results' -- A sequence of resource results.

        'expected_outcomes' -- A map from test IDs to expected outcomes,
        or 'None' if there are no expected outcomes.

        'output' -- A file object to which to write the summary."""

        database = base.get_database()

        def divider(text):
            return "--- %s %s\n\n" % (text, "-" * (73 - len(text)))

        output.write("\n")
        output.write(divider("TEST RUN STATISTICS"))
        num_tests = len(test_results)
        output.write("  %6d        tests total\n\n" % num_tests)

        if expected_outcomes is not None:
            output.write("  Test results relative to expected outcomes:\n\n")
            # Initialize a map with which we will count the number of
            # tests with each unexpected outcome.
            count_by_unexpected = {}
            for outcome in base.Result.outcomes:
                count_by_unexpected[outcome] = 0
            # Also, we'll count the number of tests that resulted in the
            # expected outcome.
            count_expected = 0
            # Count tests by expected outcome.
            for test_id in test_results.keys():
                result = test_results[test_id]
                outcome = result.GetOutcome()
                # Get the expected outcome for this test; if one isn't
                # specified, assume PASS.
                expected_outcome = expected_outcomes.get(test_id,
                                                         base.Result.PASS)
                if outcome == expected_outcome:
                    # Outcome as expected.
                    count_expected = count_expected + 1
                else:
                    # Unexpected outcome.  Count by actual (not
                    # expected) outcome.
                    count_by_unexpected[outcome] = \
                        count_by_unexpected[outcome] + 1

            output.write("  %6d (%3.0f%%) tests as expected\n"
                         % (count_expected,
                            (100. * count_expected) / num_tests))
            for outcome in base.Result.outcomes:
                count = count_by_unexpected[outcome]
                if count > 0:
                    output.write("  %6d (%3.0f%%) tests unexpected %s\n"
                                 % (count, (100. * count) / num_tests,
                                    outcome))
            output.write("\n")
            output.write("  Actual test results:\n\n")

        # Initialize a map with which we will count the number of tests
        # with each outcome.
        count_by_outcome = {}
        for outcome in base.Result.outcomes:
            count_by_outcome[outcome] = 0
        # Count tests by outcome.
        for result in test_results.values():
            outcome = result.GetOutcome()
            count_by_outcome[outcome] = count_by_outcome[outcome] + 1
        # Summarize these counts.
        for outcome, count in count_by_outcome.items():
            if count > 0:
                output.write("  %6d (%3.0f%%) tests %s\n"
                             % (count, (100. * count) / num_tests, outcome))
        output.write("\n")

        # Report results for test suites.
        if len(test_suites) > 0:
            output.write(divider("STATISTICS BY TEST SUITE"))
            for suite_id in test_suites:
                tests_in_suite = database.GetSuite(suite_id).GetTestIds()
                # Initialize a map with which we will count the number
                # of tests with each outcome.
                count_by_outcome = {}
                for outcome in base.Result.outcomes:
                    count_by_outcome[outcome] = 0
                # Count tests by outcome.
                for test_id in tests_in_suite:
                    result = test_results[test_id]
                    outcome = result.GetOutcome()
                    count_by_outcome[outcome] = count_by_outcome[outcome] + 1
                # Print results.
                output.write("  %s\n" % suite_id)
                suite_size = len(tests_in_suite)
                for outcome, count in count_by_outcome.items():
                    if count > 0:
                        output.write("  %6d (%3.0f%%) tests %s\n"
                                     % (count,
                                        (100. * count) / suite_size,
                                        outcome))
                output.write("\n")

        # If we have been provided with expected outcomes, report each
        # test whose outcome doesn't match the expected outcome.
        if expected_outcomes is not None:
            unexpected_ids = []

            # Filter function that keeps a test 'result' if its outcome
            # is not as expected in 'expected_outcomes'.
            def unexpected_filter(result, eo=expected_outcomes):
                outcome = result.GetOutcome()
                test_id = result.GetId()
                expected_outcome = eo.get(test_id, base.Result.PASS)
                return outcome != expected_outcome
                
            # Sort function for results.  The primary key is the
            # expected outcome for the result.  The secondary key is the
            # test ID.
            def unexpected_sorter(r1, r2, eo=expected_outcomes):
                tid1 = r1.GetId()
                tid2 = r2.GetId()
                o1 = eo.get(tid1, base.Result.PASS)
                o2 = eo.get(tid2, base.Result.PASS)
                if o1 != o2:
                    return cmp(base.Result.outcomes.index(o1),
                               base.Result.outcomes.index(o2))
                else:
                    return cmp(tid1, tid2)

            # Find results with unexpected outcomes.
            unexpected_results = filter(unexpected_filter,
                                        test_results.values())
            # Put them in an order convenient for users.
            unexpected_results.sort(unexpected_sorter)
            # Count 'em up.
            unexpected_count = len(unexpected_results)
            
            if unexpected_count > 0:
                # Report IDs of tests with unexpected outcomes.
                output.write(divider("TESTS WITH UNEXPECTED OUTCOMES"))
                for result in unexpected_results:
                    test_id = result.GetId()
                    # This test produced an unexpected outcome, so report it.
                    outcome = result.GetOutcome()
                    expected_outcome = expected_outcomes.get(test_id,
                                                             base.Result.PASS)
                    output.write("  %-32s: %-8s [expected %s]\n"
                                 % (test_id, outcome, expected_outcome))
                output.write("\n")

        # Count the number of tests that didn't pass.
        not_passing_count = len(filter(
            lambda r: r.GetOutcome() != base.Result.PASS,
            test_results.values()))

        # Summarize tests that didn't pass.
        if not_passing_count > 0:
            output.write(divider("TESTS THAT DID NOT PASS"))
            for test_id, result in test_results.items():
                outcome = result.GetOutcome()
                if outcome == base.Result.PASS:
                    # Don't list tests that passed.
                    continue
                # Print the test's ID and outcome.
                output.write("  %-63s: %-8s\n" % (test_id, outcome))
                # If a cause was specified, print it too.
                cause = result.get("cause", None)
                if cause is not None:
                    # Abbreviate the cause, if necessary.
                    if len(cause) > 70:
                        cause = cause[:67] + "..."
                    output.write("      %s\n\n" % cause)
            output.write("\n")

        # Count the number of failing resource functions.
        not_passing_count = len(filter(
            lambda r: r.GetOutcome() != base.Result.PASS,
            resource_results))

        # Summarize failed resource functions.
        if not_passing_count > 0:
            output.write(divider("RESOURCES THAT DID NOT PASS"))
            for result in resource_results:
                outcome = result.GetOutcome()
                if outcome != base.Result.PASS:
                    # Extract information from the result.
                    resource_id = result.GetId()
                    action = resource_id + " " + result["action"]
                    # If the name of the target on which the function ran is
                    # specified, include that in the output.
                    target = result.get("target", None)
                    if target is not None:
                        action = action + " on " + target
                    # Print the resource ID and outcome.
                    output.write("  %-63s: %-8s\n" % (action, outcome))
                    # If a cause was specified, print it too.
                    cause = result.get("cause", None)
                    if cause is not None:
                        # Abbreviate the cause, if necessary.
                        if len(cause) > 70:
                            cause = cause[:67] + "..."
                        output.write("      %s\n\n" % cause)
            output.write("\n")


 
    def __WriteResults(self, test_ids, test_results, resource_results, output):
        """Generate full test results in XML format.

        'test_ids' -- The test IDs that were requested for the test run.

        'test_results' -- A mapping from test ID to result for tests
        in the test run.

        'resource_results' -- A sequence of results of resource functions.

        'output' -- A file object to which to write the results."""

        base.write_results(test_results.values(), resource_results, output)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

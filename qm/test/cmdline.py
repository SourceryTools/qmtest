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
import string
import sys
import web.web

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
        "Add or override a context property."
        )

    context_file_spec = (
        "C",
        "context-file",
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
        "PROFILE-FILE",
        "Profile test execution to PROFILE-FILE."
        )

    concurrent_option_spec = (
        "j",
        "threads",
        "COUNT",
        "Execute tests in COUNT concurrent threads."
        )

    remote_option_spec = (
        "r",
        "remote-hosts",
        "HOST,...",
        "Execute test on HOSTs."
        )

    # Groups of options that should not be used together.
    conflicting_option_specs = (
        ( output_option_spec, no_output_option_spec ),
        ( summary_option_spec, no_summary_option_spec ),
        ( concurrent_option_spec, remote_option_spec ),
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
           outcomes_option_spec, context_option_spec, context_file_spec,
           profile_option_spec, concurrent_option_spec,
           remote_option_spec, )
         ),

        ("server",
         'Start the web GUI server.',
         '',
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
        base.load_database(db_path)

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

        context = base.Context(
            path=qm.rc.Get("path", os.environ["PATH"])
            )

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
            # We'll collect all the tests to run in this map. 
            test_ids = qm.common.OrderedMap()
            # This function adds a test to 'test_ids'.
            def add_test_id(test_id, test_ids=test_ids):
                test_ids[test_id] = None
            # Validate test IDs and expand test suites in the arguments.
            for argument in self.__arguments:
                if database.HasSuite(argument):
                    # It's a test suite.  Add all the test IDs in the
                    # suite. 
                    suite = database.GetSuite(argument)
                    map(add_test_id, suite.GetTestIds())
                elif database.HasTest(argument):
                    # It's a test.  Add it.
                    add_test_id(argument)
                else:
                    # It doesn't look like a test or suite.
                    raise qm.cmdline.CommandError, \
                          qm.error("unknown test or suite id", id=argument)
            test_ids = test_ids.keys()

            # Set up a test engine for running tests.
            remote_hosts = self.GetCommandOption("remote-hosts", None)
            concurrency = self.GetCommandOption("threads", None)
            
            if remote_hosts is not None:
                # The user specified remote hosts.  Run tests there.
                remote_hosts = string.split(remote_hosts, ",")
                remote_hosts = map(lambda host_name:
                                       base.RemoteTestHost(host_name),
                                   remote_hosts)
                rsh_program = qm.rc.Get("remote_shell",
                                        section="common",
                                        default="/usr/bin/ssh")
                engine = base.MultiRshEngine(remote_hosts, rsh_program)

            elif concurrency is not None:
                # The user specified concurrent testing.  Use the
                # multiprocess engine.
                try:
                    concurrency = int(concurrency)
                except:
                    concurrency = -1
                if concurrency < 1:
                    raise CommandError, qm.error("invalid concurrency")
                engine = base.MultiProcessEngine(concurrency)

            else:
                # Nothing special; execute tests serially, in-process.
                engine = base.InProcessEngine()

            context = self.MakeContext()
            self.__output = output
            if qm.common.verbose > 0:
                # If running verbose, specify a callback function to
                # display test results while we're running.
                callback = self.__ProgressCallback
            else:
                # Otherwise no progress messages.
                callback = None
                
            # Run the tests.
            if self.HasCommandOption("profile"):
                # Profiling was requested.  Run in the profiler.
                profile_file = self.GetCommandOption("profile")
                p = profile.Profile()
                local_vars = locals()
                p = p.runctx("results = "
                             "engine.RunTests(test_ids, context, callback)",
                             globals(), local_vars)
                results = local_vars["results"]
                p.dump_stats(profile_file)
            else:
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
        except ValueError, test_id:
            raise RuntimeError, qm.error("missing test id", test_id=test_id)
                                                    

    def __ProgressCallback(self, message):
        """Display testing progress.

        'message' -- A message indicating testing progress."""

        self.__output.write(message)
        self.__output.flush()


    def __ExecuteServer(self, output):
        """Process the server command."""

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
        server = web.web.make_server(port_number, address, log_file)

        # Construct the URL to the main page on the server.
        if address == "":
            url_address = qm.common.get_host_name()
        else:
            url_address = address
        url = "http://%s:%d/test/dir" % (url_address, port_number)

        if self.HasCommandOption("start-browser"):
            # Now that the server is bound to its address, we can point
            # a browser at it safely.
            qm.platform.open_in_browser(url)
        else:
            qm.common.print_message(0, "%s server running at %s .\n"
                                    % (qm.common.program_name, url))

        # Accept requests.
        server.Run()
    
    
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
            for test_id in results.keys():
                result = results[test_id]
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
            unexpected_ids = []

            # Filter function that keeps a test 'result' if its outcome
            # is not as expected in 'expected_outcomes'.
            def unexpected_filter(result, eo=expected_outcomes):
                outcome = result.GetOutcome()
                test_id = result.GetTestId()
                expected_outcome = eo.get(test_id, base.Result.PASS)
                return outcome != expected_outcome
                
            # Sort function for results.  The primary key is the
            # expected outcome for the result.  The secondary key is the
            # test ID.
            def unexpected_sorter(r1, r2, eo=expected_outcomes):
                tid1 = r1.GetTestId()
                tid2 = r2.GetTestId()
                o1 = eo.get(tid1, base.Result.PASS)
                o2 = eo.get(tid2, base.Result.PASS)
                if o1 != o2:
                    return cmp(base.Result.outcomes.index(o1),
                               base.Result.outcomes.index(o2))
                else:
                    return cmp(tid1, tid2)

            # Find results with unexpected outcomes.
            unexpected_results = filter(unexpected_filter, results.values())
            # Put them in an order convenient for users.
            unexpected_results.sort(unexpected_sorter)
            # Count 'em up.
            unexpected_count = len(unexpected_results)
            
            if unexpected_count > 0:
                # Report IDs of tests with unexpected outcomes.
                output.write(divider("TESTS WITH UNEXPECTED OUTCOMES"))
                for result in unexpected_results:
                    test_id = result.GetTestId()
                    # This test produced an unexpected outcome, so report it.
                    outcome = result.GetOutcome()
                    expected_outcome = expected_outcomes.get(test_id,
                                                             base.Result.PASS)
                    output.write("  %-32s: %-8s [expected %s]\n"
                                 % (test_id, outcome, expected_outcome))
                output.write("\n")

        output.write(divider("TESTS THAT DID NOT PASS"))
        non_passing_count = 0
        for test_id in results.keys():
            result = results[test_id]
            outcome = result.GetOutcome()
            extra = ""
            if outcome == base.Result.PASS:
                # Don't list tests that passed.
                continue
            # Keep count of how many didn't pass.
            non_passing_count = non_passing_count + 1
            if outcome == base.Result.UNTESTED:
                # If the test was not run, try to give some indication
                # of why.
                if result.has_key("failed_prerequisite"):
                    prerequisite = result["failed_prerequisite"]
                    prerequisite_outcome = results[prerequisite].GetOutcome()
                    extra = "[%s was %s]" \
                            % (prerequisite, prerequisite_outcome)
                elif result.has_key("failed_setup_resource"):
                    resource_id = result["failed_setup_resource"]
                    extra = "[setup %s failed]" % resource_id
            elif outcome == base.Result.FAIL \
                 or outcome == base.Result.ERROR:
                # If the result has a cause property, use it.
                if result.has_key("cause"):
                    extra = "[%s]" % result["cause"]
            output.write("  %-32s: %-8s %s\n" % (test_id, outcome, extra))

        if non_passing_count == 0:
            output.write("  (None)\n")
        output.write("\n")


    def __WriteResults(self, test_ids, results, output):
        """Generate full test results in XML format.

        'test_ids' -- The test IDs that were requested for the test run.

        'results' -- A mapping from test ID to result for tests that
        were actually run.

        'output' -- A file object to which to write the results."""

        base.write_results(results.values(), output)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

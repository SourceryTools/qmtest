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
import database
import os
import profile
import qm
import qm.cmdline
import qm.platform
from   qm.test.text_result_stream import *
from   qm.test.xml_result_stream import *
import qm.xmlutil
from   result import *
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
    """The environment variable specifying the test database path."""

    summary_formats = ("full", "brief", "stats", "none")
    """Valid formats for result summaries."""

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
        "tdb",
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

    outcomes_option_spec = (
        "O",
        "outcomes",
        "FILE",
        "Use expected outcomes in FILE."
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

    no_browser_option_spec = (
        None,
        "no-browser",
        None,
        "Do not open a new browser window."
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

    format_option_spec = (
        "f",
        "format",
        "FORMAT",
        "Specify the summary format."
        )

    tdb_class_option_spec = (
        "c",
        "class",
        "CLASS-NAME",
        "Specify the test database class."
        )

    # Groups of options that should not be used together.
    conflicting_option_specs = (
        ( output_option_spec, no_output_option_spec ),
        ( concurrent_option_spec, targets_option_spec ),
        )

    global_options_spec = [
        help_option_spec,
        verbose_option_spec,
        db_path_option_spec,
        ]

    commands_spec = [
        ("create-tdb",
         "Create a new test database.",
         "",
         "Create a new test database.",
         ( help_option_spec, tdb_class_option_spec, )
         ),

        ("gui",
         "Start the QMTest GUI.",
         "",
         "Start the QMTest graphical user interface.",
         ( help_option_spec, port_option_spec, address_option_spec,
           log_file_option_spec, no_browser_option_spec )
         ),

        ("run",
         "Run one or more tests.",
         "[ ID ... ]",
         """
Runs tests.  Optionally, generates a summary of the test run and a
record of complete test results.  You may specify test IDs and test
suite IDs to run; omit arguments to run the entire test database.

Test results are written to "results.qmr".  Use the '--output' option to
specify a different output file, or '--no-output' to supress results.

Use the '--format' option to specify the output format for the summary.
Valid formats are "full", "brief" (the default), "stats", and "none".
The summary is written to standard output.
         """,
         (
           concurrent_option_spec,
           context_file_spec,
           context_option_spec,
           format_option_spec,
           help_option_spec,
           no_output_option_spec,
           outcomes_option_spec,
           output_option_spec,
           profile_option_spec, 
           seed_option_spec,
           targets_option_spec,
           )
         ),

        ("summarize",
         "Summarize results from a test run.",
         "[FILE [ ID ... ]]",
         """
Loads a test results file and summarizes the results.  FILE is the path
to the results file.  Optionally, specify one or more test or suite IDs
whose results are shown.  If none are specified, shows all tests that
did not pass.

Use the '--format' option to specify the output format for the summary.
Valid formats are "full", "brief" (the default), "stats", and "none".
         """,
         ( help_option_spec, format_option_spec, outcomes_option_spec )
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
        db_path = self.GetGlobalOption("tdb")
        if db_path is None:
            # The db-path option wasn't specified.  Try the environment
            # variable.
            try:
                db_path = os.environ[self.db_path_environment_variable]
            except KeyError:
                raise RuntimeError, \
                      qm.error("no db specified",
                               envvar=self.db_path_environment_variable)
        # If the path is not already absolute, make it into an
        # absolute path at this point.
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)

        # Some commands don't require a test database.  
        if self.__command == "create-tdb":
            self.__ExecuteCreateTdb(output, db_path)
        else:
            # For the rest of the commands, we need to open the test
            # database first.
            try:
                # Create the database.
                base.load_database(db_path)
            except ValueError, exception:
                raise RuntimeError, str(exception)

            # Dispatch to the appropriate method.
            method = {
                "gui": self.__ExecuteServer,
                "run" : self.__ExecuteRun,
                "summarize": self.__ExecuteSummarize,
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


    def __ExecuteCreateTdb(self, output, db_path):
        """Handle the command for creating a new test database.

        'db_path' -- The path at which to create the new test database."""

        # Extract the test database class name.  Use the standard XML
        # implementation, if none was specified.
        class_name = self.GetCommandOption(
            "class", "qm.test.xmldb.Database")
        # Create the test database.
        base.create_database(db_path, class_name)
        # Print a helpful message.
        output.write(qm.message("new db message", path=db_path) + "\n")


    def __ExecuteSummarize(self, output):
        """Read in test run results and summarize."""

        # Look up the specified format.
        format = self.GetCommandOption("format", "brief")
        if format not in self.summary_formats:
            # Invalid format.  Complain.
            valid_format_string = string.join(
                map(lambda f: '"%s"' % f, self.summary_formats), ", ")
            raise qm.cmdline.CommandError, \
                  qm.error("invalid results format",
                           format=format,
                           valid_formats=valid_format_string)

        # If no results file is specified, use a default value.
        if len(self.__arguments) == 0:
            results_path = "results.qmr"
        else:
            results_path = self.__arguments[0]
        # Load results.
        try:
            test_results, resource_results = base.load_results(results_path)
        except (IOError, qm.xmlutil.ParseError), exception:
            raise RuntimeError, \
                  qm.error("invalid results file",
                           path=results_path,
                           problem=str(exception))
        else:
            # Don't need the map here.
            test_results = test_results.values()

        # Handle the 'outcome' option.
        outcomes_file_name = self.GetCommandOption("outcomes")
        if outcomes_file_name is not None:
            outcomes = base.load_outcomes(outcomes_file_name)
        else:
            outcomes = None
            
        # The remaining arguments, if any, are test and suite IDs.
        id_arguments = self.__arguments[1:]
        # Are there any?
        if len(id_arguments) > 0:
            # Expand arguments into test IDs.
            try:
                test_ids, suite_ids = base.expand_ids(id_arguments)
            except (qm.test.database.NoSuchTestError,
                    qm.test.database.NoSuchSuiteError), exception:
                raise qm.cmdline.CommandError, str(exception)
            except ValueError, exception:
                raise qm.cmdline.CommandError, \
                      qm.error("no such ID", id=str(exception))
            # Show only test results whose IDs were specified.
            test_results = filter(lambda r, ids=test_ids: r.GetId() in ids, 
                                  test_results)
            # Don't display any resource results.
            resource_results = []
        else:
            # No IDs specified.  Show all test and resource results.
            # Don't show any results by test suite though.
            suite_ids = []

        # Simulate the events that would have occurred during an
        # actual test run.
        stream = TextResultStream(output, format, outcomes, suite_ids)
        for r in test_results:
            stream.WriteResult(r)
        for r in resource_results:
            stream.WriteResult(r)
        stream.Summarize()
        

    def __ExecuteRun(self, output):
        """Execute a 'run' command."""
        
        database = self.GetDatabase()

        # Look up the summary format.
        format = self.GetCommandOption("format", "brief")
        if format not in self.summary_formats:
            # Invalid format.  Complain.
            valid_format_string = string.join(
                map(lambda f: '"%s"' % f, self.summary_formats), ", ")
            raise qm.cmdline.CommaneError, \
                  qm.error("invalid results format",
                           format=format,
                           valid_formats=valid_format_string)

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
        except (qm.test.database.NoSuchTestError,
                qm.test.database.NoSuchSuiteError), exception:
            raise qm.cmdline.CommandError, str(exception)
        except ValueError, exception:
            raise qm.cmdline.CommandError, \
                  qm.error("no such ID", id=str(exception))

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
            # Construct the target spec.  Set the target group to an
            # empty string, for lack of better information.
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

        # Create ResultStreams for textual output and for generating
        # a results file.
        result_streams = []
        if format != "none":
            result_streams.append(TextResultStream(output, format,
                                                   outcomes, test_suites))

        # Handle 'result' options.
        close_result_file = 0
        if self.HasCommandOption("no-output"):
            # User specified no output.
            result_file = None
        else:
            result_file_name = self.GetCommandOption("output", None)
            if result_file_name is None:
                # By default, write results to a default file.
                result_file_name = "results.qmr"

            if result_file_name == "-":
                # Use standard output.
                result_file = sys.stdout
            else:
                # A named file.  Open the file in unbufferred mode so
                # that results are written out immediately.
                result_file = open(result_file_name, "w", 0)
                close_result_file = 1
                
        if result_file is not None:
            result_streams.append(XMLResultStream(result_file))

        # Randomize the order of the tests.
        qm.common.shuffle(test_ids, generator=generator)

        # Run the tests.
        if self.HasCommandOption("profile"):
            # Profiling was requested.  Run in the profiler.
            profile_file = self.GetCommandOption("profile")
            p = profile.Profile()
            local_vars = locals()
            p = p.runctx(
                "run.test_run(test_ids, context, "
                "target_specs, result_streams)",
                globals(), local_vars)
            results = local_vars["results"]
            p.dump_stats(profile_file)
        else:
            run.test_run(test_ids, context, target_specs, result_streams)

        # Close the result file.
        if close_result_file:
            result_file.close()
                                                    

    def __ExecuteServer(self, output):
        """Process the server command."""

        database = self.GetDatabase()

        # Get the port number specified by a command option, if any.
        # Otherwise use a default value.
        port_number = self.GetCommandOption("port", default=0)
        try:
            port_number = int(port_number)
        except ValueError:
            raise qm.cmdline.CommandError, qm.error("bad port number")
        # Get the local address specified by a command option, if any.
        # If not was specified, use the loopback address.  The loopback
        # address is used by default for security reasons; it restricts
        # access to the QMTest server to users on the local machine.
        address = self.GetCommandOption("address", default="127.0.0.1")
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
        server = web.web.QMTestServer(database, port_number, address, log_file)
        port_number = server.GetServerAddress()[1]
        
        # Construct the URL to the main page on the server.
        if address == "":
            url_address = qm.platform.get_host_name()
        else:
            url_address = address
        url = "http://%s:%d/test/dir" % (url_address, port_number)

        if not self.HasCommandOption("no-browser"):
            # Now that the server is bound to its address, start the
            # web browser.
            qm.platform.open_in_browser(url)
            
        message = qm.message("server url", url=url)
        qm.common.print_message(0, message + "\n")

        # Accept requests.
        server.Run()


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   cmdline.py
# Author: Alex Samuel
# Date:   2001-03-16
#
# Contents:
#   QMTest command processing
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from   __future__ import nested_scopes
import base
import database
import os
import qm
import qm.cmdline
import qm.platform
from   qm.test.context import *
from   qm.test.execution_engine import *
from   qm.test.text_result_stream import *
from   qm.test.xml_result_stream import *
from   qm.trace import *
import qm.xmlutil
import Queue
import random
from   result import *
import string
import sys

########################################################################
# variables
########################################################################

_the_qmtest = None
"""The global 'QMTest' object."""

########################################################################
# classes
########################################################################

class QMTest:
    """An instance of QMTest."""

    db_path_environment_variable = "QMTEST_DB_PATH"
    """The environment variable specifying the test database path."""

    summary_formats = ("full", "brief", "stats", "none")
    """Valid formats for result summaries."""

    context_file_name = "context"
    """The default name of a context file."""
    
    expectations_file_name = "expectations.qmr"
    """The default name of a file containing expectations."""
    
    results_file_name = "results.qmr"
    """The default name of a file containing results."""
    
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

    version_option_spec = (
        None,
        "version",
        None,
        "Display version information."
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

    random_option_spec = (
        None,
        "random",
        None,
        "Run the tests in a random order."
        )

    rerun_option_spec = (
        None,
        "rerun",
        "FILE",
        "Rerun the tests that failed."
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

    attribute_option_spec = (
        "a",
        "attribute",
        "KEY=VALUE",
        "Set a database attribute."
        )

    # Groups of options that should not be used together.
    conflicting_option_specs = (
        ( output_option_spec, no_output_option_spec ),
        ( concurrent_option_spec, targets_option_spec ),
        )

    global_options_spec = [
        help_option_spec,
        verbose_option_spec,
        version_option_spec,
        db_path_option_spec,
        ]

    commands_spec = [
        ("create-tdb",
         "Create a new test database.",
         "",
         "Create a new test database.",
         ( help_option_spec,
           tdb_class_option_spec,
           attribute_option_spec)
         ),

        ("gui",
         "Start the QMTest GUI.",
         "",
         "Start the QMTest graphical user interface.",
         (
           address_option_spec,
           concurrent_option_spec,
           context_file_spec,
           context_option_spec,
           help_option_spec,
           log_file_option_spec,
           no_browser_option_spec,
           port_option_spec,
           targets_option_spec
           )
         ),

        ("remote",
         "Run QMTest as a remote server.",
         "",
         """
Runs QMTest as a remote server.  This mode is only used by QMTest
itself when distributing tests across multiple machines.  Users
should not directly invoke QMTest with this option.
         """,
         ()
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
           random_option_spec,
           rerun_option_spec,
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

    __version_output = \
        ("QMTest %s\n" 
         "Copyright (C) 2002 CodeSourcery, LLC\n"
         "QMTest comes with ABSOLUTELY NO WARRANTY\n"
         "For more information about QMTest visit http://www.qmtest.com\n")
    """The string printed when the --version option is used.

    There is one fill-in, for a string, which should contain the version
    number."""
    
    def __init__(self, program_name, argument_list,
                 major_version, minor_version, release_version):
        """Initialize a command.

        Parses the argument list but does not execute the command.

        'program_name' -- The name of the program, as invoked by the
        user.

        'argument_list' -- A sequence conaining the specified argument
        list.

        'major_version' -- The major version number.

        'minor_version' -- The minor version number.

        'release_version' -- The release version number."""

        global _the_qmtest
        
        _the_qmtest = self
        
        # Build a trace object.
        self.__tracer = Tracer()

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

        # Record the version information.
        self._major_version = major_version
        self._minor_version = minor_version
        self._release_version = release_version
        
        # We have not yet computed the set of available targets.
        self.targets = None


    def HasGlobalOption(self, option):
        """Return true if 'option' was specified as a global command.

        'command' -- The long name of the option, but without the
        preceding "--".

        returns -- True if the option is present."""

        return option in map(lambda x: x[0], self.__global_options)
    
        
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

        # If --version was given, print the version number and exit.
        # (The GNU coding standards require that the program take no
        # further action after seeing --version.)
        if self.HasGlobalOption("version"):
            sys.stdout.write(self.__version_output % self._GetVersionString())
            return
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

        # Look in several places to find the test database:
        #
        # 1. The command-line.
        # 2. The QMTEST_DB_PATH environment variable.
        # 3. The current directory.
        db_path = self.GetGlobalOption("tdb")
        if not db_path:
            if os.environ.has_key(self.db_path_environment_variable):
                db_path = os.environ[self.db_path_environment_variable]
            else:
                db_path = "."
        # If the path is not already absolute, make it into an
        # absolute path at this point.
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        # Normalize the path so that it is easy for the user to read
        # if it is emitted in an error message.
        db_path = os.path.normpath(db_path)
        
        # Some commands don't require a test database.
        if self.__command == "create-tdb":
            self.__ExecuteCreateTdb(output, db_path)
        else:
            # For the rest of the commands, we need to open the test
            # database first.
            self.__database = base.load_database(db_path)

            # Dispatch to the appropriate method.
            method = {
                "gui": self.__ExecuteServer,
                "remote" : self.__ExecuteRemote,
                "run" : self.__ExecuteRun,
                "summarize": self.__ExecuteSummarize,
                }[self.__command]
            method(output)


    def GetDatabase(self):
        """Return the test database to use."""
        
        return self.__database


    def GetTargets(self):
        """Return the 'Target' objects specified by the user.

        returns -- A sequence of 'Target' objects."""

        if self.targets is None:
            file_name = self.GetCommandOption("targets", None)
            if file_name is None:
                # No target file specified.  We'll use a single
                # 'ThreadTarget' for running tests locally.  But perhaps a
                # concurrency value was specified.
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
                # Construct the target.
                properties = {}
                if concurrency > 1:
                    class_name = "thread_target.ThreadTarget"
                    properties["concurrency"] = str(concurrency)
                else:
                    class_name = "serial_target.SerialTarget"
                target_class \
                    = get_extension_class(class_name,
                                          'target', self.GetDatabase())
                self.targets = [ target_class("local", "local", properties,
                                              self.GetDatabase()) ]
            else:
                document = qm.xmlutil.load_xml_file(file_name)
                targets_element = document.documentElement
                assert targets_element.tagName == "targets"
                self.targets = []
                for node in targets_element.getElementsByTagName("target"):
                    # Extract standard elements.
                    name = qm.xmlutil.get_child_text(node, "name")
                    class_name = qm.xmlutil.get_child_text(node, "class")
                    group = qm.xmlutil.get_child_text(node, "group")
                    # Extract properties.
                    properties = {}
                    for property_node in node.getElementsByTagName("property"):
                        property_name = property_node.getAttribute("name")
                        value = qm.xmlutil.get_dom_text(property_node)
                        properties[property_name] = value

                    # Find the target class.
                    target_class = get_extension_class(class_name,
                                                       'target',
                                                       self.GetDatabase())
                    # Build the target.
                    target = target_class(name, group, properties,
                                          self.GetDatabase())
                    # Accumulate targets.
                    self.targets.append(target)
            
        return self.targets
        

    def GetTracer(self):
        """Return the 'Tracer' associated with this instance of QMTest.

        returns -- The 'Tracer' associated with this instance of QMTest."""

        return self.__tracer

    
    def MakeContext(self):
        """Construct a 'Context' object for running tests."""

        context = Context()

        for option, argument in self.__command_options:
            # Look for the '--load-context' option.
            if option == "load-context":
                if argument == "-":
                    # Read from standard input.
                    file = sys.stdin
                else:
                    # Read from a named file.
                    try:
                        file = open(argument, "r")
                    except:
                        raise qm.cmdline.CommandError, \
                              qm.error("could not read file",
                                       path=argument)
                # Read the assignments.
                assignments = qm.common.read_assignments(file)
                # Add them to the context.
                for (name, value) in assignments.items():
                    try:
                        # Insert it into the context.
                        context[name] = value
                    except ValueError, msg:
                        # The format of the context key is invalid, but
                        # raise a 'CommandError' instead.
                        raise qm.cmdline.CommandError, msg

            # Look for the '--context' option.
            elif option == "context":
                # Parse the argument.
                name, value = qm.common.parse_assignment(argument)
            
                try:
                    # Insert it into the context.
                    context[name] = value
                except ValueError, msg:
                    # The format of the context key is invalid, but
                    # raise a 'CommandError' instead.
                    raise qm.cmdline.CommandError, msg

        return context


    def _GetVersionString(self):
        """Return the version string for this version of QMTest.

        returns -- The version string for this version of QMTest.  The
        string returned does not contain the name of the application; it
        contains only the version numbers."""

        version_string = "%d.%d" % (self._major_version, self._minor_version)
        if self._release_version:
            version_string += ".%d" % self._release_version
        return version_string
        
        
    def __ExecuteCreateTdb(self, output, db_path):
        """Handle the command for creating a new test database.

        'db_path' -- The path at which to create the new test database."""

        # Figure out what database class to use.
        class_name \
            = self.GetCommandOption("class", "qm.test.xmldb.Database")
        # There are no attributes yet.
        attributes = {}
        # Process attributes provided on the command line.
        for option, argument in self.__command_options:
            if option == "attribute":
                name, value = qm.common.parse_assignment(argument)
                attributes[name] = value
        # Create the test database.
        base.create_database(db_path, class_name, attributes)
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
            results = base.load_results(open(results_path, "r"))
            test_results = filter(lambda r: r.GetKind() == Result.TEST,
                                  results)
            resource_results = \
                filter(lambda r: r.GetKind() == Result.RESOURCE,
                       results)
        except (IOError, qm.xmlutil.ParseError), exception:
            raise QMException, \
                  qm.error("invalid results file",
                           path=results_path,
                           problem=str(exception))

        # Get the expected outcomes.
        outcomes = self.__GetExpectedOutcomes()
            
        # The remaining arguments, if any, are test and suite IDs.
        id_arguments = self.__arguments[1:]
        # Are there any?
        if len(id_arguments) > 0:
            # Expand arguments into test IDs.
            try:
                test_ids, suite_ids \
                          = self.GetDatabase().ExpandIds(id_arguments)
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
        stream = TextResultStream(output, format, outcomes,
                                  self.GetDatabase(), suite_ids)
        for r in test_results:
            stream.WriteResult(r)
        for r in resource_results:
            stream.WriteResult(r)
        stream.Summarize()
        

    def __ExecuteRemote(self, output):
        """Execute the 'remote' command."""

        database = self.GetDatabase()

        # Get the target class.  For now, we always run in serial when
        # running remotely.
        target_class = get_extension_class("serial_target.SerialTarget",
                                           'target', database)
        # Build the target.
        target = target_class("child", None, {}, database)

        # Start the target.
        response_queue = Queue.Queue(0)
        target.Start(response_queue)
        
        # Read commands from standard input, and reply to standard
        # output.
        while 1:
            # Read the command.
            command = cPickle.load(sys.stdin)
            
            # If the command is just a string, it should be
            # the 'Stop' command.
            if isinstance(command, types.StringType):
                assert command == "Stop"
                target.Stop()
                break

            # Decompose command.
            method, id, context = command
            # Get the descriptor.
            descriptor = database.GetTest(id)
            # Run it.
            target.RunTest(descriptor, context)
            # There are no results yet.
            results = []
            # Read all of the results.
            while 1:
                try:
                    result = response_queue.get(0)
                    results.append(result)
                except Queue.Empty:
                    # There are no more results.
                    break
            # Pass the results back.
            cPickle.dump(results, sys.stdout)
            # The standard output stream is bufferred, but the master
            # will block waiting for a response, so we must flush
            # the buffer here.
            sys.stdout.flush()


    def __ExecuteRun(self, output):
        """Execute a 'run' command."""
        
        database = self.GetDatabase()

        # Look up the summary format.
        format = self.GetCommandOption("format", "brief")
        if format not in self.summary_formats:
            # Invalid format.  Complain.
            valid_format_string = string.join(
                map(lambda f: '"%s"' % f, self.summary_formats), ", ")
            raise qm.cmdline.CommandError, \
                  qm.error("invalid results format",
                           format=format,
                           valid_formats=valid_format_string)

        # Get the expected outcomes.
        expectations = self.__GetExpectedOutcomes()

        # Handle the 'seed' option.  First create the random number
        # generator we will use.
        seed = self.GetCommandOption("seed")
        if seed:
            # A seed was specified.  It should be an integer.
            try:
                seed = int(seed)
            except ValueError:
                raise qm.cmdline.CommandError, \
                      qm.error("seed not integer", seed=seed)
            # Use the specified seed.
            random.seed(seed)

        # Figure out what tests to run.
        if len(self.__arguments) == 0:
            # No IDs specified; run the entire test database.
            self.__arguments.append("")

        # Expand arguments in test IDs.
        try:
            test_ids, test_suites \
                      = self.GetDatabase().ExpandIds(self.__arguments)
        except (qm.test.database.NoSuchTestError,
                qm.test.database.NoSuchSuiteError), exception:
            raise qm.cmdline.CommandError, str(exception)
        except ValueError, exception:
            raise qm.cmdline.CommandError, \
                  qm.error("no such ID", id=str(exception))

        # Filter the set of tests to be run, eliminating any that should
        # be skipped.
        test_ids = self.__FilterTestsToRun(test_ids, expectations)
        
        # Figure out which targets to use.
        targets = self.GetTargets()
        # Compute the context in which the tests will be run.
        context = self.MakeContext()

        # Create ResultStreams for textual output and for generating
        # a results file.
        result_streams = []
        if format != "none":
            stream = TextResultStream(output, format, expectations,
                                      self.GetDatabase(), test_suites)
            result_streams.append(stream)

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

        try:
            if self.HasCommandOption("random"):
                # Randomize the order of the tests.
                random.shuffle(test_ids)
            else:
                test_ids.sort()
            
            # Run the tests.
            engine = ExecutionEngine(database, test_ids, context, targets,
                                     result_streams)
            engine.Run()
        finally:
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

        # Figure out which targets to use.
        targets = self.GetTargets()
        # Compute the context in which the tests will be run.
        context = self.MakeContext()

        # Delay importing this module until absolutely necessary since
        # the GUI requires threads, and, in general, we do not assume
        # that threads are available.
        import qm.test.web.web
        # Set up the server.
        server = qm.test.web.web.QMTestServer(database, port_number, address,
                                              log_file, targets, context)
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


    def __GetExpectedOutcomes(self):
        """Return the expected outcomes for this test run.

        returns -- A map from test names to outcomes corresponding to
        the expected outcome files provided on the command line.  If no
        expected outcome files are provided, 'None' is returned."""

        outcomes_file_name = self.GetCommandOption("outcomes")
        if not outcomes_file_name:
            return None

        try:
            return base.load_outcomes(open(outcomes_file_name, "r"))
        except IOError, e:
            raise qm.cmdline.CommandError, str(e)
        
        
    def __FilterTestsToRun(self, test_names, expectations):
        """Return those tests from 'test_names' that should be run.

        'test_names' -- A sequence of test names.

        'expectations' -- A map from test names to expected outcomes, or
        'None' if there are no expected outcomes.
        
        returns -- Those elements of 'test_names' that are not to be
        skipped.  If 'a' precedes 'b' in 'test_names', and both 'a' and
        'b' are present in the result, 'a' will precede 'b' in the
        result."""

        # The --rerun option indicates that only failing tests should
        # be rerun.
        rerun_file_name = self.GetCommandOption("rerun")
        if rerun_file_name:
            # Load the outcomes from the file specified.
            outcomes = base.load_outcomes(open(rerun_file_name))
            # We can avoid treating the no-expectation case as special
            # by creating an empty map.
            if expectations is None:
                expectations = {}
            # Filter out tests that have unexpected outcomes.
            test_names \
                = filter(lambda n: \
                             (outcomes.get(n, Result.PASS) 
                              != expectations.get(n, Result.PASS)),
                         test_names)
        
        return test_names

                       
########################################################################
# functions
########################################################################

def get_qmtest():
    """Returns the global QMTest object.

    returns -- The 'QMTest' object that corresponds to the currently
    executing thread.

    At present, there is only one QMTest object per process.  In the
    future, however, there may be more than one.  Then, this function
    will return different values in different threads."""

    return _the_qmtest
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

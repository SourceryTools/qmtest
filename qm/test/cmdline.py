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
from   qm.test.pickle_result_stream import PickleResultStream
from   qm.trace import *
import qm.test.web.web
import qm.xmlutil
import Queue
import random
from   result import *
import signal
import string
import sys
import xml.sax

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

    target_file_name = "targets"
    """The default name of a file containing targets."""
    
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

    daemon_option_spec = (
        None,
        "daemon",
        None,
        "Run as a daemon."
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

    pid_file_option_spec = (
        None,
        "pid-file",
        "PATH",
        "Process ID file name."
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
        "Use FILE as the target specification file."
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

    extension_kind_option_spec = (
        "k",
        "kind",
        "EXTENSION-KIND",
        "Specify the kind of extension class."
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
        ("create-target",
         "Create (or update) a target specification.",
         "NAME CLASS [ GROUP ]",
         "Create (or update) a target specification.",
         ( attribute_option_spec,
           help_option_spec,
           targets_option_spec
           )
         ),

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
           daemon_option_spec,
           help_option_spec,
           log_file_option_spec,
           no_browser_option_spec,
           pid_file_option_spec,
           port_option_spec,
           targets_option_spec
           )
         ),

        ("extensions",
         "List extension classes.",
         "",
         """
List the available extension classes.

Use the '--kind' option to limit the classes displayed to test classes,
resource classes, etc.  The parameter to '--kind' can be one of 'test',
'resource', 'database', or 'target'.
         """,
         (
           extension_kind_option_spec,
           help_option_spec,
         )
        ),

        ("help",
         "Display usage summary.",
         "",
         "Display usage summary.",
         ()
         ),

        ("register",
         "Register an extension class.",
         "KIND CLASS",
         """
Register an extension class with QMTest.  KIND is the kind of extension
class to register; it must be one of 'test', 'resource', 'database',
or 'target'.

The CLASS gives the name of the class in the form 'module.class'.

QMTest will search the available extension class directories to find the
new CLASS.  QMTest looks for files whose basename is the module name and
whose extension is either '.py', '.pyc', or '.pyo'.

QMTest will then attempt to load the extension class.  If the extension
class cannot be loaded, QMTest will issue an error message to help you
debug the problem.  Otherwise, QMTest will update the 'classes.qmc' file
in the directory containing the module to mention your new extension class.
         """,
         ()
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
    
    def __init__(self, argument_list,
                 major_version, minor_version, release_version):
        """Construct a new QMTest.

        Parses the argument list but does not execute the command.

        'argument_list' -- The arguments to QMTest, not including the
        initial argv[0].

        'major_version' -- The major version number.

        'minor_version' -- The minor version number.

        'release_version' -- The release version number."""

        global _the_qmtest
        
        _the_qmtest = self
        
        # Use the stadard stdout and stderr streams to emit messages.
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        
        # Build a trace object.
        self.__tracer = Tracer()

        # Build a command-line parser for this program.
        self.__parser = qm.cmdline.CommandParser(
            "qmtest",
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

        # If available, record the path to the qmtest executable.
        self.__qmtest_path = os.environ.get("QM_PATH")
        
        # Record the version information.
        self._major_version = major_version
        self._minor_version = minor_version
        self._release_version = release_version

        # We have not yet loaded the database.
        self.__database = None
        
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


    def Execute(self):
        """Execute the command.

        returns -- 0 if the command was executed successfully.  1 if
        there was a problem or if any tests run had unexpected outcomes."""

        # If --version was given, print the version number and exit.
        # (The GNU coding standards require that the program take no
        # further action after seeing --version.)
        if self.HasGlobalOption("version"):
            self._stderr.write(self.__version_output
                               % self._GetVersionString())
            return 0
        # If the global help option was specified, display it and stop.
        if (self.GetGlobalOption("help") is not None 
            or self.__command == "help"):
            self._stderr.write(self.__parser.GetBasicHelp())
            return 0
        # If the command help option was specified, display it and stop.
        if self.GetCommandOption("help") is not None:
            self.__WriteCommandHelp(self.__command)
            return 0

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
        self.__db_path = os.path.normpath(db_path)

        error_occurred = 0
        
        # Dispatch to the appropriate method.
        if self.__command == "create-tdb":
            self.__ExecuteCreateTdb(db_path)
            return 0
        
        method = {
            "create-target" : self.__ExecuteCreateTarget,
            "extensions" : self.__ExecuteExtensions,
            "gui" : self.__ExecuteServer,
            "register" : self.__ExecuteRegister,
            "remote" : self.__ExecuteRemote,
            "run" : self.__ExecuteRun,
            "summarize": self.__ExecuteSummarize,
            }[self.__command]

        return method()


    def GetDatabase(self):
        """Return the test database to use."""

        if not self.__database:
            self.__database = database.load_database(self.__db_path)
            
        return self.__database


    def GetTargetFileName(self):
        """Return the path to the file containing target specifications.

        returns -- The path to the file containing target specifications."""

        # See if the user requested a specific target file.
        target_file_name = self.GetCommandOption("targets")
        if target_file_name:
            return target_file_name
        # If there was no explicit option, use the "targets" file in the
        # database directory.
        return os.path.join(self.GetDatabase().GetConfigurationDirectory(),
                            self.target_file_name)
    

    def GetTargetsFromFile(self, file_name):
        """Return the 'Target's specified in 'file_name'.

        returns -- A list of the 'Target' objects specified in the
        target specification file 'file_name'."""

        try:
            document = qm.xmlutil.load_xml_file(file_name)
            targets_element = document.documentElement
            if targets_element.tagName != "targets":
                raise QMException, \
                      qm.error("could not load target file",
                               file = file_name)
            targets = []
            for node in targets_element.getElementsByTagName("extension"):
                # Parse the DOM node.
                target_class, arguments \
                    = (qm.extension.parse_dom_element
                       (node,
                        lambda n: get_extension_class(n, "target",
                                                      self.GetDatabase())))
                # Build the target.
                target = target_class(self.GetDatabase(), arguments)
                # Accumulate targets.
                targets.append(target)

            return targets
        except Context:
            raise QMException, \
                  qm.error("could not load target file",
                           file=file_name)

        
        
    def GetTargets(self):
        """Return the 'Target' objects specified by the user.

        returns -- A sequence of 'Target' objects."""

        if self.targets is None:
            file_name = self.GetTargetFileName()
            if os.path.exists(file_name):
                self.targets = self.GetTargetsFromFile(file_name)
            else:
                # The target file does not exist.
                concurrency = self.GetCommandOption("concurrency")
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
                arguments = {}
                arguments["name"] = "local"
                arguments["group"] = "local"
                if concurrency > 1:
                    class_name = "thread_target.ThreadTarget"
                    arguments["threads"] = concurrency
                else:
                    class_name = "serial_target.SerialTarget"
                target_class \
                    = get_extension_class(class_name,
                                          'target', self.GetDatabase())
                self.targets = [ target_class(self.GetDatabase(), arguments) ]
            
        return self.targets
        

    def GetTracer(self):
        """Return the 'Tracer' associated with this instance of QMTest.

        returns -- The 'Tracer' associated with this instance of QMTest."""

        return self.__tracer

    
    def MakeContext(self):
        """Construct a 'Context' object for running tests."""

        context = Context()

        # First, see if a context file was specified on the command
        # line.
        use_implicit_context_file = 1
        for option, argument in self.__command_options:
            if option == "load-context":
                use_implicit_context_file = 0
                break

        # If there is no context file, read the default context file.
        if (use_implicit_context_file
            and os.path.isfile(self.context_file_name)):
            context.Read(self.context_file_name)
                
        for option, argument in self.__command_options:
            # Look for the '--load-context' option.
            if option == "load-context":
                context.Read(argument)
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


    def GetExecutablePath(self):
        """Return the path to the QMTest executable.

        returns -- A string giving the path to the QMTest executable.
        This is the path that should be used to invoke QMTest
        recursively.  Returns 'None' if the path to the QMTest
        executable is uknown."""

        return self.__qmtest_path
    
    
    def _GetVersionString(self):
        """Return the version string for this version of QMTest.

        returns -- The version string for this version of QMTest.  The
        string returned does not contain the name of the application; it
        contains only the version numbers."""

        version_string = "%d.%d" % (self._major_version, self._minor_version)
        if self._release_version:
            version_string += ".%d" % self._release_version
        return version_string
        

    def __GetAttributeOptions(self):
        """Return the attributes specified on the command line.

        returns -- A dictionary mapping attribute names (strings) to
        values (strings).  There is an entry for each attribute
        specified with '--attribute' on the command line."""

        # There are no attributes yet.
        attributes = {}

        # Go through the command line looking for attribute options.
        for option, argument in self.__command_options:
            if option == "attribute":
                name, value = qm.common.parse_assignment(argument)
                attributes[name] = value

        return attributes
    
        
    def __ExecuteCreateTdb(self, db_path):
        """Handle the command for creating a new test database.

        'db_path' -- The path at which to create the new test database."""

        # Figure out what database class to use.
        class_name \
            = self.GetCommandOption("class", "xml_database.XMLDatabase")
        # Get the attributes.
        attributes = self.__GetAttributeOptions()
        # Create the test database.
        database.create_database(db_path, class_name, attributes)
        # Print a helpful message.
        self._stdout.write(qm.message("new db message", path=db_path) + "\n")


    def __ExecuteCreateTarget(self):
        """Create a new target file."""

        # Make sure that the arguments are correct.
        if (len(self.__arguments) < 2 or len(self.__arguments) > 3):
            self.__WriteCommandHelp("create-target")
            return 1

        # Pull the required arguments out of the command line.
        target_name = self.__arguments[0]
        class_name = self.__arguments[1]
        if (len(self.__arguments) > 2):
            target_group = self.__arguments[2]
        else:
            target_group = ""

        # Load the database.
        database = self.GetDatabase()

        # Load the target class.
        target_class = qm.test.base.get_extension_class(class_name,
                                                        "target",
                                                        database)

        # Get the dictionary of class arguments.
        field_dictionary \
            = qm.extension.get_class_arguments_as_dictionary(target_class)

        # Get the name of the target file.
        file_name = self.GetTargetFileName()
        # If the file already exists, read it in.
        if os.path.exists(file_name):
            # Load the document.
            document = qm.xmlutil.load_xml_file(file_name)
            # If there is a previous entry for this target, discard it.
            targets_element = document.documentElement
            duplicates = []
            for target_element \
                in targets_element.getElementsByTagName("extension"):
                for attribute \
                    in target_element.getElementsByTagName("argument"):
                    if attribute.getAttribute("name") == "name":
                        name = field_dictionary["name"].\
                               GetValueFromDomNode(attribute.childNodes[0],
                                                   None)
                        if name == target_name:
                            duplicates.append(target_element)
                            break
            for duplicate in duplicates:
                targets_element.removeChild(duplicate)
                duplicate.unlink()
        else:
            document = (qm.xmlutil.create_dom_document
                        (public_id = dtds["target"],
                         dtd_file_name = "target.dtd",
                         document_element_tag = "targets"))
            targets_element = document.documentElement
            
        # Get the attributes.
        attributes = self.__GetAttributeOptions()
        attributes["name"] = target_name
        attributes["group"] = target_group
        attributes = qm.extension.validate_arguments(target_class,
                                                     attributes)
        
        # Create the target element.
        target_element = qm.extension.make_dom_element(target_class,
                                                       attributes,
                                                       document)
        targets_element.appendChild(target_element)

        # Write out the XML file.
        document.writexml(open(self.GetTargetFileName(), "w"))
        
        return 0

    
    def __ExecuteExtensions(self):
        """List the available extension classes."""

        try:
            database = self.GetDatabase()
        except:
            # If the database could not be opened that's OK; this
            # command can be used without a database.
            database = None

        # Figure out what kinds of extensions we're going to list.
        kind = self.GetCommandOption("kind")
        kinds = ['test', 'resource', 'database', 'target']
        if kind:
            if kind not in kinds:
                raise qm.cmdline.CommandError, \
                      qm.error("invalid extension kind",
                               kind = kind)
            kinds = [kind]

        for kind in kinds:
            # Get the available classes.
            names = qm.test.base.get_extension_class_names(kind,
                                                           database,
                                                           self.__db_path)
            # Build structured text describing the classes.
            description = "** Available %s classes **\n\n" % kind
            for n in names:
                description += "  * " + n + "\n\n    "
                # Try to load the class to get more information.
                try:
                    extension_class \
                        = qm.test.base.get_extension_class(n, kind, database)
                    description \
                        += qm.extension.get_class_description(extension_class,
                                                              brief=1)
                except:
                    description += ("No description available: "
                                    "could not load class.")
                description += "\n\n"
                
            self._stdout.write(qm.structured_text.to_text(description))
            

    def __ExecuteRegister(self):
        """Register a new extension class."""

        # Make sure that the KIND and CLASS were specified.
        if (len(self.__arguments) != 2):
            self.__WriteCommandHelp("register")
            return 1
        kind = self.__arguments[0]
        class_name = self.__arguments[1]

        # Check that the KIND is valid.
        if kind not in ['test', 'resource', 'database', 'target']:
            raise qm.cmdline.CommandError, \
                  qm.error("invalid extension kind",
                           kind = kind)

        # Check that the CLASS_NAME is well-formed.
        if class_name.count('.') != 1:
            raise qm.cmdline.CommandError, \
                  qm.error("invalid class name",
                           class_name = class_name)
        module, name = class_name.split('.')

        # Try to load the database.  It may provide additional
        # directories to search.
        try:
            database = self.GetDatabase()
        except:
            database = None
        # Hunt through all of the extension class directories looking
        # for an appropriately named module.
        found = None
        directories = get_extension_directories(kind, database,
                                                self.__db_path)
        for directory in directories:
            for ext in (".py", ".pyc", ".pyo"):
                file_name = os.path.join(directory, module + ext)
                if os.path.exists(file_name):
                    found = file_name
                    break
            if found:
                break

        # If we could not find the module, issue an error message.
        if not found:
            raise qm.QMException, \
                  qm.error("module does not exist",
                           module = module)

        # Inform the user of the location in which QMTest found the
        # module.  (Sometimes, there might be another module with the
        # same name in the path.  Telling the user where we've found
        # the module will help the user to deal with this situation.)
        self._stdout.write(qm.structured_text.to_text
                           (qm.message("loading class",
                                       class_name = name,
                                       file_name = found)))
        
        # We have found the module.  Try loading it.
        try:
            extension_class = get_extension_class_from_directory(class_name,
                                                                 kind,
                                                                 directory,
                                                                 directories)
        except PythonException, pe:
            # The class could not be loaded.  Show a traceback.
            self._stderr.write(qm.common.format_exception
                               ((pe.exc_type, pe.exc_value,
                                 sys.exc_info()[2])))
            raise QMException, \
                  qm.error("could not load extension class",
                           class_name = class_name)

        # Update the classes.qmc file.  If it already exists, we must
        # read it in first.
        classes_file_name = os.path.join(directory, "classes.qmc")
        try:
            document = qm.xmlutil.load_xml_file(classes_file_name)
        except:
            document = (qm.xmlutil.create_dom_document
                        (public_id=qm.test.base.dtds["class-directory"],
                         dtd_file_name="class-directory.dtd",
                         document_element_tag="class-directory"))

        # Remove any previous entries for this class.
        duplicates = []
        for element in qm.xmlutil.get_children(document.documentElement,
                                               "class"):
            if (str(qm.xmlutil.get_dom_text(element)) == class_name):
                duplicates.append(element)
        for element in duplicates:
            document.documentElement.removeChild(element)
            element.unlink()
                
        # Construct the new node.
        class_element = (qm.xmlutil.create_dom_text_element
                         (document, "class", class_name))
        class_element.setAttribute("kind", kind)
        document.documentElement.appendChild(class_element)

        # Write out the file.
        document.writexml(open(classes_file_name, "w"))

        return 0

        
    def __ExecuteSummarize(self):
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
            results = base.load_results(open(results_path, "rb"))
            test_results = filter(lambda r: r.GetKind() == Result.TEST,
                                  results)
            resource_results = \
                filter(lambda r: r.GetKind() != Result.TEST, results)
        except (IOError, xml.sax.SAXException), exception:
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
                raise qm.cmdline.CommandError, \
                      qm.error("no such ID", id=str(exception))
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

        any_unexpected_outcomes = 0
        
        # Simulate the events that would have occurred during an
        # actual test run.
        stream = TextResultStream(self._stdout, format, outcomes,
                                  self.GetDatabase(), suite_ids)
        for r in test_results:
            stream.WriteResult(r)
            if r.GetOutcome() != outcomes.get(r.GetId(), Result.PASS):
                any_unexpected_outcomes = 1
        for r in resource_results:
            stream.WriteResult(r)
        stream.Summarize()

        return any_unexpected_outcomes
        

    def __ExecuteRemote(self):
        """Execute the 'remote' command."""

        database = self.GetDatabase()

        # Get the target class.  For now, we always run in serial when
        # running remotely.
        target_class = get_extension_class("serial_target.SerialTarget",
                                           'target', database)
        # Build the target.
        target = target_class(database, { "name" : "child" })

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

        return 0


    def __ExecuteRun(self):
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

        class UnexpectedOutcomesStream(ResultStream):
            """An 'UnexpectedOutcomesStream' notices unexpected results.

            An 'UnexpectedOutcomesStream' sets a flag if any unexpected
            results occur."""
            
            def __init__(self, expected_outcomes):
                """Construct an 'UnexpectedOutcomesStream'.

                'expected_outcomes' -- A map from test IDs to expected
                outcomes."""

                ResultStream.__init__(self)

                self.__expected_outcomes = expected_outcomes
                self.__any_unexpected_outcomes = 0
                

            def WriteResult(self, result):

                if (result.GetKind() == result.TEST
                    and (result.GetOutcome()
                         != self.__expected_outcomes.get(result.GetId(),
                                                         Result.PASS))):
                    self.__any_unexpected_outcomes = 1


            def AnyUnexpectedOutcomes(self):
                """Returns true if any unexpected outcomes have occurred.

                returns -- True if any unexpected outcomes have
                occurred."""

                return self.__any_unexpected_outcomes
                
        # Create ResultStreams for textual output and for generating
        # a results file.
        result_streams = []
        if format != "none":
            stream = TextResultStream(self._stdout, format, expectations,
                                      self.GetDatabase(), test_suites)
            result_streams.append(stream)

        # Handle 'result' options.
        close_result_file = 0
        if self.HasCommandOption("no-output"):
            # User specified no output.
            result_file = None
        else:
            result_file_name = self.GetCommandOption("output")
            if result_file_name is None:
                # By default, write results to a default file.
                result_file_name = "results.qmr"

            if result_file_name == "-":
                # Use standard output.
                result_file = sys.stdout
            else:
                # A named file.  Open the file in unbufferred mode so
                # that results are written out immediately.
                result_file = open(result_file_name, "wb", 0)
                close_result_file = 1
                
        if result_file is not None:
            result_streams.append(PickleResultStream(result_file))

        # Keep track of whether or not any unexpected outcomes have
        # occurred.
        unexpected_outcomes_stream = UnexpectedOutcomesStream(expectations)
        result_streams.append(unexpected_outcomes_stream)
        
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
            return unexpected_outcomes_stream.AnyUnexpectedOutcomes()
        finally:
            # Close the result file.
            if close_result_file:
                result_file.close()
                                                    

    def __ExecuteServer(self):
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

        # If a log file was requested, open it now.
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

        # If a PID file was requested, create it now.
        pid_file_path = self.GetCommandOption("pid-file")
        if pid_file_path is not None:
            # If a PID file was requested, but no explicit path was
            # given, use a default value.
            if not pid_file_path:
                pid_file_path = qm.common.rc.Get("pid-file",
                                                 "/var/run/qmtest.pid",
                                                 "qmtest")
            try:
                pid_file = open(pid_file_path, "w")
            except IOError, e:
                raise qm.cmdline.CommandError, str(e)
        else:
            pid_file = None
            
        # Figure out which targets to use.
        targets = self.GetTargets()
        # Compute the context in which the tests will be run.
        context = self.MakeContext()

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
        sys.stderr.write(message + "\n")

        # Become a daemon, if appropriate.
        if self.GetCommandOption("daemon") is not None:
            # Fork twice.
            if os.fork() != 0:
                os._exit(0)
            if os.fork() != 0:
                os._exit(0)
            # This process is now the grandchild of the original
            # process.

        # Write out the PID file.  The correct PID is not known until
        # after the transformation to a daemon has taken place.
        try:
            if pid_file:
                pid_file.write(str(os.getpid()))
                pid_file.close()
                
            # Accept requests.
            try:
                server.Run()
            except qm.platform.SignalException, se:
                if se.GetSignalNumber() == signal.SIGTERM:
                    # If we receive SIGTERM, shut down.
                    pass
                else:
                    # Other signals propagate outwards.
                    raise
        finally:
            if pid_file:
                os.remove(pid_file_path)
                
        return 0


    def __WriteCommandHelp(self, command):
        """Write out help information about 'command'.

        'command' -- The name of the command for which help information
        is required."""

        self._stderr.write(self.__parser.GetCommandHelp(command))
        

    def __GetExpectedOutcomes(self):
        """Return the expected outcomes for this test run.

        returns -- A map from test names to outcomes corresponding to
        the expected outcome files provided on the command line.  If no
        expected outcome files are provided, an empty map is
        returned."""

        outcomes_file_name = self.GetCommandOption("outcomes")
        if not outcomes_file_name:
            return {}

        try:
            return base.load_outcomes(open(outcomes_file_name, "rb"))
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
            outcomes = base.load_outcomes(open(rerun_file_name, "rb"))
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

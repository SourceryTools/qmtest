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

    db_path_option_spec = (
        "D",
        "db-path",
        "PATH",
        "Path to the test database."
        )

    global_options_spec = [
        help_option_spec,
        db_path_option_spec,
        ]

    commands_spec = [
        ("run",
         "Run one or more tests.",
         "ID ...",
         "This command runs tests, prints their outcomes, and writes "
         "test results.  Specify one or more test IDs and "
         "suite IDs as arguments.",
         ( help_option_spec, )
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
                                                 self.commands_spec)
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


    def __ExecuteRun(self, output):
        """Execute a 'run' command."""
        
        database = self.GetDatabase()
        # Make sure some arguments were specified.  The arguments are
        # the IDs of tests and suites to run.
        if len(self.__arguments) == 0:
            raise CommandError, qm.error("no ids specified")
        try:
            test_ids = []
            base.expand_and_validate_ids(database,
                                         self.__arguments,
                                         test_ids)

            engine = base.Engine(database)
            context = base.Context()
            results = engine.RunTests(test_ids, context)

            self.__WriteOutcomes(test_ids, results, output)
        except:
            raise
                                                    

    def __WriteOutcomes(self, test_ids, results, output):
        # Find the width of the longest test ID.
        width = apply(max, (map(len, test_ids), ))
        # Throttle it.
        width = min(60, width + 1)
        # Generate a format string for printing test outcomes.
        format = "%%-%ds: %%s\n" % width

        for test_id in test_ids:
            result = results[test_id]
            output.write(format % (test_id, result.GetOutcome()))



########################################################################
# functions
########################################################################

# Place function definitions here.

########################################################################
# script
########################################################################

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   command.py
# Author: Alex Samuel
# Date:   2001-03-24
#
# Contents:
#   Test classes for testing command-line programs.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import cPickle
import errno
import os
import qm.common
import qm.executable
import qm.fields
import qm.test.base
from   qm.test.test import Test
from   qm.test.result import Result
import string
import sys
import types

########################################################################
# Classes
########################################################################

class ExecTestBase(Test):
    """Check a program's output and exit code.

    An 'ExecTestBase' runs a program and compares its standard output,
    standard error, and exit code with expected values.  The program
    may be provided with command-line arguments and/or standard
    input.

    The test passes if the standard output, standard error, and
    exit code are identical to the expected values."""

    arguments = [
        qm.fields.TextField(
            name="stdin",
            title="Standard Input",
            verbatim="true",
            multiline="true",
            description="""The contents of the standard input stream.

            If this field is left blank, the standard input stream will
            contain no data."""
            ),

        qm.fields.SetField(qm.fields.TextField(
            name="environment",
            title="Environment",
            description="""Additional environment variables.

            By default, QMTest runs tests with the same environment that
            QMTest is running in.  If you run tests in parallel, or
            using a remote machine, the environment variables available
            will be dependent on the context in which the remote test
            is executing.

            You may add variables to the environment.  Each entry must
            be of the form 'VAR=VAL'.  The program will be run in an
            environment where the environment variable 'VAR' has the
            value 'VAL'.  If 'VAR' already had a value in the
            environment, it will be replaced with 'VAL'.

            In addition, QMTest automatically adds an environment
            variable corresponding to each context property.  The name
            of the environment variable is the name of the context
            property, prefixed with 'QMV_'.  For example, if the value
            of the context property named 'target' is available in the
            environment variable 'QMV_target'.""" )),
        
        qm.fields.IntegerField(
            name="exit_code",
            title="Exit Code",
            description="""The expected exit code.

            Most programs use a zero exit code to indicate success and a
            non-zero exit code to indicate failure.  Under Windows,
            QMTest does not accurately report the exit code of the
            program; all programs are treated as if they exited with
            code zero."""
            ),

        qm.fields.TextField(
            name="stdout",
            title="Standard Output",
            verbatim="true",
            multiline="true",
            description="""The expected contents of the standard output stream.

            If the output written by the program does not match this
            value, the test will fail."""
            ),
        
        qm.fields.TextField(
            name="stderr",
            title="Standard Error",
            verbatim="true",
            multiline="true",
            description="""The expected contents of the standard error stream.

            If the output written by the program does not match this
            value, the test will fail."""
            ),

        qm.fields.IntegerField(
            name="timeout",
            title="Timeout",
            description="""The number of seconds the child program will run.

            If this field is non-negative, it indicates the number of
            seconds the child program will be permitted to run.  If this
            field is not present, or negative, the child program will be
            permitted to run for ever.""",
            default_value = -1,
            ),
        ]


    def MakeEnvironment(self, context):
        """Construct the environment for executing the target program."""

        # Start with any environment variables that are already present
        # in the environment.
        environment = os.environ.copy()
        # Copy context variables into the environment.
        for key, value in context.items():
            if "." not in key and type(value) == types.StringType:
                name = "QMV_" + key
                environment[name] = value
        # Extract additional environment variable assignments from the
        # 'Environment' field.
        for assignment in self.environment:
            if "=" in assignment:
                # Break the assignment at the first equals sign.
                variable, value = string.split(assignment, "=", 1)
                environment[variable] = value
            else:
                raise ValueError, \
                      qm.error("invalid environment assignment",
                               assignment=assignment)
        return environment


    def RunProgram(self, program, arguments, context, result):
        """Run the 'program'.

        'program' -- The path to the program to run.

        'arguments' -- A list of the arguments to the program.  This
        list must contain a first argument corresponding to 'argv[0]'.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Construct the environment.
        environment = self.MakeEnvironment(context)
        # Create the executable.
        e = qm.executable.Filter(self.stdin, self.timeout)
        # Run it.
        exit_status = e.Run(arguments, environment, path = program)

        # If the process terminated normally, check the outputs.
        if sys.platform == "win32" or os.WIFEXITED(exit_status):
            # There are no causes of failure yet.
            causes = []
            # The target program terminated normally.  Extract the
            # exit code, if this test checks it.
            if self.exit_code is None:
                exit_code = None
            elif sys.platform == "win32":
                exit_code = 0
            else:
                exit_code = os.WEXITSTATUS(exit_status)
            # Get the output generated by the program.
            stdout = e.stdout
            stderr = e.stderr
            # Check to see if the exit code matches.
            if exit_code != self.exit_code:
                causes.append("exit_code")
                result["ExecTest.expected_exit_code"] \
                    = str(self.exit_code)
                result["ExecTest.exit_code"] = str(exit_code)
            # Check to see if the standard output matches.
            if stdout != self.stdout:
                causes.append("standard output")
                result["ExecTest.stdout"] = "<pre>" + stdout + "</pre>"
                result["ExecTest.expected_stdout"] \
                    = "<pre>" + self.stdout + "</pre>"
            # Check to see that the standard error matches.
            if stderr != self.stderr:
                causes.append("standard error")
                result["ExecTest.stderr"] = "<pre>" + stderr + "</pre>"
                result["ExecTest.expected_stderr"] \
                    = "<pre>" + self.stderr + "</pre>"
            # If anything went wrong, the test failed.
            if causes:
                result.Fail("Unexpected %s." % string.join(causes, ", ")) 
        elif os.WIFSIGNALED(exit_status):
            # The target program terminated with a signal.  Construe
            # that as a test failure.
            signal_number = str(os.WTERMSIG(exit_status))
            result.Fail("Program terminated by signal.")
            result["ExecTest.signal_number"] = signal_number
        elif os.WIFSTOPPED(exit_status):
            # The target program was stopped.  Construe that as a
            # test failure.
            signal_number = str(os.WSTOPSIG(exit_status))
            result.Fail("Program stopped by signal.")
            result["ExecTest.signal_number"] = signal_number
        else:
            # The target program terminated abnormally in some other
            # manner.  (This shouldn't normally happen...)
            result.Fail("Program did not terminate normally.")

        
    
class ExecTest(ExecTestBase):
    """Check a program's output and exit code.

    An 'ExecTest' runs a program by using the 'exec' system call."""

    arguments = [
        qm.fields.TextField(
            name="program",
            title="Program",
            not_empty_text=1,
            description="""The path to the program.

            This field indicates the path to the program.  If it is not
            an absolute path, the value of the 'PATH' environment
            variable will be used to search for the program."""
            ),
        
        qm.fields.SetField(qm.fields.TextField(
            name="arguments",
            title="Argument List",
            description="""The command-line arguments.

            If this field is left blank, the program is run without any
            arguments.

            An implicit 0th argument (the path to the program) is added
            automatically."""
            ))]

    _allow_arg_names_matching_class_vars = 1


    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Was the program not specified?
        if string.strip(self.program) == "":
            result.Fail("No program specified.")
            return

        self.RunProgram(self.program, 
			[ self.program ] + self.arguments,
                        context, result)



class ShellCommandTest(ExecTestBase):
    """Check a shell command's output and exit code.

    A 'ShellCommandTest' runs the shell and compares its standard
    output, standard error, and exit code with expected values.  The
    shell may be provided with command-line arguments and/or standard
    input.

    QMTest determines which shell to use by the following method:

      - If the context contains the property
        'ShellCommandTest.command_shell', its value is split into
        an argument list and used.

      - Otherwise, if the '.qmrc' configuration file contains the common
        property 'command_shell', its value is split into an argument
        list and used.

      - Otherwise, the default shell for the target system is used.

    """

    arguments = [
        qm.fields.TextField(
            name="command",
            title="Command",
            description="""The arguments to the shell.

            This field contains the arguments that are passed to the
            shell.  It should not contain the path to the shell itself.

            If this field is left blank, the shell is run without
            arguments."""
            )
        ]

    
    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # If the context specifies a shell, use it.
        if context.has_key("ShellCommandTest.command_shell"):
            # Split the context value to build the argument list.
            shell = qm.common.split_argument_list(
                context["ShellCommandTest.command_shell"])
        else:
            # Otherwise, use a platform-specific default.
            shell = qm.platform.get_shell_for_command()
        # Append the command at the end of the argument list.
        arguments = shell + [ self.command ]
        self.RunProgram(arguments[0], arguments, context, result)



class ShellScriptTest(ExecTestBase):
    """Check a shell script's output and exit code.

    A 'ShellScriptTest' runs the shell script provided and compares its
    standard output, standard error, and exit code with expected values.
    The shell script may be provided with command-line arguments and/or
    standard input.

    QMTest determines which shell to use by the following method:

      - If the context contains the property
        'ShellScriptTest.script_shell', its value is split into an
        argument list and used.

      - Otherwise, if the '.qmrc' configuration file contains the common
        property 'script_shell', its value is split into an argument
        list and used.

      - Otherwise, the default shell for the target system is used.

    """

    arguments = [
        qm.fields.TextField(
            name="script",
            title="Script",
            description="""The contents of the shell script.

            Provide the entire shell script here.  The script will be
            written to a temporary file before it is executed.  There
            does not need to be an explicit '#! /path/to/shell' at
            the beginning of the script because QMTest will not directly
            invoke the script.  Instead, it will run the shell, passing
            it the name of the temporary file containing the script as
            an argument.""",
            verbatim="true",
            multiline="true",
            ),
        qm.fields.SetField(qm.fields.TextField(
            name="arguments",
            title="Argument List",
            description="""The command-line arguments.

            If this field is left blank, the program is run without any
            arguments.

            An implicit 0th argument (the path to the program) is added
            automatically."""
            ))        
        ]

    _allow_arg_names_matching_class_vars = 1

    
    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations."""

        # Create a temporary file for the script.
        self.__script_file_name, script_file = qm.open_temporary_file() 
        try:
            # Write the script to the temporary file.
            script_file.write(self.script)
            script_file.close()
            # If the context specifies a shell, use it.
            if context.has_key("ShellScriptTest.script_shell"):
                # Split the context value to build the argument list.
                shell = qm.common.split_argument_list(
                    context["ShellScriptTest.script_shell"])
            else:
                # Otherwise, use a platform-specific default.
                shell = qm.platform.get_shell_for_script()
            # Construct the argument list.  The argument list for the
            # interpreter is followed by the name of the script
            # temporary file, and then the arguments to the script.
            arguments = shell \
                        + [ self.__script_file_name ] \
                        + self.arguments
            self.RunProgram(arguments[0], arguments, context, result)
        finally:
            # Clean up the script file.
            os.remove(self.__script_file_name)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

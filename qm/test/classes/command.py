########################################################################
#
# File:   command.py
# Author: Alex Samuel
# Date:   2001-03-24
#
# Contents:
#   Test classes for testing command-line programs.
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

import cPickle
import errno
import os
import qm.fields
import qm.test.base
from   qm.test.base import Result
import string
import sys
import tempfile

########################################################################
# constants
########################################################################

# File descriptor numbers corresponding to standard streams.
STDIN_FILENO = sys.stdin.fileno()
STDOUT_FILENO = sys.stdout.fileno()
STDERR_FILENO = sys.stderr.fileno()

########################################################################
# classes
########################################################################

class ExecTest:
    """Check a program's output and exit code.

    An 'ExecTest' runs a program and compares its standard output,
    standard error, and exit code with expected values.  The program
    may be provided with command-line arguments and/or standard
    input.

    The test passes if the standard output, standard error, and
    exit code are identical to the expected values."""

    fields = [
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
            )),
            
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
            non-zero exit code to indicate failure."""
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
            title="Expected Standard Error",
            verbatim="true",
            multiline="true",
            description="""The expected contents of the standard error stream.

            If the output written by the program does not match this
            value, the test will fail."""
            ),
        ]


    def __init__(self,
                 program,
                 arguments=[],
                 stdin=None,
                 environment=[],
                 exit_code=None,
                 stdout=None,
                 stderr=None):
        # Just store everything away for later.
        self.program = program
        self.arguments = arguments
        self.stdin = stdin
        self.environment_list = environment
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


    def MakeEnvironment(self, context):
        """Construct the environment for executing the target program."""

        # Start with any environment variables that are already present
        # in the environment.
        environment = os.environ.copy()
        # Copy context variables into the environment.
        for key, value in context.items():
            name = "QMV_" + key
            environment[name] = value
        # Extract additional environment variable assignments from the
        # 'Environment' field.
        for assignment in self.environment_list:
            if "=" in assignment:
                # Break the assignment at the first equals sign.
                variable, value = string.split(assignment, "=", 1)
                environment[variable] = value
            else:
                raise ValueError, \
                      qm.error("invalid environment assignment",
                               assignment=assignment)
        return environment


    def Run(self, context):
        # Names of temporary files.  The file have been created iff the
        # corresponding file name variable is not 'None'.
        stdin_file_name = None
        stdout_file_name = None
        stderr_file_name = None
        result_pipe_file = None

        # Construct the environment.
        self.environment = self.MakeEnvironment(context)

        # Try block to clean up temporary files and file descriptors in
        # any eventuality.
        try:
            # Generate temporary files for standard output and error.
            stdout_file_name, stdout_fd = qm.open_temporary_file_fd()
            stderr_file_name, stderr_fd = qm.open_temporary_file_fd()
            # Write the standard input contents to a temporary file.
            stdin_file_name, stdin_fd = qm.open_temporary_file_fd()
            bytes_written = os.write(stdin_fd, self.stdin)
            assert bytes_written == len(self.stdin)
            # Rewind back to the beginning of the file.
            os.lseek(stdin_fd, 0, 0)

            # Create a pipe for communicating with the child process.
            # This pipe is used to communicate test results from the
            # child to the parent in case something goes wrong (for
            # instance, if the target program cannot be run).
            #
            # Only the parent reads from the pipe, and only the child
            # writes to the pipe.  If the child process runs the target
            # program successfully, it simply closes the pipe without
            # writing anything.  If something goes wrong, though, the
            # child process builds an appropriate test result object,
            # pickles it, writes it to the pipe, and then closes the
            # pipe and exits.
            result_pipe_read, result_pipe_write = os.pipe()

            # FIXME: Use spawn under Windows.

            # Fork a new process.
            child_pid = os.fork()

            if child_pid == 0:
                # This is the child process.
                try:
                    try:
                        # Close the read end of the result pipe.
                        os.close(result_pipe_read)
                        # Redirect stdin from the standard input file.
                        os.dup2(stdin_fd, STDIN_FILENO)
                        # Redirect stdout to the standard output file.
                        os.dup2(stdout_fd, STDOUT_FILENO)
                        # Redirect stderr to the standard error file.
                        os.dup2(stderr_fd, STDERR_FILENO)
                    except:
                        # Perhaps something went wrong while setting up
                        # the standard stream files.
                        result = qm.test.base.make_result_for_exception(
                            sys.exc_info(),
                            cause="Exception setting up test.")
                    else:
                        # Run the target program.  If the target executes
                        # successfully, this call does not return.
                        result = self.RunProgram(context)
                    # If the call returned, it handed back an error
                    # result.  Pass it to our parent process by pickling
                    # it and sending it down the pipe.
                    result_pickle = cPickle.dumps(result)
                    os.write(result_pipe_write, result_pickle)
                    os.close(result_pipe_write)
                except:
                    # It would be bad if we let an exception get out of
                    # the child process.  For one thing, the program's
                    # output would be extremely confusing.  So, write to
                    # the stderr file.
                    sys.stderr.write(qm.format_exception(sys.exc_info()))

                # End this process immediately.  Don't do any Python
                # cleanup.
                os._exit(1)

            # This is the parent process.

            # Only the child process writes to the result pipe; we don't.
            os.close(result_pipe_write)
            # We don't need the standard input file any longer.
            os.close(stdin_fd)
            # Wait for the child process to complete.
            pid, exit_status = os.waitpid(child_pid, 0)
            assert pid == child_pid
            # Try to read a pickled result from the result pipe.  If the
            # child process didn't write one, we'll read zero bytes.
            result_pipe_file = os.fdopen(result_pipe_read, "r")
            result_pickle = result_pipe_file.read()
            # Did we get back something (that should be a pickle)?
            if len(result_pickle) > 0:
                # Yes; unpickle it.
                result = cPickle.loads(result_pickle)
            # Otherwise no: the child ran the target program successfully.

            elif os.WIFEXITED(exit_status):
                # The target program terminated normally.  Extract the
                # exit code, if this test checks it.
                if self.exit_code is None:
                    exit_code = None
                else:
                    exit_code = os.WEXITSTATUS(exit_status)
                # Read the standard output generated by the program.
                os.lseek(stdout_fd, 0, 0)
                stdout_file = os.fdopen(stdout_fd, "r+b")
                stdout = stdout_file.read()
                expected_stdout = self.stdout
                # Read the standard error generated by the program.
                os.lseek(stderr_fd, 0, 0)
                stderr_file = os.fdopen(stderr_fd, "r+b")
                stderr = stderr_file.read()
                expected_stderr = self.stderr
                # Do the target program's outputs match expectations?
                if exit_code == self.exit_code \
                   and stdout == expected_stdout \
                   and stderr == expected_stderr: 
                    # Yes -- that's a pass.
                    result = Result(Result.PASS)
                else:
                    # No.  The test has failed.  Construct a failing
                    # result, including the outputs that didn't match
                    # expectations. 
                    result = Result(Result.FAIL)
                    causes = []
                    if exit_code != self.exit_code:
                        causes.append("exit code")
                        result["exit_code"] = str(exit_code)
                    if stdout != expected_stdout:
                        causes.append("standard output")
                        result["stdout"] = stdout
                    if stderr != expected_stderr:
                        causes.append("standard error")
                        result["stderr"] = stderr
                    result["cause"] = "Unexpected %s." \
                                      % string.join(causes, ", ") 

            elif os.WSIGNALED(exit_status):
                # The target program terminated with a signal.  Construe
                # that as a test failure.
                signal_number = str(WTERMSIG(exit_status))
                result = Result(Result.FAIL,
                                cause="Program terminated by signal.",
                                signal_number=signal_number)

            elif os.WIFSTOPPED(exit_status):
                # The target program was stopped.  Construe that as a
                # test failure.
                signal_number = str(WSTOPSIG(exit_status))
                result = Result(Result.FAIL,
                                cause="Program stopped by signal.",
                                signal_number=signal_number)

            else:
                # The target program terminated abnormally in some other
                # manner.  (This shouldn't normally happen...)
                result = Result(Result.FAIL,
                                cause="Program did not terminate normally.")

        finally:
            # Clean things up.
            if result_pipe_file is not None:
                result_pipe_file.close()
            if stdin_file_name is not None:
                os.remove(stdin_file_name)
            if stdout_file_name is not None:
                os.close(stdout_fd)
                os.remove(stdout_file_name)
            if stderr_file_name is not None:
                os.close(stderr_fd)
                os.remove(stderr_file_name)

        return result


    def RunProgram(self, context):
        """Run the target program.

        This function will not return if the target program executes
        (whether the test passes or fails).  However, if a problem
        occurs while running the target program, this function returns a
        'Result' object indicating the error."""
        
        # Was the program not specified?
        if string.strip(self.program) == "":
            return Result(Result.ERROR, cause="No program specified.")
        # Locate the program executable in the path specified in the
        # context. 
        path = context["path"]
        program = qm.find_program_in_path(self.program, path)
        # Did we find it?
        if program is None:
            # No.  That's an error.
            return Result(Result.ERROR,
                          cause="Could not locate program '%s'."
                          % self.program,
                          path=path)
        # Make sure it's an executable.
        if not qm.is_executable(program):
            return Result(Result.ERROR,
                          cause="Program '%s' is not an executable."
                          % program)

        # The name of the program is the first element of its argument
        # list. 
        arguments = [ program ] + self.arguments
        try:
            try:
                # Run it.
                os.execve(program, arguments, self.environment)
            # Handle selected failures specially.
            except os.error, os_error:
                if os_error.errno == errno.EACCES:
                    return Result("ERROR",
                                  cause="Access error running %s." % program)
                raise
        except:
            return qm.test.base.make_result_for_exception(
                sys.exc_info(), cause="Exception running program.")
        # We should never get here.
        assert 0


class ShellCommandTest(ExecTest):
    """Check a shell command's output and exit code.

    A 'CommandTest' runs the shell and compares its standard output,
    standard error, and exit code with expected values.  The shell
    may be provided with command-line arguments and/or standard
    input.

    QMTest determines which shell to use by the following method:

      - If the context contains the property 'command_shell', its value
        is split into an argument list and used.

      - Otherwise, if the '.qmrc' configuration file contains the common
        property 'command_shell', its value is split into an argument
        list and used.

      - Otherwise, the default shell for the target system is used.

    """

    fields = [
        qm.fields.TextField(
            name="command",
            title="Command",
            description="""The arguments to the shell.

            This field contains the arguments that are passed to the
            shell.  It should contain the path to the shell itself.

            If this field is left blank, the shell is run without
            arguments."""
            ),

        ] + ExecTest.fields[2:]

    
    def __init__(self,
                 command,
                 stdin,
                 environment,
                 exit_code,
                 stdout,
                 stderr):
        self.command = command
        self.stdin = stdin
        self.environment_list = environment
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


    def RunProgram(self, context):
        # If the context specifies a shell, use it.
        if context.has_key("command_shell"):
            # Split the context value to build the argument list.
            shell = qm.common.split_argument_list(
                context["command_shell"])
        else:
            # Otherwise, use a platform-specific default.
            shell = qm.platform.get_shell_for_command()
        # Make sure the interpreter exists.
        if not qm.is_executable(shell[0]):
            return Result(Result.ERROR,
                          cause=qm.message("no shell executable"),
                          executable=shell_executable)
        # Append the command at the end of the argument list.
        arguments = shell + [ self.command ]
        try: 
            # Run the interpreter.
            os.execve(arguments[0], arguments, self.environment)
        except:
            return qm.test.base.make_result_for_exception(
                sys.exc_info(), cause="Exception invoking command.")
        # We should never reach here.
        assert 0



class ShellScriptTest(ExecTest):
    """Check a shell script's output and exit code.

    A 'ShellScriptTest' runs the shell script provided and compares its
    standard output, standard error, and exit code with expected values.
    The shell script may be provided with command-line arguments and/or
    standard input.

    QMTest determines which shell to use by the following method:

      - If the context contains the property 'script_shell', its value
        is split into an argument list and used.

      - Otherwise, if the '.qmrc' configuration file contains the common
        property 'script_shell', its value is split into an argument
        list and used.

      - Otherwise, the default shell for the target system is used.

    """

    fields = [
        qm.fields.TextField(
            name="script",
            title="Script",
            description="""The contents of the shell script.

            Provide the entire shell script here.  The script will be
            written to a temporary file before it is executed.  There
            does not need to be an explicit '#! /path/to/shell' at
            the beginning of the script because QMTest will not directly
            invoke the script.  Instead, it wil lrun the shell, passing
            it the name of the temporary file containing the script as
            an argument.""",
            verbatim="true",
            multiline="true",
            ),

        ] + ExecTest.fields[1:]

    def __init__(self,
                 script,
                 arguments=[],
                 stdin=None,
                 environment=[],
                 exit_code=None,
                 stdout=None,
                 stderr=None):
        self.script = script
        self.arguments = arguments
        self.stdin = stdin
        self.environment_list = environment
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


    def Run(self, context):
        # Create a temporary file for the script.
        self.__script_file_name, script_file = qm.open_temporary_file() 
        try:
            # Write the script to the temporary file.
            script_file.write(self.script)
            script_file.close()
            # Run the script.
            result = ExecTest.Run(self, context)
        finally:
            # Clean up the script file.
            os.remove(self.__script_file_name)
        return result
        

    def RunProgram(self, context):
        # If the context speciifes a shell, use it.
        if context.has_key("script_shell"):
            # Split the context value to build the argument list.
            shell = qm.common.split_argument_list(
                context["script_shell"])
        else:
            # Otherwise, use a platform-specific default.
            shell = qm.platform.get_shell_for_script()
        # Make sure the interpreter exists.
        if not qm.is_executable(shell[0]):
            return Result(Result.ERROR,
                          cause=qm.message("no shell executable"),
                          executable=shell_executable)
        # Construct the argument list.  The argument list for the
        # interpreter is followed by the name of the script
        # temporary file, and then the arguments to the script.
        arguments = shell \
                    + [ self.__script_file_name ] \
                    + self.arguments
        try: 
            # Run the script.
            os.execve(arguments[0], arguments, self.environment)
        except:
            return qm.test.base.make_result_for_exception(
                sys.exc_info(),
                cause="Exception while running script.")



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

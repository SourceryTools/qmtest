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
    """Test a program by running it and checking its output and exit code.

    An 'ExecTest' instance runs a specified program, optionally passing
    it an argument list and standard input.  The program's standard
    output, standard error, and exit code are captured, and compared
    against reference values.  The test passes if these quantities are
    identical to the expected values."""

    fields = [
        qm.fields.TextField(
            name="program",
            title="Program",
            description="The program to run."
            ),
        
        qm.fields.SetField(qm.fields.TextField(
            name="arguments",
            title="Argument List",
            description="""Elements of the program's argument list 
            (command line).  The implicit 0th element of the argument 
            list is added automatically, and should not be specified 
            here.  If omitted, the argument list is empty."""
            )),
            
        qm.fields.AttachmentField(
            name="stdin",
            title="Standard Input",
            description="Text or data to pass to the program as standard "
            "input.  If omitted, the program's standard input is empty."
            ),

        qm.fields.SetField(qm.fields.TextField(
            name="environment",
            title="Environment",
            description="""The environment when executing the target
            program.  Each element is of the form 'variable=value'.

            In addition, the following environment variables are
            defined:

              'PATH' -- The path from which executables are loaded, as
              specified by the 'path' attribute in the test context."""
            )),
        
        qm.fields.IntegerField(
            name="exit_code",
            title="Expected Exit Code",
            description="The program's expected exit code.  If omitted, "
            "the program's exit code is not checked."
            ),

        qm.fields.AttachmentField(
            name="stdout",
            title="Expected Standard Output",
            description="The expected text or data from the program's "
            "standard output stream.  If omitted, the program's standard " 
            "output is not checked."
            ),
        
        qm.fields.AttachmentField(
            name="stderr",
            title="Expected Standard Error",
            description="The expected text or data from the program's "
            "standard error stream.  If omitted, the program's standard "
            "error is not checked."
            ),
        ]


    def __init__(self,
                 program,
                 arguments=[],
                 stdin="",
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

        # Start with any environment variables that are automatically
        # defined. 
        environment = {
            "PATH": context["path"],
            }
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
                # Read the standard output generated by the program, if
                # this test checks it.
                if self.stdout is None:
                    stdout = None
                else:
                    os.lseek(stdout_fd, 0, 0)
                    stdout_file = os.fdopen(stdout_fd, "w+b")
                    stdout = stdout_file.read()
                # Read the standard error generated by the program, if
                # this test checks it.
                if self.stderr is None:
                    stderr = None
                else:
                    os.lseek(stderr_fd, 0, 0)
                    stderr_file = os.fdopen(stderr_fd, "w+b")
                    stderr = stderr_file.read()
                # Do the target program's outputs match expectations?
                if exit_code == self.exit_code \
                   and stdout == self.stdout.GetData() \
                   and stderr == self.stderr.GetData():
                    # Yes -- that's a pass.
                    result = Result(Result.PASS)
                else:
                    # No.  The test has failed.  Construct a failing
                    # result, including the outputs that didn't match
                    # expectations. 
                    result = Result(Result.FAIL)
                    causes = []
                    if exit_code != self.exit_code:
                        causes.append("Exit code.")
                        result["exit_code"] = str(exit_code)
                    if stdout != self.stdout.GetData():
                        causes.append("Stdout.")
                        result["stdout"] = stdout
                    if stderr != self.stderr.GetData():
                        causes.append("Stderr.")
                        result["stderr"] = stderr
                    result["cause"] = string.join(causes, "  ") 

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
        
        # Locate the program executable in the path specified in the
        # context. 
        path = context["path"]
        program = qm.find_program_in_path(self.program, path)
        # Did we find it?
        if program is None:
            # No.  That's an error.
            return Result(Result.ERROR,
                          cause="Could not locate program.",
                          path=path)

        # The name of the program is the first element of its argument
        # list. 
        arguments = [ program ] + self.arguments
        try:
            # Run it.
            os.execve(program, arguments, self.environment)
        except:
            return qm.test.base.make_result_for_exception(
                sys.exc_info(), cause="Exception running program.")
        # We should never get here.
        assert 0



class CommandTest(ExecTest):
    """Invoke a shell command and check its output and exit code.

    A 'CommandTest' test invokes a shell command, optionally passing it
    standard input, and checks its exit code, standard output, and
    standard error.  The test does not test any side effects of the
    script."""

    fields = [
        qm.fields.TextField(
            name="command",
            title="Command",
            description="The command to run."
            ),

        qm.fields.TextField(
            name="interpreter",
            title="Command Interpreter",
            description="The command interpreter (shell) with which to run "
            "the command.  This value may contain options and/or " 
            "arguments with which to invoke the interpreter; the command "
            "itself is placed at the end.  If omitted, the system's "
            "default command shell is used."
            )

        ] + ExecTest.fields[2:]

    
    def __init__(self,
                 command,
                 interpreter=None,
                 stdin="",
                 environment=[],
                 exit_code=None,
                 stdout=None,
                 stderr=None):
        self.__command = command
        if interpreter is not None:
            # A custom interpreter.  Break it into an argument list.
            self.__interpreter = string.split(interpreter, " ")
        else:
            # Use the default shell.
            # FIXME: Do something for Windows and other platforms here.
            self.__interpreter = [
                "/bin/bash",
                "-norc",
                "-noprofile",
                "-c",
                ]
        # Store other stuff.
        self.stdin = stdin
        self.environment_list = environment
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


    def RunProgram(self, context):
        # Append the command at the end of the argument list.
        arguments = self.__interpreter + [ self.__command ]
        try: 
            # Run the interpreter.
            os.execve(arguments[0], arguments, self.environment)
        except:
            return qm.test.base.make_result_for_exception(
                sys.exc_info(), cause="Exception invoking command.")
        # We should never reach here.
        assert 0



class ScriptTest(ExecTest):
    """Invoke a script and check its output and exit code.

    A 'ScriptTest' test runs a script (which can be a shell script or
    any other interpreted language), optionally passing it command line
    arguments and standard input.  The exit code, standard output, and
    standard error are compared to expected values, if specified."""

    fields = [
        qm.fields.AttachmentField(
            name="script",
            title="Script",
            description="The text of the script to run."
            ),

        qm.fields.TextField(
            name="interpreter",
            title="Script Interpreter",
            description="The interpreter in which to run the script. "
            "This value may contain options and/or arguments with which "
            "to invoke the interpreter; the name of a (temporary) file "
            "containing the script itself is placed at the end, followed "
            "by any arguments.  If omitted, the system's default shell "
            "is used."
            ),
        ] + ExecTest.fields[1:]

    def __init__(self,
                 script,
                 interpreter=None,
                 arguments=[],
                 stdin="",
                 environment=[],
                 exit_code=None,
                 stdout=None,
                 stderr=None):
        self.script = script
        if interpreter is not None:
            self.__interpreter = string.split(interpreter, " ")
        else:
            # Use the default shell.
            # FIXME: Do something for Windows and other platforms here.
            self.__interpreter = [
                "/bin/bash",
                "-norc",
                "-noprofile",
                ]
        # Store other stuff.
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
            script_file.write(self.script.GetData())
            script_file.close()
            # Run the script.
            result = ExecTest.Run(self, context)
        finally:
            # Clean up the script file.
            os.remove(self.__script_file_name)
        return result
        

    def RunProgram(self, context):
        # Construct the argument list.  The argument list for the
        # interpreter is followed by the name of the script
        # temporary file, and then the arguments to the script.
        arguments = self.__interpreter \
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

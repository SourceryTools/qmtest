########################################################################
#
# File:   platform_linux.py
# Author: Alex Samuel
# Date:   2001-05-13
#
# Contents:
#   Platform-specific function for Linux.
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

import common
import cPickle
import os
import posix
import qm
import select
import signal
import string
import sys
import traceback

########################################################################
# constants
########################################################################

CLOSE_STREAM = common.Empty()

########################################################################
# classes
########################################################################

class RunProgramError(RuntimeError):
    """An error while running an external program."""
    
    pass



class ProgramStoppedError(RunProgramError):
    """An external program was stopped by a signal."""

    pass



class ProgramTerminatedBySignalError(RunProgramError):
    """An external program was terminated by a signal."""

    pass



class SignalException(Exception):
    """An exception raised in response to a signal."""

    def __init__(self, signal_number):
        """Create a new signal exception.

        'signal_number' -- The signal number."""

        # Construct a text argument for the exception.
        message = "signal %d" % signal_number
        # Include the signal name, if available.
        signal_name = get_signal_name(signal_number)
        if signal_name is not None:
            message = message + " (%s)" % signal_name
        # Initialize the base class.
        RuntimeError.__init__(self, message)
        # Store the signal number.
        self.__signal_number = signal_number


    def GetSignalNumber(self):
        """Return the number of the signal that caused this exception."""

        return self.__signal_number



########################################################################
# functions
########################################################################

def find_in_path(file_name):
    """Look for a program in the execution path.

    Searches the directories in the 'PATH' environment variable for an
    executable named 'file_name'.

    returns -- The path to the executable, or 'None' if none is
    found."""

    # Get the path, and split it into directories.
    path = os.environ["PATH"]
    path = string.split(path, ":")
    # Look for the file in each directory.
    for directory in path:
        file_path = os.path.join(directory, file_name)
        if os.access(file_path, os.X_OK):
            return file_path
    # No luck.
    return None


def open_in_browser(url):
    """Open a browser window and point it at 'url'.

    The browser is run in a separate, independent process."""

    # Escape single quotes in the URL.
    url = string.replace(url, "'", r"\'")
    # Which browser to use?
    browser = common.rc.Get("browser", "netscape", "common")
    browser_executable = find_in_path(browser)
    if browser_executable is None:
        raise RuntimeError, \
              qm.error("browser error", browser_path=browser)
    # Invoke the browser.
    os.system("%s '%s' &" % (browser_executable, url))


def send_email(body,
               subject,
               recipients,
               ccs=[],
               bccs=[],
               from_address=None,
               attachments=[],
               headers={}):
    """Send an email message.

    'body' -- The message body text.

    'subject' -- The message subject.

    'recipients' -- A sequence of email addresses of message
    recipients.

    'ccs' -- A sequence of email addresses of recipients of carbon
    copies.

    'bccs' -- A sequence of email addresses of recipients of blind
    carbon copies.

    'from_address' -- The message's originating address.  If 'None',
    the system will fill in the sending user's address.

    'attachments' -- A sequence of email attachments.  Each
    attachment is a triplet of '(description, MIME type,
    attachment_data)'. 

    'headers' -- Additional RFC 822 headers in a map.  Keys are
    header names and values are corresponding header contents."""

    if len(attachments) > 0:
        # FIXME: implement this.
        raise NotImplementedError, "attachments not implemented"

    # Figure out which sendmail (or equivalent) to use.
    sendmail_path = common.rc.Get("sendmail", "/usr/lib/sendmail",
                                  "common")
    # Make sure it exists and is executable.
    if not os.access(sendmail_path, os.X_OK):
        raise RuntimeError, \
              qm.error("sendmail error",
                       sendmail_path=sendmail_path)

    # Start a sendmail process.
    addresses = map(lambda a: "'%s'" % a, recipients + ccs + bccs)
    sendmail_command = sendmail_path + " " + string.join(addresses, " ")
    sendmail = os.popen(sendmail_command, "w")

    # Construct and send the entire RFC 822 message.
    if from_address is not None:
        sendmail.write("From: %s\n" % from_address)
    sendmail.write("To: %s\n" % string.join(recipients, ", "))
    if len(ccs) > 0:
        sendmail.write("Cc: %s\n" % string.join(ccs, ", "))
    if len(bccs) > 0:
        sendmail.write("Bcc: %s\n" % string.join(bccs, ", "))
    for name, value in headers.items():
        sendmail.write("%s: %s\n" % (name, value))
    sendmail.write("Subject: %s\n" % subject)
    sendmail.write("\n")
    sendmail.write(body)

    # Finish up.
    exit_code = sendmail.close()
    if exit_code is not None:
        raise MailError, "%s returned with exit code %d" \
              % (sendmail_path, exit_code)


def get_signal_name(signal_number):
    """Return the name for signal 'signal_number'.

    returns -- The signal's name, or 'None'."""

    # A hack: look for an attribute in the 'signal' module whose
    # name starts with "SIG" and whose value is the signal number.
    for attribute_name in dir(signal):
        if len(attribute_name) > 3 \
           and attribute_name[:3] == "SIG" \
           and getattr(signal, attribute_name) == signal_number:
            return attribute_name
    # No match.
    return None


def install_signal_handler(signal_number):
    """Install a handler to translate a signal into an exception.

    The signal handler raises a 'SignalException' exception in
    response to a signal."""

    signal.signal(signal_number, _signal_handler)


def _signal_handler(signal_number, execution_frame):
    """Generic signal handler that raises an exception."""

    raise SignalException(signal_number)


def replace_program(program,
                    arguments,
                    environment=None,
                    stdin=None,
                    stdout=None,
                    stderr=None):
    """Replace the Python interpreter with another program.

    'program' -- The path to the program to run.

    'arguments' -- The argument list for the program, as a sequence of
    strings.  Conventionally, the first element is the same as the value
    of 'program'.

    'environment' -- A map specifying the environment for the program.
    If 'None' or omitted, this process's environment is used instead.

    'stdin' -- A file descriptor to use as standard input for the
    program.  If 'None' or omitted, this process's standard input stream
    is used.  If 'CLOSE_STREAM', the process's standard input stream is
    closed.

    'stdout' -- A file descriptor to use as standard output for the
    program.  If 'None' or omitted, this process's standard output
    stream is used.  If 'CLOSE_STREAM', the process's standard output
    stream is closed.

    'stderr' -- A file descriptor to use as standard error for the
    program.  If 'None' or omitted, this process's standard error stream
    is used.  If 'CLOSE_STREAM', the process's standard error stream is
    closed.

    returns -- Does not return.

    raises -- 'ValueError' if 'program' is not the path to an accessible
    executable.

    raises -- 'ProgramTerminatedBySignalError' if 'program' was
    terminated by a signal.

    raises -- 'ProgramStoppedError' if 'program' was stopped by a
    signal."""

    # Make sure 'program' is executable.  We have a race condition
    # between this check and the actual call to 'exec', but all that
    # means is we may raise the wrong exception.
    if not qm.is_executable(program):
        raise ValueError, "program %s is not executable" % program

    # First set up file descriptors.  Close or duplicate standard input,
    # if requested.
    if stdin is None:
        pass
    elif stdin is CLOSE_STREAM:
        os.close(sys.stdin.fileno())
    else:
        os.dup2(stdin, sys.stdin.fileno())
    # Close or duplicate standard output, if requested.
    if stdout is None:
        pass
    elif stdout is CLOSE_STREAM:
        os.close(sys.stdout.fileno())
    else:
        os.dup2(stdout, sys.stdout.fileno())
    # Close or duplicate standard error, if requested.
    if stderr is None:
        pass
    elif stderr is CLOSE_STREAM:
        os.close(sys.stderr.fileno())
    else:
        os.dup2(stderr, sys.stderr.fileno())

    # Run the program.
    if environment is None:
        os.execv(program, arguments)
    else:
        os.execve(program, arguments, environment)
    # 'exec' functions should not return normally.
    assert not "reachable"
    

def run_program(program,
                arguments,
                environment=None,
                stdin=None,
                stdout=None,
                stderr=None):
    """Run a program in a subprocess.

    'program' -- The path to the program to run.

    'arguments' -- The argument list for the program, as a sequence of
    strings.  Conventionally, the first element is the same as the value
    of 'program'.

    'environment' -- A map specifying the environment for the program.
    If 'None' or omitted, this process's environment is used instead.

    'stdin' -- A file descriptor to use as standard input for the
    program.  If 'None' or omitted, this process's standard input stream
    is used.  If 'CLOSE_STREAM', the process's standard input stream is
    closed.

    'stdout' -- A file descriptor to use as standard output for the
    program.  If 'None' or omitted, this process's standard output
    stream is used.  If 'CLOSE_STREAM', the process's standard output
    stream is closed.

    'stderr' -- A file descriptor to use as standard error for the
    program.  If 'None' or omitted, this process's standard error stream
    is used.  If 'CLOSE_STREAM', the process's standard error stream is
    closed.

    returns -- The exit code from running 'program'.

    raises -- 'ValueError' if 'program' is not the path to an accessible
    executable.

    raises -- 'ProgramTerminatedBySignalError' if 'program' was
    terminated by a signal.

    raises -- 'ProgramStoppedError' if 'program' was stopped by a
    signal."""

    # We need to fork a new process to run the program.  But
    # first, create a pipe through which the child process can send
    # an exception object, should one be thrown while attemptint to
    # run the program.
    pipe_read, pipe_write = os.pipe()
    # Now fork the child process.
    child_pid = os.fork()
    # Which process is this?
    if child_pid == 0:
        # This is the child process.  We only write to the pipe.
        os.close(pipe_read)
        # Actually run the program.
        try:
            replace_program(program, arguments, environment,
                            stdin, stdout, stderr)
        except:
            # Oops, something went wrong. 
            exc_info = sys.exc_info()
            type, exception, frame = exc_info
            # Execution frame objects are not pickleable, so format
            # the traceback here and glue it on to the exception, in
            # case someone's interested.
            exception.traceback = common.format_traceback(exc_info)
            # Send the exception through the pipe.
            pickle = cPickle.dumps(exception)
            os.write(pipe_write, pickle)
        # Close the pipe.
        os.close(pipe_write)
        # Violently end this process.  We don't want Python to do
        # cleanup things here.
        os._exit(1)
    else:
        # This is the parent process.  We only read from the pipe.
        os.close(pipe_write)
        # Wait for the child to exit.
        pid, exit_status = os.waitpid(child_pid, 0)
        assert pid == child_pid
        # Read whatever the child wrote in the pipe.
        pickle = os.fdopen(pipe_read, "r").read()
        # Did the child write an exception to the pipe?
        if len(pickle) > 0:
            # Yes.  Extract and raise it.
            exception = cPickle.loads(pickle)
            raise exception
        # How did the child terminate?
        if os.WIFEXITED(exit_status):
            # Normally.  Return its exit code.
            return os.WEXITSTATUS(exit_status)
        elif os.WIFSIGNALED(exit_status):
            # By a signal.  Raise an exception.
            raise ProgramTerminatedBySignalError, \
                  os.WTERMSIG(exit_status)
        elif os.WIFSTOPPED(exit_status):
            # Stopped by a signal.  Raise an exception
            raise ProgramStoppedError, os.WSTOPSIG(exit_status)
        else:
            # Don't know what happened here.
            raise RuntimeError, "unknown exit status"


def run_program_captured(program,
                         arguments,
                         environment=None,
                         stdin=""):
    """Execute 'program', capturing standard output and error.

    'arguments' -- The argument list for the program, as a sequence of
    strings.  Conventionally, the first element is the same as the value
    of 'program'.

    'environment' -- A map specifying the environment for the program.
    If 'None' or omitted, this process's environment is used instead.

    'stdin' -- The text to pass to this program on standard input.

    returns -- A triplet '(exit_code, stdout, stderr)'.  The first is
    the program's exit code; the other two are strings containing the
    data that the program wrote to standard output and error,
    respectively."""

    stdin_fd = -1
    stdout_fd = -1
    stderr_fd = -1

    try:
        if stdin == "":
            # No standard input; don't bother writing an empty temporary
            # file. 
            stdin_fd = os.open("/dev/null", os.O_RDONLY)
        else:
            # Write a temporary file containing the standard input text.
            stdin_path, stdin_fd = common.open_temporary_file_fd()
            os.unlink(stdin_path)
            os.write(stdin_fd, stdin)
            # Rewrind back to the start of it.
            os.lseek(stdin_fd, 0, 0)
        # Open a temporary file to catch standard output.
        stdout_path, stdout_fd = common.open_temporary_file_fd()
        os.unlink(stdout_path)
        # Open a temporary file to catch standard error.
        stderr_path, stderr_fd = common.open_temporary_file_fd()
        os.unlink(stderr_path)

        # Run the program.
        exit_code = run_program(program, arguments, environment,
                                stdin=stdin_fd,
                                stdout=stdout_fd,
                                stderr=stderr_fd)

        # Rewind to the beginning of the standard output file, and read
        # in what the program wrote.
        os.lseek(stdout_fd, 0, 0)
        stdout_file = os.fdopen(stdout_fd, "r")
        stdout = stdout_file.read()
        # Rewind to the beginning of the standard error file, and read
        # in what the program wrote.
        os.lseek(stderr_fd, 0, 0)
        stderr_file = os.fdopen(stderr_fd, "r")
        stderr = stderr_file.read()

        # All done.
        return exit_code, stdout, stderr

    finally:
        # Close any files that were opened.
        if stdin_fd != -1:
            os.close(stdin_fd)
        if stdout_fd != -1:
            os.close(stdout_fd)
        if stderr_fd != -1:
            os.close(stderr_fd)


def get_temp_directory():
    """Return the full path to a directory for storing temporary files."""

    return "/var/tmp"


def get_user_name():
    """Return the name user running the current program."""

    # FIXME: Security.
    return os.environ["USER"]


def get_host_name():
    """Return the name of this computer."""

    return posix.uname()[1]


########################################################################
# initialization
########################################################################

def _initialize():
    """Perform module initialization."""

    # Install signal handlers for several common signals.
    map(install_signal_handler,
        [
        signal.SIGALRM,
        signal.SIGHUP,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
        ])
        

_initialize()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

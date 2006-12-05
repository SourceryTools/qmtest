########################################################################
#
# File:   executable.py
# Author: Mark Mitchell
# Date:   11/14/2002
#
# Contents:
#   Executable, RedirectedExecutable
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

import os
import qm.common
import signal
import string
import sys
import time

# The classes in this module are implemented differently depending on
# the operating system in use.
if sys.platform == "win32":
    import msvcrt
    import pywintypes
    from   threading import *
    import win32api
    import win32con
    import win32event
    import win32file
    import win32pipe
    import win32process
else:
    import cPickle
    import fcntl
    import select
    import qm.sigmask
    
########################################################################
# Classes
#######################################################################

class Executable(object):
    """An 'Executable' is a program that the operating system can run.

    'Exectuable' (and classes derived from it) create child processes.
    The 'Spawn' function creates child processes that execute
    asynchronously.  The 'Run' function creates child processes that
    execute synchrounously, i.e,. the 'Run' function does not return
    until the child process has completed its execution.

    It is safe to reuse a particular 'Executable' instance (by calling
    'Spawn' or 'Run' more than once), so long as the uses are not
    interleaved."""

    def Spawn(self, arguments=[], environment = None, dir = None,
              path = None, exception_pipe = None):
        """Spawn the program.

        'arguments' -- The sequence of arguments that should be passed
        to the executable.  The first argument provided in this
        sequence will be 'argv[0]'; that is also the value used for
        the path to the executable.

        'environment' -- If not 'None', a dictionary giving the
        environment that should be provided to the child.

        'dir' -- If not 'None', the directory in which the child
        should begin execution.  If 'None', the child will execute in
        the same directory as the parent.

        'path' -- If not 'None', the path to the program to run.  If
        'None', 'arguments[0]' is used.

        'exception_pipe' -- If not 'None', a pipe that the child can
        use to communicate an exception to the parent.  This pipe is
        only used on UNIX systems.  The write end of the pipe will be
        closed by this function.

        returns -- The PID of the child.

        Before creating the child, the parent will call
        'self._InitializeParent'.  On UNIX systems, the child will
        call 'self._InitializeChild' after 'fork', but before 'exec'.
        On non-UNIX systems, 'self._InitializeChild' will never be
        called.

        After creating the child, 'self._HandleChild' is called in the
        parent.  This hook should be used to handle tasks that must be
        performed after the child is running.

        If the path to the program is absolute, or contains no
        separator characters, it is not modified.  Otherwise the path
        to the program is relative, it is transformed into an absolute
        path using 'dir' as the base, or the current directory if
        'dir' is not set."""

        # Remember the directory in which the execution will occur.
        self.__dir = dir

        # The path to the executable is the first argument, if not
        # explicitly specified.
        if not path:
            path = arguments[0]

        # Normalize the path name.  At the conclusion of this
        # processing, the path is either an absolute path, or contains
        # no directory seperators.
        if os.path.isabs(path):
            # An absolute path.
            pass
        elif (os.sep in path or (os.altsep and os.altsep in path)):
            # A relative path name, like "./program".
            if dir:
                path = os.path.normpath(os.path.join(dir, path))
                if not os.path.isabs(path):
                    path = os.path.abspath(path)
            else:
                path = os.path.abspath(path)
        else:
            # A path with no directory separators.  The program to
            # execute will be found by searching the PATH environment
            # variable.
            pass

        # Initialize the parent.
        startupinfo = self._InitializeParent()

        # Initialize self.__child so that if "fork" or "CreateProcess"
        # throws an exception our caller can tell that there is no
        # child process to kill.
        self.__child = None
        
        if sys.platform == "win32":
            # Compute the command line.  The Windows API uses a single
            # string as the command line, rather than an array of
            # arguments.
            command_line = self.__CreateCommandLine(arguments)

            # If the path is not absolute, then we need to search the
            # PATH.  Since CreateProcess only searches the PATH if its
            # first argument is None, we clear path here.
            if not os.path.isabs(path):
                path = None
            
            # Windows supports wide-characters in the environment, but
            # the Win32 extensions to Python require that all of the
            # entries in the environment be of the same type,
            # i.e,. that either all of them be of type StringType or
            # of type UnicodeType.  Therefore, if we find any elements
            # that are Unicode strings, convert all of them to Unicode
            # strings.
            if environment is not None:
                # See if there any Unicode strings in the environment.
                uses_unicode = 0
                for (k, v) in environment.iteritems():
                    if (isinstance(k, unicode)
                        or isinstance(v, unicode)):
                        uses_unicode = 1
                        break
                # If there are Unicode strings in the environment,
                # convert all of the key-value pairs to Unicode.
                if uses_unicode:
                    new_environment = {}
                    for (k, v) in environment.iteritems():
                        new_environment[unicode(k)] = unicode(v)
                    environment = new_environment
                        
            # Create the child process.
            self.__child \
                = win32process.CreateProcess(path,
                                             command_line,
                                             None,
                                             None,
                                             1,
                                             0,
                                             environment,
                                             self.__dir,
                                             startupinfo)[0]
        else:
            # Fork.
            self.__child = os.fork()

            if self.__child == 0:
                try:
                    # Close the read end of the pipe.
                    if exception_pipe:
                        os.close(exception_pipe[0])
                    # Initialize the child.
                    self._InitializeChild()
                    # Exec the program.
                    if environment:
                        os.execvpe(path, arguments, environment)
                    else:
                        os.execvp(path, arguments)
                except:
                    if exception_pipe:
                        # Get the exception information.
                        exc_info = sys.exc_info()
                        # Write it to the pipe.  The traceback object
                        # cannot be pickled, unfortunately, so we
                        # cannot communicate that information.
                        cPickle.dump(exc_info[:2],
                                     os.fdopen(exception_pipe[1], "w"),
                                     1)
                    # Exit without running cleanups.
                    os._exit(1)

                # This code should never be reached.
                assert None

        # Nothing will be written to the exception pipe in the parent.
        if exception_pipe:
            os.close(exception_pipe[1])
            
        # Let the parent take any actions required after creating the
        # child.
        self._HandleChild()
        
        return self.__child


    def Run(self, arguments=[], environment = None, dir = None,
            path = None):
        """Spawn the program and wait for it to finish.

        'arguments' -- The sequence of arguments that should be passed
        to the executable.  The first argument provided in this
        sequence will be 'argv[0]'.

        'environment' -- If not 'None', a dictionary giving the
        environment that should be provided to the child.  If 'None',
        the child will inherit the parents environment.

        'dir' -- If not 'None', the directory in which the child
        should begin execution.  If 'None', the child will execute in
        the same directory as the parent.

        'path' -- If not 'None', the path to the program to run.  If
        'None', 'arguments[0]' is used.

        returns -- The status returned by the program.  Under UNIX,
        this is the value returned by 'waitpid'; under Windows, it is
        the value returned by 'GetExitCodeProcess'.

        After invoking 'Spawn', this function invokes '_DoParent' to
        allow the parent process to perform whatever actions are
        required.  After that function returns, the parent waits for
        the child process to exit."""

        # If fork succeeds, but the exec fails, we want information
        # about *why* it failed.  The exit code from the subprocess is
        # not nearly as illuminating as the exception raised by exec.
        # Therefore, we create a pipe between the parent and child;
        # the child writes the exception into the pipe to communicate
        # it to the parent.
        if sys.platform != "win32":
            exception_pipe = os.pipe()
            # Mark the write end as close-on-exec so that the file
            # descriptor is not passed on to the child.
            qm.common.close_file_on_exec(exception_pipe[1])
        else:
            exception_pipe = None

        # Start the program.
        child = self.Spawn(arguments, environment, dir, path, exception_pipe)

        # Give the parent a chance to do whatever it needs to do.
        self._DoParent()
        
        # Wait for the child to exit.
        if sys.platform == "win32":
            win32event.WaitForSingleObject(child, win32event.INFINITE)
            # Get its exit code.
            return win32process.GetExitCodeProcess(child)
        else:
            status = os.waitpid(child, 0)[1]
            # See if an exception was pushed back up the pipe.
            data = os.fdopen(exception_pipe[0]).read()
            # If any data was read, then it is data corresponding to
            # the exception thrown by exec.
            if data:
                # Unpickle the data.
                exc_info = cPickle.loads(data)
                # And raise it here.
                raise exc_info[0], exc_info[1]

            return status

        
    def _InitializeParent(self):
        """Initialize the parent process.

        Before spawning the child, this method is invoked to give the
        parent a chance to initialize itself.

        returns -- Under Windows, a 'PySTARTUPINFO' structure
        explaining how the child should be initialized.  On other
        systems, the return value is ignored."""

        if sys.platform == "win32":
            return win32process.STARTUPINFO()


    def Kill(self):
        """Kill the child process.

        The child process is killed in a way that does not permit an
        orderly shutdown.  In other words, 'SIGKILL' is used under
        UNIX, not 'SIGTERM'.  On Windows, 'TerminateProcess' is used,
        and the exit code from the child process will be '1'."""
        
        if sys.platform == "win32":
            win32process.TerminateProcess(self._GetChildPID(), 1)
        else:
            os.kill(self._GetChildPID(), signal.SIGKILL)

                
    def _HandleChild(self):
        """Run in the parent process after the child has been created.

        The child process has been spawned; its PID is avialable via
        '_GetChildPID'.  Take any actions in the parent that are
        required now that the child exists.

        Derived class versions must call this method."""

        pass
    
        
    def _InitializeChild(self):
        """Initialize the child process.

        After 'fork' is called this method is invoked to give the
        child a chance to initialize itself.  '_InitializeParent' will
        already have been called in the parent process.

        This method is not used under Windows."""

        assert sys.platform != "win32"

        # The way Python's threading support works, every thread except
        # the main thread always has all signals blocked.  This is fine
        # for the threads themselves, but it causes problems if we
        # 'fork' from a child thread; the new process starts with all
        # signals blocked, which is probably not what you want!
        # Arguably this is a bug in Python, but for the meantime, work
        # around this by setting the new process's signal mask to match
        # the signal mask that QMTest was started with.
        qm.sigmask.restore_mask()

        if self.__dir:
            os.chdir(self.__dir)


    def _DoParent(self):
        """Perform actions required in the parent after 'Spawn'."""

        pass
    

    def _GetChildPID(self):
        """Return the process ID for the child process.

        returns -- The process ID for the child process.  (On Windows,
        the value returned is the process handle.)  Returns 'None' if
        the child has not yet been created, or if something went awry
        when creating it.  For example, if 'os.fork' throws an
        exception, this value will return 'None'."""

        return self.__child
    
        
    def __CreateCommandLine(self, arguments):
        """Return a string giving the process command line.

        arguments -- A sequence of arguments (including argv[0])
        indicating the command to be run.
        
        returns -- A string that could be provided to the shell in
        order to run the command."""

        command = ""
        need_space = 0
        for a in arguments:
            # Add a space between arguments.
            if need_space:
                command += " "
            else:
                need_space = 1
            # If the argument contains whitespace characters, enclose
            # it in quotes.  Similarly, an empty argument must be
            # enclosed in quotes.
            if not a:
                command += '""'
                continue
            whitespace = 0
            for c in string.whitespace:
                if c in a:
                    whitespace = 1
                    break
            if whitespace:
                command += '"' + a + '"'
            else:
                command += a

        return command



class TimeoutExecutable(Executable):
    """A 'TimeoutExecutable' runs for a limited time.

    If the timer expires, the child process is killed and
    self.timedout is set to 1.  Otherwise, self.timedout is set to 0.

    In order to implement this functionality under UNIX, the child
    process is placed into its own process group.  An additional
    monitoring process is created whose sole job is to kill the
    primary child's process group if the timeout expires.  Process
    groups are used so that if the child process spawns additional
    processes they are killed too.  A separate monitoring process is
    used so as not to block the parent.

    Under Windows, a monitoring thread is created.  When the timer
    expires, the child process is terminated.  However, the child
    process is not placed into a separate process group, so
    granchildren kare not terminated.  In the future, when Python
    provides access to 'CreateJobObject' and related functions, jobs
    will be used to provide functionality similar to UNIX process
    groups.
    
    The 'Run' method will automatically start the monitoring process.
    The 'Spawn' method does not start the monitoring process.  User's
    of 'Spawn' should invoke '_DoParent' in order to start the
    monitoring process.  Derived class '_DoParent' functions should
    call the version defined in this class."""

    def __init__(self, timeout = -1):
        """Construct a new 'TimeoutExecutable'.

        'timeout' -- The number of seconds that the child is permitted
        to run.  This value may be a floating-point value.  However,
        the value may be rounded to an integral value on some systems.
        Once the timeout expires, the child and its entire process
        group is killed.  (The processes in the process group are sent
        the 'SIGKILL' signal.)  If the 'timeout' is -2, the child is
        allowed to run forever, but when it terminates the child's
        process group is killed.
        
        If the 'timeout' is -1, this class behaves exactly like
        'Executable'."""

        super(TimeoutExecutable, self).__init__()
        self.__timeout = float(timeout)
        

    def _InitializeChild(self):

        # Put the child into its own process group.  This step is
        # performed in both the parent and the child; therefore both
        # processes can safely assume that the creation of the process
        # group has taken place.
        if self.__UseSeparateProcessGroupForChild():
            os.setpgid(0, 0)

        super(TimeoutExecutable, self)._InitializeChild()


    def _HandleChild(self):

        super(TimeoutExecutable, self)._HandleChild()
        
        if self.__UseSeparateProcessGroupForChild():
            # Put the child into its own process group.  This step is
            # performed in both the parent and the child; therefore both
            # processes can safely assume that the creation of the process
            # group has taken place.
            child_pid = self._GetChildPID()
            try:
                os.setpgid(child_pid, child_pid)
            except:
                # The call to setpgid may fail if the child has exited,
                # or has already called 'exec'.  In that case, we are
                # guaranteed that the child has already put itself in the
                # desired process group.
                pass

            # Create the monitoring process.
            #
            # If the monitoring process is in parent's process group and
            # kills the child after waitpid has returned in the parent, we
            # may end up trying to kill a process group other than the one
            # that we intend to kill.  Therefore, we put the monitoring
            # process in the same process group as the child; that ensures
            # that the process group will persist until the monitoring
            # process kills it.
            self.__monitor_pid = os.fork()
            if self.__monitor_pid != 0:
                # Make sure that the monitoring process is placed into the
                # child's process group before the parent process calls
                # 'waitpid'.  In this way, we are guaranteed that the process
                # group as the child 
                os.setpgid(self.__monitor_pid, child_pid)
            else:
                # Put the monitoring process into the child's process
                # group.  We know the process group still exists at
                # this point because either (a) we are in the process
                # group, or (b) the parent has not yet called waitpid.
                os.setpgid(0, child_pid)

                # Close all open file descriptors.  They are not needed
                # in the monitor process.  Furthermore, when the parent
                # closes the write end of the stdin pipe to the child,
                # we do not want the pipe to remain open; leaving the
                # pipe open in the monitor process might cause the child
                # to block waiting for additional input.
                try:
                    max_fds = os.sysconf("SC_OPEN_MAX")
                except:
                    max_fds = 256
                for fd in xrange(max_fds):
                    try:
                        os.close(fd)
                    except:
                        pass

                try:
                    if self.__timeout >= 0:
                        # Give the child time to run.
                        time.sleep (self.__timeout)
                        # Kill all processes in the child process group.
                        os.kill(0, signal.SIGKILL)
                    else:
                        # This call to select will never terminate.
                        select.select ([], [], [])
                finally:
                    # Exit.  This code is in a finally clause so that
                    # we are guaranteed to get here no matter what.
                    os._exit(0)
        elif self.__timeout >= 0 and sys.platform == "win32":
            # Create a monitoring thread.
            self.__monitor_thread = Thread(target = self.__Monitor)
            self.__monitor_thread.start()


    def Run(self, arguments=[], environment = None, dir = None,
            path = None):

        if self.__UseSeparateProcessGroupForChild():
            self.__monitor_pid = None
        elif self.__timeout >= 0 and sys.platform == "win32":
            self.__monitor_thread = None
            
        # Run the process.
        try:
            status = super(TimeoutExecutable, self).Run(arguments,
                                                        environment,
                                                        dir,
                                                        path)
        finally:
            if self.__UseSeparateProcessGroupForChild():
                # Clean up the monitoring program; it is no longer needed.
                child_pid = self._GetChildPID()
                if child_pid is not None:
                    os.kill(-child_pid, signal.SIGKILL)
                if self.__monitor_pid is not None:
                    os.waitpid(self.__monitor_pid, 0)
            elif self.__timeout >= 0 and sys.platform == "win32":
                # Join the monitoring thread.
                if self.__monitor_thread is not None:
                    self.__monitor_thread.join()
                
        return status


    def __UseSeparateProcessGroupForChild(self):
        """Returns true if the child wil be placed in its own process group.

        returns -- True if the child will be placed in its own process
        group.  In that case, a separate monitoring process will also
        be created."""

        if sys.platform == "win32":
            # In Windows 2000 (or later), we should use "jobs" by
            # analogy with UNIX process groups.  However, that
            # functionality is not (yet) provided by the Python Win32
            # extensions.
            return 0
        
        return self.__timeout >= 0 or self.__timeout == -2


    if sys.platform == "win32":

        def __Monitor(self):
            """Kill the child if the timeout expires.

            This function is run in the monitoring thread."""
        
            # The timeout may be expressed as a floating-point value
            # on UNIX, but it must be an integer number of
            # milliseconds when passed to WaitForSingleObject.
            timeout = int(self.__timeout * 1000)
            # Wait for the child process to terminate or for the
            # timer to expire.
            result = win32event.WaitForSingleObject(self._GetChildPID(),
                                                    timeout)
            # If the timeout occurred, kill the child process.
            if result == win32con.WAIT_TIMEOUT:
                self.Kill()
            


class RedirectedExecutable(TimeoutExecutable):
    """A 'RedirectedExecutable' redirects the standard I/O streams."""

    def _InitializeParent(self):

        super(RedirectedExecutable, self)._InitializeParent()
        
        # Create a pipe for each of the streams.
        self._stdin_pipe = self._StdinPipe()
        self._stdout_pipe = self._StdoutPipe()
        self._stderr_pipe = self._StderrPipe()

        # There has been no output yet.
        self.stdout = ""
        self.stderr = ""

        # Under Windows, create a startupinfo structure that explains
        # where the streams connected to the child should go.
        if sys.platform == "win32":
            # Create a startupinfo structure.
            startupinfo = win32process.STARTUPINFO()
            # Indicate that the child process should use the standard
            # handles in startupinfo.
            startupinfo.dwFlags = win32con.STARTF_USESTDHANDLES

            # Attach each of the pipes to the appropriate entries in
            # startupinfo.  Also create a non-inheritable duplicate of the
            # pipe end we will be using, and close the inheritable
            # version.
            if self._stdin_pipe:
                startupinfo.hStdInput = self._stdin_pipe[0]
                self._stdin_pipe[1] \
                    = self.__UninheritableHandle(self._stdin_pipe[1])
            else:
                startupinfo.hStdInput = win32file.INVALID_HANDLE_VALUE
            if self._stdout_pipe:
                startupinfo.hStdOutput = self._stdout_pipe[1]
                self._stdout_pipe[0] \
                    = self.__UninheritableHandle(self._stdout_pipe[0])
            else:
                startupinfo.hStdOutput = win32file.INVALID_HANDLE_VALUE
            if self._stderr_pipe:
                startupinfo.hStdError =  self._stderr_pipe[1]
                self._stderr_pipe[0] \
                    = self.__UninheritableHandle(self._stderr_pipe[0])
            elif self._stdout_pipe:
                # If there's no stderr pipe -- but there is a stdout
                # pipe -- redirect both stdout and stderr to the same
                # pipe.
                startupinfo.hStdError = self._stdout_pipe[1]
            else:
                startupinfo.hStdError = win32file.INVALID_HANDLE_VALUE

            return startupinfo
        
        
    def _InitializeChild(self):

        # Let the base class do any initialization required.
        super(RedirectedExecutable, self)._InitializeChild()
        
        # Redirect the standard I/O streams to the pipes.  Python does
        # not provide STDIN_FILENO, STDOUT_FILENO, and STDERR_FILENO,
        # so we must use the file descriptor numbers directly.
        if self._stdin_pipe:
            os.dup2(self._stdin_pipe[0], 0)
        else:
            os.close(0)
            
        if self._stdout_pipe:
            os.dup2(self._stdout_pipe[1], 1)
        else:
            os.close(1)
            
        if self._stderr_pipe:
            os.dup2(self._stderr_pipe[1], 2)
        elif self._stdout_pipe:
            # If there's no stderr pipe -- but there is a stdout
            # pipe -- redirect both stdout and stderr to the same
            # pipe.
            os.dup2(self._stdout_pipe[1], 2)
        else:
            os.close(2)

        # Close the pipe fds.  This should happen automatically when we
        # exec the new process anyway, but it is polite to close fds as
        # soon as possible.
        if self._stdin_pipe:
            os.close(self._stdin_pipe[0])
            os.close(self._stdin_pipe[1])
        if self._stdout_pipe:
            os.close(self._stdout_pipe[0])
            os.close(self._stdout_pipe[1])
        if self._stderr_pipe:
            os.close(self._stderr_pipe[0])
            os.close(self._stderr_pipe[1])


    def _HandleChild(self):

        # Close the pipe ends that we do not need.
        if self._stdin_pipe:
            self._ClosePipeEnd(self._stdin_pipe[0])
        if self._stdout_pipe:
            self._ClosePipeEnd(self._stdout_pipe[1])
        if self._stderr_pipe:
            self._ClosePipeEnd(self._stderr_pipe[1])

        # The pipes created by 'RedirectedExecutable' must be closed
        # before the monitor process (created by 'TimeoutExecutable')
        # is created.  Otherwise, if the child process dies, 'select'
        # in the parent will not return if the monitor process may
        # still have one of the file descriptors open.
        super(RedirectedExecutable, self)._HandleChild()
        
        
    def _DoParent(self):

        super(RedirectedExecutable, self)._DoParent()

        # Process the various redirected streams until none of the
        # streams remain open.
        if sys.platform != "win32":
            while 1:
                # Prepare the lists of interesting descriptors.
                read_fds = []
                write_fds = []
                if self._stdout_pipe:
                    read_fds.append(self._stdout_pipe[0])
                if self._stderr_pipe:
                    read_fds.append(self._stderr_pipe[0])
                if self._stdin_pipe:
                    write_fds.append(self._stdin_pipe[1])

                # If there are no longer any interesting descriptors, we are
                # done.
                if not read_fds and not write_fds:
                    return

                # See which descriptors are ready for processing.
                read_ready, write_ready \
                    = select.select(read_fds, write_fds, [])[:2]

                # Process them.
                if self._stdout_pipe and self._stdout_pipe[0] in read_ready:
                    self._ReadStdout()
                if self._stderr_pipe and self._stderr_pipe[0] in read_ready:
                    self._ReadStderr()
                if self._stdin_pipe and self._stdin_pipe[1] in write_ready:
                    self._WriteStdin()
        else:
            # Under Windows, neither select, nor
            # WaitForMultipleObjects, works on pipes.  The only
            # approach that is reliable under all versions of Windows
            # is to use a separate thread for each handle.  By
            # converting the pipe ends from OS handles to file
            # descriptors at this point, _ReadStdout, _ReadStderr, and
            # _WriteStdin can use the same implementations under
            # Windows that they do under UNIX.
            
            if self._stdin_pipe:
                h = self._stdin_pipe[1]
                self._stdin_pipe[1] = msvcrt.open_osfhandle(h, 0)
                h.Detach()
                stdin_thread = Thread(target = self.__CallUntilNone,
                                      args = (self._WriteStdin,
                                              "_stdin_pipe"))
            else:
                stdin_thread = None
                
            if self._stdout_pipe:
                h = self._stdout_pipe[0]
                self._stdout_pipe[0] = msvcrt.open_osfhandle(h, 0)
                h.Detach()
                stdout_thread = Thread(target = self.__CallUntilNone,
                                       args = (self._ReadStdout,
                                               "_stdout_pipe"))
            else:
                stdout_thread = None

            if self._stderr_pipe:
                h = self._stderr_pipe[0]
                self._stderr_pipe[0] = msvcrt.open_osfhandle(h, 0)
                h.Detach()
                stderr_thread = Thread(target = self.__CallUntilNone,
                                       args = (self._ReadStderr,
                                               "_stderr_pipe"))
            else:
                stderr_thread = None

            # Start the threads.
            for t in stdin_thread, stdout_thread, stderr_thread:
                if t:
                    t.start()
            # Wait for them to finish.
            for t in stdin_thread, stdout_thread, stderr_thread:
                if t:
                    t.join()
            
        
    def _ReadStdout(self):
        """Read from the standard output pipe."""

        # Read some data.
        data = os.read(self._stdout_pipe[0], 64 * 1024)
        
        if not data:
            # If there is no new data, end-of-file has been reached.
            os.close(self._stdout_pipe[0])
            self._stdout_pipe = None
        else:
            # Otherwise, add the data to the output we have already
            # collected.
            self.stdout += data
        

    def _ReadStderr(self):
        """Read from the standard error pipe."""

        # Read some data.
        data = os.read(self._stderr_pipe[0], 64 * 1024)

        if not data:
            # If there is no new data, end-of-file has been reached.
            os.close(self._stderr_pipe[0])
            self._stderr_pipe = None
        else:
            # Otherwise, add the data to the output we have already
            # collected.
            self.stderr += data


    def _WriteStdin(self):
        """Write to the standard input pipe.

        This implementation writes no data and closes the pipe."""

        # Close the pipe.
        os.close(self._stdin_pipe[1])
        self._stdin_pipe = None


    def _StdinPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None' if the standard input should be
        closed in the child."""

        pipe = self._CreatePipe()
        if sys.platform != "win32":
            # Make sure that writing to the pipe will never result in
            # deadlock.
            fcntl.fcntl(pipe[1], fcntl.F_SETFL,
                        fcntl.fcntl(pipe[1], fcntl.F_GETFL) | os.O_NONBLOCK)
        return pipe


    def _StdoutPipe(self):
        """Return a pipe to which to redirect the standard output.

        returns -- A pipe, or 'None' if the standard output should be
        closed in the child."""

        return self._CreatePipe()


    def _StderrPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None'.  If 'None' is returned, but
        '_StdoutPipe' returns a pipe, then the standard error and
        standard input will both be redirected to that pipe.  However,
        if '_StdoutPipe' also returns 'None', then the standard error
        will be closed in the child."""

        return self._CreatePipe()


    def _ClosePipeEnd(self, fd):
        """Close the file descriptor 'fd', which is one end of a pipe.

        'fd' -- Under UNIX, a file descriptor.  Under Windows, a
        handle."""

        if sys.platform == "win32":
            fd.Close()
        else:
            os.close(fd)


    def _CreatePipe(self):
        """Return a new pipe.

        returns -- A tuple (under UNIX) or list (under Windows)
        consisting of the file descriptors (UNIX) or handles (Windows)
        for the read end and write end of a new pipe.  The pipe is
        inheritable by child processes.  On UNIX the fds will not be
        inherited across 'exec'."""

        if sys.platform == "win32":
            # Create a security descriptor so that we can mark the handles
            # as inheritable.  (A call to os.pipe under Windows
            # returns handles that are not inheritable.)
            sa = pywintypes.SECURITY_ATTRIBUTES()
            sa.bInheritHandle = 1
            # Transform the tuple returned into a list so that the
            # individual elements can be altered.
            r, w = win32pipe.CreatePipe(sa, 0)
            return [r, w]
        else:
            pipe = os.pipe()
            for fd in pipe:
                qm.common.close_file_on_exec(fd)
            return pipe


    def __CallUntilNone(self, f, attribute):
        """Call 'f' until 'self.attribute' is 'None'.

        'f' -- A callable.

        'attribute' -- A string giving the name of an attribute."""

        while getattr(self, attribute) is not None:
            f()
            
    
    def __UninheritableHandle(self, handle):
        """Return a duplicate of a file handle that is not inheritable.

        'handle' -- A file handle.

        returns -- A new handle that is a non-inheritable duplicate of
        the 'handle'.

        This method should only be used under Windows."""

        assert sys.platform == "win32"
        
        current_process = win32api.GetCurrentProcess()
        return win32api.DuplicateHandle(current_process,
                                        handle,
                                        current_process,
                                        0,
                                        0,
                                        win32con.DUPLICATE_SAME_ACCESS)



class Filter(RedirectedExecutable):
    """A 'FilterExecutable' feeds an input string to another proces.

    The input string is provided to a child process via a pipe; the
    standard output and standard error streams from the child process
    are collected in the 'Filter'."""

    def __init__(self, input, timeout = -1):
        """Create a new 'Filter'.

        'input' -- The string containing the input to provide to the
        child process.

        'timeout' -- As for 'TimeoutExecutable.__init__'."""

        super(Filter, self).__init__(timeout)
        self.__input = input
        self.__next = 0


    def _WriteStdin(self):

        # If there's nothing more to write, stop.
        if self.__next == len(self.__input):
            super(Filter, self)._WriteStdin()
        else:            
            # Write some data.
            self.__next += os.write(self._stdin_pipe[1],
                                    self.__input[self.__next
                                                 : self.__next + 64 * 1024])


########################################################################
# Variables
#######################################################################

__all__ = ["Executable",
           "TimeoutExecutable",
           "RedirectedExecutable",
           "Filter"]
       

########################################################################
#
# File:   executable.py
# Author: Mark Mitchell
# Date:   11/14/2002
#
# Contents:
#   Executable, RedirectedExecutable
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

import os
import sys

# The classes in this module are implemented differently depending on
# the operating system in use.
if sys.platform == "win32":
    from   threading import *
    import win32api
    import win32con
    import win32event
    import win32file
    import win32pipe
    import win32process
else:
    import select
    
########################################################################
# Classes
#######################################################################

class Executable:
    """An 'Executable' is a program that the operating system can run."""

    def __init__(self):
        """Construct a new 'Executable'."""

        # This method is a placeholder.  At some point in the future,
        # we may need to do some initialization; by providing the
        # method derived classes can call Executable.__init__ and will
        # not need to be updated later.

        pass
    
        
    def Spawn(self, arguments=[], environment = None, dir = None,
              path = None):
        """Spawn the program.

        'arguments' -- The sequence of arguments that should be passed
        to the executable.  The first argument provided in this
        sequence will be 'argv[0]'; that is also the value used for
        the path to the executable.

        'environment' -- If not 'None', a dictionary giving the
        environment that should be provided to the child.

        'dir' -- If not 'None', the directory in which the child
        should begin executable.  If 'None', the child will execute in
        the same directory as the parent.

        'path' -- If not 'None', the path to the program to run.  If
        'None', 'arguments[0]' is used.

        Before creating the child, the parent will call
        'self._InitializeParent'.  On UNIX systems, the child will
        call 'self._InitializeChild' after 'fork', but before 'exec'.

        The PID of the child is available by calling 'GetChild'."""

        # Remember the directory in which the execution will occur.
        self.__dir = dir
        # The path to the executable is the first argument.
        if not path:
            path = arguments[0]
        
        # Initialize the parent.
        startupinfo = self._InitializeParent()

        if sys.platform == "win32":
            # Compute the command line.  The Windows API uses a single
            # string as the command line, rather than an array of
            # arguments.
            command_line = self.__CreateCommandLine(arguments)
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
                    # Initialize the child.
                    self._InitializeChild()
                    # Exec the program.
                    if environment:
                        os.execvpe(path, arguments, environment)
                    else:
                        os.execvp(path, arguments)
                except:
                    # Exit immediately.
                    os._exit(1)

                # This code should never be reached.
                assert None
                

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
        should begin executable.  If 'None', the child will execute in
        the same directory as the parent.

        'path' -- If not 'None', the path to the program to run.  If
        'None', 'arguments[0]' is used.

        returns -- The status returned by the program.  Under UNIX,
        this is the value returned by 'waitpid'; under Windows, it is
        the value returned by 'GetExitCodeProcess'."""

        # Spawn the program.
        self.Spawn(arguments, environment, dir, path)
        # Give the parent a chance to do whatever it needs to do.
        self._DoParent()
        # Wait for the child to exit.
        if sys.platform == "win32":
            child = self._GetChild()
            win32event.WaitForSingleObject(child, win32event.INFINITE)
            # Get its exit code.
            return win32process.GetExitCodeProcess(child)
        else:
            return os.waitpid(self.GetChild(), 0)[1]

        
    def GetChild(self):
        """Return the PID of the child process.

        returns -- The PID of the child process."""

        return self.__child
        
        
    def _InitializeParent(self):
        """Initialize the parent process.

        Before spawning the child, this method is invoked to give the
        parent a chance to initialize itself.

        returns -- Under Windows, a 'PySTARTUPINFO' structure
        explaining how the child should be initialized.  On other
        systems, the return value is ignored."""

        if sys.platform == "win32":
            return win32process.STARTUPINFO()


    def _InitializeChild(self):
        """Initialize the child process.

        After 'fork' is called this method is invoked to give the
        child a chance to initialize itself.  '_InitializeParent' will
        already have been called in the parent process.

        This method is not used under Windows."""

        assert sys.platform != "win32"
        
        if self.__dir:
            os.chdir(self.__dir)


    def _DoParent(self):
        """Perform actions required in the parent after 'Spawn'."""

        pass
    

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



class RedirectedExecutable(Executable):
    """A 'RedirectedExecutable' redirects the standard I/O streams."""

    def _InitializeParent(self):

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
        Executable._InitializeChild(self)
        
        # Close the pipe ends that we do not need.
        if self._stdin_pipe:
            os.close(self._stdin_pipe[1])
        if self._stdout_pipe:
            os.close(self._stdout_pipe[0])
        if self._stderr_pipe:
            os.close(self._stderr_pipe[0])

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


    def _DoParent(self):

        # Close the pipe ends that we do not need.
        if self._stdin_pipe:
            self._ClosePipeEnd(self._stdin_pipe[0])
        if self._stdout_pipe:
            self._ClosePipeEnd(self._stdout_pipe[1])
        if self._stderr_pipe:
            self._ClosePipeEnd(self._stderr_pipe[1])

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
                self._stdin_pipe[1] \
                    = msvcrt.open_osfhandle(self._stdin_pipe[1], 0)
                stdin_thread = Thread(target = self.__CallUntilNone,
                                      args = (self._WriteStdin,
                                              "_stdin_pipe"))
            else:
                stdin_thread = None
                
            if self._stdout_pipe:
                self._stdout_pipe[0] \
                    = msvcrt.open_osfhandle(self._stdout_pipe[0], 0)
                stdout_thread = Thread(target = self.__CallUntilNone,
                                       args = (self._ReadStdout,
                                               "_stdout_pipe"))
            else:
                stdout_thread = None

            if self._stderr_pipe:
                self._stderr_pipe[0] \
                    = msvcrt.open_osf_handle(self._stderr_pipe[0], 0)
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

        return self._CreatePipe()


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
        inheritable by child processes."""

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
            return os.pipe()
            

    def __CallUntilNone(self, f, attribute):
        """Call 'f' until 'self.attribute' is 'None'.

        'f' -- A callable.

        'attribute' -- A string giving the name of an attribute."""

        while getattr(self, attribute) is not None:
            f()
            
    
    def __UninheritableHandle(self, handle):
        """Return a duplicate of a file handle that is not inheritable.

        'handle' -- A file handle.

        returns -- A new handle that is a duplicate of the
        'handle'.

        This method should only be used under Windows."""

        assert sys.platform == "win32"
        
        current_process = win32api.GetCurrentProcess()
        return win32api.DuplicateHandle(current_process,
                                        handle,
                                        current_process,
                                        0,
                                        inheritable,
                                        win32con.DUPLICATE_SAME_ACCESS)

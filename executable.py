########################################################################
#
# File:   executable.py
# Author: Mark Mitchell
# Date:   02/15/2002
#
# Contents:
#   Executable
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
#######################################################################

import os
import select

########################################################################
# Classes
#######################################################################

class Executable:
    """An 'Executable' is a program that the operating system can run."""

    def __init__(self, path, dir = None):
        """Construct a new 'Executable'.

        'path' -- A string giving the location of the executable.

        'dir' -- If not 'None', the directory to which the child
        should change before executing."""

        self.__path = path
        self.__dir = dir
        

    def GetPath(self):
        """Return the location of the executable.

        returns -- A string giving the location of the executable.
        This location is the one that was specified as the 'path'
        argument to '__init__'."""
        
        return self.__path


    def Spawn(self, arguments=[]):
        """Spawn the program.

        'arguments' -- The sequence of arguments that should be passed
        to the executable.  The first argument provided in this
        sequence will be 'argv[0]'.

        The child is executed via 'fork' and 'execvp'.  Before calling
        'fork', the parent will call 'self._InitializeParent'.  Before
        calling 'execvp', the child will call 'self._InitializeChild'.

        The PID of the child is available by calling '_GetChild'."""

        # Initialize the parent.
        self._InitializeParent()

        # Fork.
        self.__child = os.fork()

        if self.__child == 0:
            try:
                # Initialize the child.
                self._InitializeChild()
                # Exec the program.
                os.execvp(self.GetPath(), arguments)
            except:
                # Exit immediately.
                os._exit(1)

            # This code should never be reached.
            assert None
                

    def Run(self, arguments=[]):
        """Spawn the program and wait for it to finish.

        'arguments' -- The sequence of arguments that should be passed
        to the executable.  The first argument provided in this
        sequence will be 'argv[0]'.

        returns -- The status returned by 'waitpid' for the program."""

        # Spawn the program.
        self.Spawn(arguments)
        # Give the parent a chance to do whatever it needs to do.
        self._DoParent()
        # Wait for the child to exit.
        return os.waitpid(self._GetChild(), 0)[1]

        
    def _GetChild(self):
        """Return the PID of the child process.

        returns -- The PID of the child process."""

        return self.__child
        
        
    def _InitializeParent(self):
        """Initialize the parent process.

        Before 'fork' is called this method is invoked to give the
        parent a chance to initialize itself.  This method is called
        before '_InitializeChild' is called."""

        pass


    def _InitializeChild(self):
        """Initialize the child process.

        After 'fork' is called this method is invoked to give the
        child a chance to initialize itself.  '_InitializeParent' will
        already have been called in the parent process."""

        if self.__dir:
            os.chdir(self.__dir)


    def _DoParent(self):
        """Perform actions required in the parent after 'Spawn'."""

        pass
    


class RedirectedExecutable(Executable):
    """A 'RedirectedExecutable' redirects the standard I/O streams."""

    def _InitializeParent(self):
        """Initialize the parent process.

        Before 'fork' is called this method is invoked to give the
        parent a chance to initialize itself.  This method is called
        before '_InitializeChild' is called."""

        # Create a pipe for each of the streams.
        self._stdin_pipe = self._StdinPipe()
        self._stdout_pipe = self._StdoutPipe()
        self._stderr_pipe = self._StderrPipe()

        # There has been no output yet.
        self.stdout = ""
        self.stderr = ""
        
        
    def _InitializeChild(self):
        """Initialize the child process.

        'data1' -- The value that was passed to 'Run' as 'data'.

        'data2' -- The value that was previously returned by
        '_InitializeParent'.
        
        After 'fork' is called this method is invoked to give the
        child a chance to initialize itself.  '_InitializeParent' will
        already have been called in the parent process."""

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
        """Perform actions required in the parent after 'fork'."""

        # Close the pipe ends that we do not need.
        if self._stdin_pipe:
            os.close(self._stdin_pipe[0])
        if self._stdout_pipe:
            os.close(self._stdout_pipe[1])
        if self._stderr_pipe:
            os.close(self._stderr_pipe[1])

        # Process the various redirected streams until none of the
        # streams remain open.
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
        """Write to the standard input pipe."""

        # Close the pipe.
        os.close(self._stdin_pipe[1])
        self._stdin_pipe = None


    def _StdinPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None' if the standard input should be
        closed in the child."""

        return os.pipe()


    def _StdoutPipe(self):
        """Return a pipe to which to redirect the standard output.

        returns -- A pipe, or 'None' if the standard output should be
        closed in the child."""

        return os.pipe()


    def _StderrPipe(self):
        """Return a pipe to which to redirect the standard input.

        returns -- A pipe, or 'None'.  If 'None' is returned, but
        '_StdoutPipe' returns a pipe, then the standard error and
        standard input will both be redirected to that pipe.  However,
        if '_StdoutPipe' also returns 'None', then the standard error
        will be closed in the child."""

        return os.pipe()

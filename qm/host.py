########################################################################
#
# File:   host.py
# Author: Mark Mitchell
# Date:   2005-06-03
#
# Contents:
#   Host
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

from   qm.executable import RedirectedExecutable
from   qm.extension import Extension
import os.path

########################################################################
# Classes
#######################################################################

class Host(Extension):
    """A 'Host' is a logical machine.

    Each logical machine has a default directory.  When a file is
    uploaded to or downloaded from the machine, and a relative path
    is specified, the patch is relative to the default directory.
    Similarly, when a program is run on the remote machine, its
    initial working directory is the default directory.

    The interface presented by 'Host' is a lowest common
    denominator.  The objective is not to expose all the functionality
    of any host; rather it is to provide an interface that can be used
    on many hosts."""

    kind = "host"
    
    class Executable(RedirectedExecutable):
        """An 'Executable' is a simple redirected executable.

        The standard error and standard output streams are combined
        into a single stream.

        The standard input is not closed before
        invoking the program because SSH hangs if its standard input
        is closed before it is invoked.  For example, running:

           ssh machine echo hi <&-

        will hang with some versions of SSH."""     

        def _StderrPipe(self):

            return None


    def __init__(self, arguments = None, **args):

        if arguments: args.update(arguments)
        super(Host, self).__init__(**args)


    def Run(self, path, arguments, environment = None, timeout = -1,
            relative = False):
        """Run a program on the remote host.

        'path' -- The name of the program to run, on the remote host.
        If 'relative' is true, or if 'path' is not an absolute path
        but does contain at least one directory separator, then 'path'
        is interpreted relative to the default directory.  Otherwise,
        'path' is used unmodified.
        
        'arguments' -- The sequence of arguments that should be passed
        to the program.

        'environment' -- If not 'None', a dictionary of pairs of
        strings to add to the environment of the running program.
        
        'timeout' -- The number of seconds the program is permitted
        to execute.  After the 'timeout' expires, the program will be
        terminated.  However, in some cases (such as when using 'rsh')
        it will be the local side of the connection that is closed.
        The remote side of the connection may or may not continue to
        operate, depending on the vagaries of the remote operating
        system.
        
        returns -- A pair '(status, output)'.  The 'status' is the
        exit status returned by the program, or 'None' if the exit
        status is not available.  The 'output' is a string giving the
        combined standard output and standard error output from the
        program.""" 

        # Compute the full environment for the child.
        if environment is not None:
            new_environment = os.environ.copy()
            new_environment.update(environment)
            environment = new_environment
        executable = self.Executable(timeout)
        if relative:
            path = os.path.join(os.curdir, path)
        status = executable.Run([path] + arguments, environment)
        return (status, executable.stdout)


    def UploadFile(self, local_file, remote_file = None):
        """Copy 'local_file' to 'remote_file'.

        'local_file' -- The name of the file on the local machine.

        'remote_file' -- The name of the file on the remote machine.
        The 'remote_file' must be a relative path.  It is interpreted
        relative to the default directory.  If 'None', the
        'remote_file' is placed in the default directory using the
        basename of the 'local_file'.

        If the 'local_file' and 'remote_file' are the same, then this
        function succeeds, but takes no action."""

        raise NotImplementedError


    def DownloadFile(self, remote_file, local_file):
        """Copy 'remote_file' to 'local_file'.

        'remote_file' -- The name of the file on the remote machine.
        The 'remote_file' must be a relative path.  It is interpreted
        relative to the default directory.

        'local_file' -- The name of the file on the local machine.  If
        'None', the 'local_file' is placed in the current directory
        using the basename of the 'remote_file'.

        If the 'local_file' and 'remote_file' are the same, then this
        function succeeds, but takes no action."""

        raise NotImplementedError


    def UploadAndRun(self, path, arguments, environment = None,
                     timeout = -1):
        """Run a program on the remote host.

        'path' -- The name of the program to run, as a path on the
        local machine.

        'arguments' -- As for 'Run'.

        'environment' -- As for 'Run'.
        
        'timeout' -- As for 'Run'.

        returns -- As for 'Run'.

        The program is uploaded to the default directory on the remote
        host, run, and then deleted."""
        
        self.UploadFile(path)
        basename = os.path.basename(path)
        result = self.Run(basename,
                          arguments,
                          environment,
                          timeout,
                          relative = True)
        self.DeleteFile(basename)
        return result
        
        
    def DeleteFile(self, remote_file):
        """Delete the 'remote_file'.

        'remote_file' -- A relative path to the file to be deleted."""

        raise NotImplementedError

########################################################################
#
# File:   ssh_host.py
# Author: Mark Mitchell
# Date:   2005-06-03
#
# Contents:
#   SSHHost, RSHHost
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

from   qm.host import Host
import os
import os.path
from   qm.fields import TextField, SetField
import qm.common
import sys

########################################################################
# Classes
#######################################################################

class SSHHost(Host):
    """An 'SSHHost' is accessible via 'ssh' or a similar program."""

    # If not empty, the name of the remote host. 
    host_name = TextField()
    # The path to "ssh".
    ssh_program = TextField(
        default_value = "ssh",
        description = """The path to the remote shell program."""
        )
    # Any arguments that must be provided to "ssh". 
    ssh_args = SetField(
        TextField(description =
                  """The arguments to the remote shell program."""))
    # The path to "scp".
    scp_program = TextField(
        default_value = "scp",
        description = """The path to the remote copy program."""
        )
    # Any arguments that must be provided to "scp".
    scp_args = SetField(
        TextField(description =
                  """The arguments to the remote copy program."""))
    # The default directory on the remote system.
    default_dir = TextField(
        description = """The default directory on the remote system."""
        )

    nfs_dir = TextField(
        description = """The default directory, as seen from the local host.
    
        If not empty, 'nfs_dir' is a directory on the local machine
        that is equivalent to the default directory on the remote
        machine.  In that case, files will be copied to and from this
        directory on the local machine, rather than by using
        'scp'."""
        )

    user_name = TextField(
        description = """The user name on the remote host.

        If not empty, the user name that should be used when
        connecting to the remote host."""
        )
    
    def Run(self, path, arguments, environment = None, timeout = -1,
            relative = False):

        default_dir = self.default_dir
        if not default_dir:
            default_dir = os.curdir
        if (relative
            or (not os.path.isabs(path)
                and (path.find(os.path.sep) != -1
                     or (os.path.altsep
                         and path.find(os.path.altsep) != -1)))):
            path = os.path.join(default_dir, path)
        path, arguments = self._FormSSHCommandLine(path, arguments,
                                                   environment)
        return super(SSHHost, self).Run(path, arguments, None, timeout)


    def UploadFile(self, local_file, remote_file = None):

        if remote_file is None:
            remote_file = os.path.basename(local_file)
        if self.nfs_dir:
            remote_file = os.path.join(self.nfs_dir, remote_file)
            super(SSHHost, self).UploadFile(local_file, remote_file)
        else:    
            if self.default_dir:
                remote_file = os.path.join(self.default_dir, remote_file)
            command = self._FormSCPCommandLine(True, local_file,
                                               remote_file)
            executable = self.Executable()
            status = executable.Run(command)
            if ((sys.platform != "win32"
                 and (not os.WIFEXITED(status)
                      or os.WEXITSTATUS(status) != 0))
                or (sys.platform == "win32" and status != 0)):
                raise qm.common.QMException("could not upload file")
        

    def DownloadFile(self, remote_file, local_file = None):

        if local_file is None:
            local_file = os.path.basename(remote_file)
        if self.nfs_dir:
            remote_file = os.path.join(self.nfs_dir, remote_file)
            super(SSHHost, self).DownloadFile(remote_file, local_file)
        else:
            if self.default_dir:
                remote_file = os.path.join(self.default_dir, remote_file)
            command = self._FormSCPCommandLine(False, local_file,
                                               remote_file)
            executable = self.Executable()
            executable.Run(command)


    def DeleteFile(self, remote_file):

        if self.default_dir:
            remote_file = os.path.join(self.default_dir, remote_file)
        return self.Run("rm", [remote_file])

        
    def _FormSSHCommandLine(self, path, arguments, environment = None):
        """Form the 'ssh' command line.

        'path' -- The remote command, in the same format expected by
        'Run'. 
        
        'arguments' -- The arguments to the remote command.

        'environment' -- As for 'Run'.

        returns -- A pair '(path, arguments)' describing the command
        to run on the local machine that will execute the remote
        command."""

        command = self.ssh_args + [self.host_name]
        if self.user_name:
            command += ["-l", self.user_name]
        if environment is not None:
            command.append("env")
            for (k, v) in environment.iteritems():
                command.append("%s='%s'" % (k, v))
        command.append(path)
        command += arguments

        return self.ssh_program, command


    def _FormSCPCommandLine(self, upload, local_file, remote_file):
        """Form the 'scp' command line.

        'upload' -- True iff the 'local_file' should be copied to the
        remote host.

        'local_file' -- The path to the local file.

        'remote_file' -- The path to the remote file.

        returns -- The list of arguments for a command to run on the
        local machine that will perform the file copy."""

        if self.default_dir:
            remote_file = os.path.join(self.default_dir, remote_file)
        remote_file = self.host_name + ":" + remote_file
        if self.user_name:
            remote_file = self.user_name + "@" + remote_file
        command = [self.scp_program] + self.scp_args
        if upload:
            command += [local_file, remote_file]
        else:
            command += [remote_file, local_file]

        return command    



class RSHHost(SSHHost):
    """An 'RSHHost' is an 'SSHHost' that uses 'rsh' instead of 'ssh'.

    The reason that 'RSHHost' is a separate class is that (a) that
    makes it easier for users to construct an 'SSHHost', and (b) 'rsh'
    does not return the exit code of the remote program, so 'Run'
    requires adjustment."""

    # Override the default values.
    ssh_program = TextField(
        default_value = "rsh",
        description = """The path to the remote shell program."""
        )
    scp_program = TextField(
        default_value = "rcp",
        description = """The path to the remote copy program."""
        )

    def Run(self, path, arguments, environment = None, timeout = -1):

        status, output = \
                super(RSHHost, self).Run(path, arguments,
                                         environment, timeout)
        # The exit status of 'rsh' is not the exit status of the
        # remote program.  The exit status of the remote program is
        # unavailable. 
        return (None, output)

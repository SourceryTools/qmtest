########################################################################
#
# File:   local_host.py
# Author: Mark Mitchell
# Date:   2005-06-03
#
# Contents:
#   LocalHost
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

import os
import os.path
from   qm.remote_host import RemoteHost
import shutil

########################################################################
# Classes
#######################################################################

class LocalHost(RemoteHost):
    """A 'LocalHost' is the machine on which Python is running.

    The default directory for a 'LocalHost' is the current working
    directory for this Python process."""

    def Run(self, path, arguments, environment = None, timeout = -1):

        # Compute the full environment for the child.
        if environment is not None:
            new_environment = os.environ.copy()
            new_environment.update(environment)
            environment = new_environment
        executable = self.Executable(timeout)
        status = executable.Run([path] + arguments, environment)
        return (status, executable.stdout)


    def UploadFile(self, local_file, remote_file = None):

        if remote_file is None:
            remote_file = os.path.basename(local_file)
        # Do not copy the files if they are the same.
        if not self._SameFile(local_file, remote_file):
            shutil.copy(local_file, remote_file)


    def DownloadFile(self, remote_file, local_file = None):

        return self.UploadFile(remote_file, local_file)


    def _SameFile(self, file1, file2):
        """Return true iff 'file1' and 'file2' are the same file.

        returns -- True iff 'file1' and 'file2' are the same file,
        even if they have different names."""

        if not os.path.exists(file1) or not os.path.exists(file2):
            return False
        if hasattr(os.path, "samefile"):
            return os.path.samefile(file1, file2)
        return (os.path.normcase(os.path.abspath(file1))
                == os.path.normcase(os.path.abspath(file2)))


    def DeleteFile(self, remote_file):

        os.remove(remote_file)

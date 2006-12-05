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
from   qm.host import Host
import shutil

########################################################################
# Classes
#######################################################################

class LocalHost(Host):
    """A 'LocalHost' is the machine on which Python is running.

    The default directory for a 'LocalHost' is the current working
    directory for this Python process."""

    def UploadFile(self, local_file, remote_file = None):

        if remote_file is None:
            remote_file = os.path.basename(local_file)
        # Do not copy the files if they are the same.
        if not self._SameFile(local_file, remote_file):
            shutil.copy(local_file, remote_file)


    def UploadAndRun(self, path, arguments, environment = None,
                     timeout = -1):

        # There is no need to actually upload the file, since it is
        # running on the local machine.
        return self.Run(path, arguments, environment, timeout)


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

########################################################################
#
# File:   temporary.py
# Author: Alex Samuel
# Date:   2001-04-06
#
# Contents:
#   Resource classes to manage temporary files and directories.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os
import qm.common
import qm.fields
from   qm.test.result import *
from   qm.test.test import *
from   qm.test.resource import *
import tempfile

########################################################################
# classes
########################################################################

class TempDirectoryResource(Resource):
    """Resource class to manage a temporary directory.

    An instance of this resource creates a temporary directory during
    setup, and deletes it during cleanup.  The full path to the
    directory is available to tests via a context property."""

    arguments = [
        qm.fields.TextField(
            name="dir_path_property",
            title="Directory Path Property Name",
            description="The name of the context property which is "
            "set to the path to the temporary directory.",
            default_value="temp_dir_path"
            ),

        qm.fields.IntegerField(
            name="delete_recursively",
            title="Delete Directory Recursively",
            description="If non-zero, the contents of the temporary "
            "directory are deleted recursively during cleanup. "
            "Otherwise, the directory must be empty on cleanup.",
            default_value=0
            ),
        ]


    def SetUp(self, context, result):
        # Generate a temporary file name.
        self.__dir_path = tempfile.mktemp()
        try:
            # Create the directory.
            os.mkdir(self.__dir_path, 0700)
        except OSError, error:
            # Setup failed.
            cause = "Directory creation failed.  %s" % str(error)
            result.Fail(cause)
        else:
            # Setup succeeded.  Store the path to the directory where
            # tests can get at it.
            context[self.dir_path_property] = self.__dir_path
    

    def CleanUp(self, result):
        # Extract the path to the directory.
        dir_path = self.__dir_path
        # Clean up the directory.
        try:
            if self.delete_recursively:
                qm.common.rmdir_recursively(dir_path)
            else:
                os.rmdir(dir_path)
        except OSError, error:
            # Cleanup failed.
            cause = "Directory cleanup failed.  %s" % str(error)
            Result.Fail(cause=cause)
        else:
            # Cleanup succeeded.
            pass


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

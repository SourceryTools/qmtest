########################################################################
#
# File:   temporary.py
# Author: Alex Samuel
# Date:   2001-04-06
#
# Contents:
#   Resource classes to manage temporary files and directories.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
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
import qm.temporary_directory

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
            description="""This field is obsolete  All temporary
            directories are removed recursively.""",
            default_value=1,
            ),
        ]


    def SetUp(self, context, result):

        # Generate a temporary file name.
        self.__dir = qm.temporary_directory.TemporaryDirectory()
        context[self.dir_path_property] = self.__dir.GetPath()
    

    def CleanUp(self, result):

        del self.__dir


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

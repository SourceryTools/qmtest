########################################################################
#
# File:   build.py
# Author: Mark Mitchell
# Date:   2003-11-23
#
# Contents:
#   Command to create the build files.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils.command.build import build as base
from os.path import join, normpath

########################################################################
# Classes
########################################################################

class build(base):
    """Build files required for installation."""

    def run(self):

        # Do the default actions.
        base.run(self)
        # Copy the classes.qmc file.
        self.copy_file(join ("qm", "test", "classes", "classes.qmc"),
                       join(self.build_lib, "qm", "test", "classes",
                            "classes.qmc"))
                                

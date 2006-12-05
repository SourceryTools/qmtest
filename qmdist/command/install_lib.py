########################################################################
#
# File:   install_lib.py
# Author: Mark Mitchell
# Date:   2003-11-23
#
# Contents:
#   Command to install library files.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils.command.install_lib import install_lib as base
from os.path import join, normpath

########################################################################
# Classes
########################################################################

class install_lib(base):
    """Install library files."""

    def get_inputs(self):
    
        inputs = base.get_inputs(self)
        return inputs + [join("qm", "test", "classes", "classes.qmc")]


    def get_outputs(self):
        
        outputs = base.get_outputs(self)
        return outputs + [join(self.install_dir,
                               "qm", "test", "classes", "classes.qmc")]

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
from qmdist.command import reset_config_variables
import sys
from os.path import join

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

    def run(self):
        
        # Do the standard installation.
        base.run(self)
        
        config_file = join(self.install_dir, 'qm', 'config.py')
        self.announce("adjusting config parameters")
        i = self.distribution.get_command_obj('install')
        prefix = i.root or i.prefix
        extension_path = join('share',
                              'qmtest',
                              'site-extensions-%d.%d'%sys.version_info[:2])
        reset_config_variables(config_file,
                               prefix=prefix, extension_path=extension_path)


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
        prefix = i.prefix
        extension_path = join('share',
                              'qmtest',
                              'site-extensions-%d.%d'%sys.version_info[:2])
        reset_config_variables(config_file,
                               version=self.distribution.get_version(),
                               prefix=prefix, extension_path=extension_path)

        # Make sure the new config file gets recompiled, or else python may
        # not notice it is in fact different from the original config file.
        files = [config_file]

        from distutils.util import byte_compile
        install_root = self.get_finalized_command('install').root

        if self.compile:
            byte_compile(files, optimize=0,
                         force=1, prefix=install_root,
                         dry_run=self.dry_run)
        if self.optimize > 0:
            byte_compile(files, optimize=self.optimize,
                         force=1, prefix=install_root,
                         verbose=self.verbose, dry_run=self.dry_run)


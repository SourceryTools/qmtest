########################################################################
#
# File:   install_data.py
# Author: Stefan Seefeld
# Date:   2003-09-01
#
# Contents:
#   command to install data files
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from distutils.command import install_data as base
import os

class install_data(base.install_data):
    """Extends 'install_data' by generating a config module.

    This module contains data only available at installation time,
    such as installation paths for data files."""

    def run(self):
        """Run this command."""
        
        id = self.distribution.get_command_obj('install_data')
        il = self.distribution.get_command_obj('install_lib')
        base.install_data.run(self)
        config = os.path.join(il.install_dir, 'qm/config.py')
        self.announce("generating %s" %(config))
        outf = open(config, "w")
        outf.write("version='%s'\n"%(self.distribution.get_version()))
        
        outf.write("\n")
        self.outfiles.append(config)

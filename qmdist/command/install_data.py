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

########################################################################
# Imports
########################################################################

from   distutils.command import install_data as base
import os
from   qmdist.command import get_relative_path

########################################################################
# Classes
########################################################################

class install_data(base.install_data):
    """Extends 'install_data' by generating a config module.

    This module contains data only available at installation time,
    such as installation paths for data files."""

    def run(self):

        # Do the standard installation.
        base.install_data.run(self)
        
        i = self.distribution.get_command_obj('install')
        il = self.distribution.get_command_obj('install_lib')

        config = os.path.join(il.install_dir, 'qm/config.py')
        self.announce("generating %s" %(config))
        outf = open(config, "w")
        outf.write("version='%s'\n" % (self.distribution.get_version()))
        # Compute the path to the data directory.
        data_dir = os.path.join(self.install_dir, "qm")
        # Encode the relative path from the installation prefix to the
        # data directory.
        outf.write("data_dir='%s'\n"
                   % get_relative_path (i.prefix, data_dir))
        outf.write("\n")
        self.outfiles.append(config)

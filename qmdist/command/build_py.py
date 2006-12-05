########################################################################
#
# File:   build_py.py
# Author: Stefan Seefeld
# Date:   2006-11-03
#
# Contents:
#   Command to build the python modules.
#
# Copyright (c) 2006 by CodeSourcery.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils.command.build_py import build_py as base
from qmdist.command import reset_config_variables
import os, sys

########################################################################
# Classes
########################################################################

class build_py(base):
    """Adjust config variable to make them valid even during the build.
    This allows us to run (in particular, test) QMTest after being built,
    but before being installed."""

    def run(self):

        # Do the default actions.
        base.run(self)
        config_file = os.path.join(self.build_lib, 'qm', 'config.py')
        self.announce("adjusting config parameters")
        reset_config_variables(config_file,
                               prefix=os.getcwd(),
                               extension_path=os.path.join('qm',
                                                           'test',
                                                           'classes'))


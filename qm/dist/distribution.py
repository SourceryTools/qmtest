########################################################################
#
# File:   setup.py
# Author: Stefan Seefeld
# Date:   2005-11-16
#
# Contents:
#   Distribution class adding 'install_extensions' command.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils import dist
from qm.dist.command.build_extensions import build_extensions
from qm.dist.command.install_extensions import install_extensions

class Distribution(dist.Distribution):


    def __init__(self, attrs=None):

        # Set up the Distribution class to make it aware of the additional
        # commands. First we need to add an attribute so setup() can pass
        # a 'qmtest_extensions' parameter.
        self.qmtest_extensions = None
        dist.Distribution.__init__(self, attrs)
        # Now add our own commands to the list.
        self.cmdclass['build_extensions'] = build_extensions
        self.cmdclass['install_extensions'] = install_extensions

        # Register the command as a sub-command of 'install'
        def has_extensions(cmd): return self.qmtest_extensions 
        build = self.get_command_class('build')
        build.sub_commands.append(('build_extensions', has_extensions))
        install = self.get_command_class('install')
        install.sub_commands.append(('install_extensions', has_extensions))

########################################################################
#
# File:   bdist_wininst.py
# Author: Stefan Seefeld
# Date:   2006-10-30
#
# Contents:
#   command to build windows installer
#
# Copyright (c) 2006 by CodeSourcery.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from distutils.command.bdist_wininst import bdist_wininst as base
import os, os.path

########################################################################
# Classes
########################################################################

class bdist_wininst(base):
    def initialize_options(self):
        base.initialize_options(self)
        self.title = 'QMTest %s'%self.distribution.get_version()
        self.bitmap = os.path.join('share', 'logo.bmp')
        self.install_script = 'qmtest-postinstall.py'

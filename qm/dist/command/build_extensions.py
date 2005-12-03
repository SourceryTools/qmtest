########################################################################
#
# File:   build_extensions.py
# Author: Stefan Seefeld
# Date:   2005-11-16
#
# Contents:
#   Command to build qmtest extensions.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.xmlutil
from distutils.command.build_py import build_py
from distutils.util import get_platform
import os, sys, dircache

########################################################################
# Classes
########################################################################

class build_extensions(build_py):
    """build extension files."""

    description = "build qmtest extension classes."

    def finalize_options(self):

        b = self.distribution.get_command_obj('build')
        b.ensure_finalized()
        base = b.build_base

        build_py.finalize_options(self)

        self.build_dir = os.path.join(base, 'ext')
        if self.distribution.ext_modules:
            plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
            self.build_dir += plat_specifier


        self.extensions = self.distribution.qmtest_extensions


    def get_input(self):
        """Return all files containing extension classes."""
    
        files = [os.path.join(self.extensions, f)
                 for f in dircache.listdir(self.extensions)
                 if f.endswith('.py') or f == 'classes.qmc']
        return files
    

    def run(self):

        self.mkpath(self.build_dir)
        for f in self.get_input():
            basename = os.path.basename(f)
            self.copy_file(f, os.path.join(self.build_dir, basename),
                           preserve_mode=0)

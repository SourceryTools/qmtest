########################################################################
#
# File:   install_scripts.py
# Author: Mark Mitchell
# Date:   2003-10-14
#
# Contents:
#   Command to install scripts.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   distutils.command import install_scripts as base
import os
from   qmdist.command import get_relative_path
import re
import sys

########################################################################
# Classes
########################################################################

class install_scripts(base.install_scripts):
    """Handle installation of Python scripts."""

    def run(self):

        # Do the standard installation.
        base.install_scripts.run(self)

        # Postprocess the main QMTest Python script.  The script will
        # have ".py" extension on Windows systems, but not on UNIX
        # systems.
        for basename in ("qmtest", "qmtest.py"):
            qmtest_file = os.path.join(self.install_dir, basename)
            if not os.path.exists(qmtest_file):
                continue
            # Read the contents of the script.
            qmtest_script = open(qmtest_file).read()
            # Encode the relative path from that script to the top of the
            # installation directory.
            i = self.distribution.get_command_obj('install')
            prefix = i.root or i.prefix
            rel_prefix = get_relative_path(self.install_dir, prefix)
            assignment = 'rel_prefix = "%s"' % rel_prefix
            qmtest_script = re.sub("rel_prefix = .*", assignment,
                                   qmtest_script)
            # Encode the relative path from the prefix to the library
            # directory.
            il = self.distribution.get_command_obj('install_lib')
            rel_libdir = get_relative_path(prefix, il.install_dir)
            assignment = 'rel_libdir = "%s"' % rel_libdir
            qmtest_script = re.sub("rel_libdir = .*", assignment,
                                   qmtest_script)

            # Write the script back out.
            open(qmtest_file, "w").write(qmtest_script)

########################################################################
#
# File:   build_scripts.py
# Author: Stefan Seefeld
# Date:   2005-01-05
#
# Contents:
#   Command to build the scripts.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import os, sys

# The workaround is only needed on posix systems for
# python version < 2.3.
if os.name != 'posix' or sys.version_info[:2] > (2,2):

    # The original command is good enough.
    from distutils.command.build_scripts import build_scripts

else:
    
    from distutils.command.build_scripts import build_scripts as base
    from stat import ST_MODE
    from os.path import join, normpath

    ########################################################################
    # Classes
    ########################################################################

    class build_scripts(base):
        """Build scripts required for installation. Extend the default
        build_scripts command as that ommitted to make the scripts executable."""

        def run(self):

            # Do the default actions.
            base.run(self)
            # Work around distutils bug (for python > 2.3)
            # change permissions to executable.
            for s in self.scripts:
                script = os.path.join(self.build_dir, os.path.basename(s))

                if self.dry_run:
                    self.announce("changing mode of %s"%script)
                else:
                    oldmode = os.stat(script)[ST_MODE] & int('7777', 8)
                    newmode = (oldmode | int('555', 8)) & int('7777', 8)
                    if newmode != oldmode:
                        self.announce("changing mode of %s from %o to %o"%(script, oldmode, newmode)),
                        os.chmod(script, newmode)


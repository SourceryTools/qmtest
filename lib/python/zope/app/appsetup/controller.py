##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Top-level controller for 'zopectl'.
"""

import os

import zdaemon.zdctl


INSTANCE_HOME = os.path.dirname(
    os.path.dirname(os.path.dirname(zdaemon.__file__)))


class ZopectlCmd(zdaemon.zdctl.ZDCmd):

    def do_debug(self, rest):
        cmdline = os.path.join(INSTANCE_HOME, 'bin', 'debugzope')
        os.system(cmdline)

    def help_debug(self):
        print "debug -- Initialize the Zope application, providing a"
        print "         debugger object at an interactive Python prompt."

    def do_run(self, arg):
        cmdline = "%s %s" % (
            os.path.join(INSTANCE_HOME, 'bin', 'scriptzope'), arg)
        os.system(cmdline)

    def help_run(self):
        print "run <script> [args] -- run a Python script with the Zope "
        print "                       environment set up.  The script has "
        print "                       'root' exposed as the root container."


def main(args=None, options=None, cmdclass=ZopectlCmd):
    zdaemon.zdctl.main(args, options, cmdclass)

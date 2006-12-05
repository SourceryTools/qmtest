########################################################################
#
# File:   platform.py
# Author: Alex Samuel
# Date:   2001-04-30
#
# Contents:
#   Platform-specific code.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import common
import os
import qm
import string
import sys

########################################################################
# classes
########################################################################

class MailError(RuntimeError):

    pass


########################################################################
# initialization
########################################################################

if sys.platform == "win32":
    from platform_win32 import *
else:
    from platform_unix import *

########################################################################
# functions
########################################################################

def get_shell_for_command():
    """Return the command shell to use when running a single shell command.

    returns -- A sequence of argument list entries to use when invoking
    the shell.  The first element of the list is the shell executable
    path.  The command should be appended to the argument list."""

    shell = common.rc.Get("command_shell", None, "common")
    if shell is not None:
        # Split the configuration value into an argument list.
        shell = common.split_argument_list(shell)
    else:
	if sys.platform == "win32":
	    shell = default_shell + ["/c"]
	else:
            shell = default_shell + ["-c"]
    return shell


def get_shell_for_script():
    """Return the command shell to use when running a shell script.

    returns -- A sequence of argument list entries to use when running a
    shell script.  The first element of the list is the shell
    executable.  The name of the script should be appended to the
    argument list."""

    shell = common.rc.Get("script_shell", None, "common")
    if shell is not None:
        # Split the configuration value into an argument list.
        shell = common.split_argument_list(shell)
    else:
        # Use the default, but copy it so the caller can change it.
        shell = default_shell[:]
    return shell


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

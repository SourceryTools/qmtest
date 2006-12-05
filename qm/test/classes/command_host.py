########################################################################
#
# File:   command_host.py
# Author: Stefan Seefeld
# Date:   2006-10-24
#
# Contents:
#   CommandHost
#
# Copyright (c) 2006 by CodeSourcery, Inc.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

from qm.fields import TextField, SetField
from qm.test.classes import local_host
import sys, os, os.path

########################################################################
# Classes
#######################################################################

class CommandHost(local_host.LocalHost):
    """A CommandHost runs an executable through a command.

    The 'command' parameter specifies the command to use, while
    'command_args' contains a set of arguments to be passed to the
    command."""


    command = TextField(description="Name of the command"
                        " used to run the executable.")
    command_args = SetField(TextField(description="Set of arguments"
                                      " passed to the command."))

    def Run(self, path, arguments, environment = None, timeout = -1,
            relative = False):

        if (relative
            or (not os.path.isabs(path)
                and (path.find(os.path.sep) != -1
                     or (os.path.altsep
                         and path.find(os.path.altsep) != -1)))):
            path = os.path.join(os.curdir, path)
        arguments = self.command_args + [path] + arguments
        return local_host.LocalHost.Run(self, self.command,
                                        arguments, environment, timeout)

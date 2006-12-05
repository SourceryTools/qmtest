########################################################################
#
# File:   serial_target.py
# Author: Mark Mitchell
# Date:   12/19/2001
#
# Contents:
#   SerialTarget
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   qm.test.base import *
from   qm.test.context import *
from   qm.test.target import *

########################################################################
# Classes
########################################################################

class SerialTarget(Target):
    """A target that runs tests in serial on the local machine."""

    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""

        # The target is always idle when this method is called since
        # whenever it asked to perform a task it blocks the caller.
        return 1



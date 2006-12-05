########################################################################
#
# File:   simulator.py
# Author: Mark Mitchell
# Date:   2005-06-03
#
# Contents:
#   Simulator
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
#######################################################################

from local_host import LocalHost
from qm.fields import TextField, SetField

########################################################################
# Classes
#######################################################################

class Simulator(LocalHost):
    """A 'Simulator' is a semi-hosted simulation environment.

    The local file system is shared with the simulated machine.  A
    simulator is used to execute programs."""

    simulator = TextField(
        description = """The simulation program."""
        )

    # Any arguments that must be provided to the simulator.
    simulator_args = SetField(
        TextField(description = """Arguments to the simulation program."""))
    
    def Run(self, path, arguments, environment = None, timeout = -1):

        arguments = self.simulator_args + [path] + arguments
        return super(Simulator, self.Run(self.simulator,
                                         arguments,
                                         environment,
                                         timeout))

########################################################################
#
# File:   rsh_target.py
# Author: Mark Mitchell
# Date:   10/30/2001
#
# Contents:
#   RSHTarget
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   process_target import *
import string

########################################################################
# Classes
########################################################################

class RSHTarget(ProcessTarget):
    """A target that runs tests via a remote shell invocation.

    A 'RSHTarget' runs tests on a remote computer via a remote shell
    call.  The remote shell is in the style of 'rsh' and 'ssh'.  Using
    the remote shell, the target invokes the 'qmtest-remote' script,
    which services commands sent via 'stdin', and replies via
    'stdout'."""

    arguments = [
        qm.fields.TextField(
            name="host",
            title="Remote Host Name",
            description="""The name of the host on which to run tests.

            The name (or IP address) of the host on which QMTest
            should execute tests.  If this value is the empty string,
            the name of the target is used."""),
        qm.fields.TextField(
            name="remote_shell",
            title="Remote Shell Program",
            description="""The path to the remote shell program.

            The name of the program that can be used to create a
            remote shell.  This program must accept the same command
            line arguments as the 'rsh' program.""",
            default_value="ssh"),
        qm.fields.TextField(
            name="arguments",
            title="Remote Shell Arguments",
            description="""The arguments to provide to the remote shell.

            A space-separated list of arguments to provide to the
            remote shell program.""",
            default_value="")
        ]
    
    def __init__(self, properties, database):
        """Construct a new 'RSHTarget'.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
        run."""

        # Initialize the base class.
        ProcessTarget.__init__(self, properties, database)

        # Use the target name as the default name for the remote host.
        if not self.host:
            self.host = self.GetName()


    def _GetInterpreter(self):
        
        # Determine the remote shell program to use.
        remote_shell_program = self.remote_shell
        if not remote_shell_program:
            remote_shell_program = qm.rc.Get("remote_shell",
                                             default="ssh",
                                             section="common")
        # Extra command-line arguments to the remote shell program
        # may be specified with the "arguments" property.
        arguments = self.arguments.split(" ")

        return [remote_shell_program] + arguments + [self.host]

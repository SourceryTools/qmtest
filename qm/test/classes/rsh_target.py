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
    'stdout'.

    This target recognizes the following properties:

      'remote_shell' -- The path to the remote shell executable to
      use.  If omitted, the configuration variable 'remote_shell' is
      used instead.  If neither is specified, the default is
      '/usr/bin/ssh'.  The remote shell program must accept the
      command-line syntax 'remote_shell *remote_host*
      *remote_command*'.

      'host' -- The remote host name.  If omitted, the target name is
      used.

      'database_path' -- The path to the test database on the remote
      computer.  The test database must be identical to the local test
      database.  If omitted, the local test database path is used.

      'qmtest' -- The path to 'qmtest'.  The default is
      '/usr/local/bin/qmtest'.

      'arguments' -- Additional command-line arguments to pass to the
      remote shell program.  The value of this property is split at
      space characters, and the arguments are added to the command line
      before the name of the remote host."""

    def __init__(self, name, group, properties, database):
        """Construct a new 'RSHTarget'.

        'name' -- A string giving a name for this target.

        'group' -- A string giving a name for the target group
        containing this target.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
        run."""

        # Initialize the base class.
        ProcessTarget.__init__(self, name, group, properties, database)

        # Determine the host name.
        self.__host_name = self.GetProperty("host", None)
        if self.__host_name is None:
            # None specified; use the target name.
            self.__host_name = self.GetName()


    def _GetInterpreter(self):
        
        # Determine the remote shell program to use.
        remote_shell_program = self.GetProperty("remote_shell")
        open("/tmp/foo", "w").write(str(type(remote_shell_program)))
        if not remote_shell_program:
            remote_shell_program = qm.rc.Get("remote_shell",
                                             default="/usr/bin/ssh",
                                             section="common")
        # Extra command-line arguments to the remote shell program
        # may be specified with the "arguments" property. 
        extra_arguments = self.GetProperty("arguments", None)
        if extra_arguments is None:
            # None specified.
            extra_arguments = []
        else:
            # Split them at spaces.
            extra_arguments = string.split(extra_arguments, " ")

        return [remote_shell_program] + extra_arguments + [self.__host_name]

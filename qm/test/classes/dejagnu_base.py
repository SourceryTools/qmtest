########################################################################
#
# File:   dejagnu_base.py
# Author: Mark Mitchell
# Date:   05/15/2003
#
# Contents:
#   DejaGNUBase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Classes
########################################################################

class DejaGNUBase:
    """A 'DejaGNUBase' is a base class for tests and resources."""

    def _RecordCommand(self, result, command):
        """Record the execution of 'command'.

        'result' -- The 'Result' for the test.

        'command' -- A sequence of strings, giving the arguments to a
        command that is about to be executed.

        returns -- An integer giving the the index for this command.
        This value should be provided to '_RecordCommandOutput' after
        the command's output is known."""

        index = self.__next_command
        key = "DejaGNUTest.command_%d" % index
        result[key] = result.Quote(" ".join(command))
        self.__next_command += 1

        return index
        

    def _RecordCommandOutput(self, result, index, status, output):
        """Record the result of running a command.

        'result' -- The 'Result' for the test.
        
        'index' -- An integer, return from a previous call to
        '_RecordCommand'.
        
        'status' -- The exit status from the command.

        'output' -- A string containing the output, if any, from the
        command."""

        # Figure out what index to use for this output.
        
        if status != 0:
            result["DejaGNUTest.command_status_%d" % index] = str(status)
        if output:
            result["DejaGNUTest.command_output_%d" % index] \
              = result.Quote(output)


    def _SetUp(self, context):
        """Prepare to run a test.

        'context' -- The 'Context' in which this test will run.

        This method may be overridden by derived classes, but they
        must call this version."""

        # The next command will be the first.
        self.__next_command = 1

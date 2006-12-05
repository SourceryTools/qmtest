########################################################################
#
# File:   command_thread.py
# Author: Mark Mitchell
# Date:   01/02/2002
#
# Contents:
#   CommandThread
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import Queue
from   threading import *
import types

########################################################################
# Classes
########################################################################

class CommandThread(Thread):
    """A 'CommandThread' is a thread that executes commands.

    The commands are written to a 'Queue' by a controlling thread.
    The 'CommandThread' extracts the commands and dispatches them to
    derived class methods that process them.  This class is used as a
    base class for thread classes used by some targets.

    The commands are written to the 'Queue' as Python objects.  The
    normal commands have the form '(method, descriptor, context)'
    where 'method' is a string.  At present, the only value used for
    'method' is '_RunTest'.  In that case 'descriptor' is a test
    descriptor and 'context' is a 'Context'.  The 'Stop' command is
    provided as a simple string, not a tuple."""

    def __init__(self, target):
	"""Construct a new 'CommandThread'.

	'target' -- The 'Target' that owns this thread."""

	Thread.__init__(self, None, None, None)

        # Remember the target.
	self.__target = target

	# Create the queue to which the controlling thread will
	# write commands.
	self.__command_queue = Queue.Queue(0)


    def run(self):
        """Execute the thread."""
        
	try:
            # Process commands from the queue, until the "quit"
            # command is received.
            while 1:
                # Read the command.
                command = self.__command_queue.get()

                # If the command is just a string, it should be
                # the 'Stop' command.
                if isinstance(command, types.StringType):
                    assert command == "Stop"
                    self._Stop()
                    break

                # Decompose command.
                method, id, context = command
                # Run it.
                eval ("self.%s(id, context)" % method)
        except:
            # Exceptions should not occur in the above loop.  However,
            # in the event that one does occur it is easier to debug
            # QMTest is the exception is written out.
            exc_info = sys.exc_info()
            sys.stderr.write(qm.common.format_exception(exc_info))
            assert 0
            

    def GetTarget(self):
        """Return the 'Target' associated with this thread.

        returns -- The 'Target' with which this thread is associated.

        Derived classes must not override this method."""

        return self.__target


    def RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The 'TestDescriptor' for the test to be run.

        'context' -- The 'Context' in which to run the test.

        This method is called by the controlling thread.
        
        Derived classes must not override this method."""

        self.__command_queue.put(("_RunTest", descriptor, context))


    def Stop(self):
        """Stop the thread.

        Derived classes must not override this method."""

        self.__command_queue.put("Stop")

        
    def _RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The 'TestDescriptor' for the test to be run.

        'context' -- The 'Context' in which to run the test.

        Derived classes must override this method."""

        raise NotImplementedError


    def _Stop(self):
        """Stop the thread.

        This method is called in the thread after 'Stop' is called
        from the controlling thread.  Derived classes can use this
        method to release resources before the thread is destroyed.
        
        Derived classes may override this method."""

        pass

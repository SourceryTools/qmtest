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

        raise qm.common.MethodShouldBeOverriddenError, \
              "CommandThread._RunTest"


    def _Stop(self):
        """Stop the thread.

        This method is called in the thread after 'Stop' is called
        from the controlling thread.  Derived classes can use this
        method to release resources before the thread is destroyed.
        
        Derived classes may override this method."""

        pass

########################################################################
#
# File:   target.py
# Author: Mark Mitchell
# Date:   10/29/2001
#
# Contents:
#   QMTest Target class.
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

import qm
from   qm.test.result import *
import Queue
from   threading import *
import sys
import types

########################################################################
# classes
########################################################################

class Target:
    """Base class for target implementations.

    A 'Target' is an entity that can run tests.  QMTest can spread the
    workload from multiple tests across multiple targets.  In
    addition, a single target can run more that one test at once.

    'Target' is an abstract class.

    You can extend QMTest by providing your own target class
    implementation.

    To create your own test class, you must create a Python class
    derived (directly or indirectly) from 'Target'.  The documentation
    for each method of 'Target' indicates whether you must override it
    in your test class implementation.  Some methods may be
    overridden, but do not need to be.  You might want to override
    such a method to provide a more efficient implementation, but
    QMTest will work fine if you just use the default version."""

    def __init__(self, name, group, concurrency, properties,
                 database, response_queue):
        """Construct a 'Target'.

        'name' -- A string giving a name for this target.

        'group' -- A string giving a name for the target group
        containing this target.

        'concurrency' -- The amount of parallelism desired.  If 1, the
        target will execute only a single command at once.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
        run.

        'response_queue' -- The 'Queue' in which the results of test
        executions are placed."""

        self.__name = name
        self.__group = group
        self.__concurrency = concurrency
        self.__properties = properties
        self.__database = database
        self.__response_queue = response_queue
        

    def GetName(self):
        """Return the name of the target.

        Derived classes must not override this method."""
        
        return self.__name


    def GetGroup(self):
        """Return the group of which the target is a member.

        Derived classes must not override this method."""

        return self.__group


    def GetConcurrency(self):
        """Return the number of tests the target may run concurrently.

        Derived classes must not override this method."""

        return self.__concurrency


    def GetDatabase(self):
        """Return the 'Database' containing the tests this target will run.

        returns -- The 'Database' containing the tests this target will
        run.

        Derived classes must not override this method."""

        return self.__database


    def GetProperty(self, name, default=None):
        """Return the value of the property with the indicated 'name'.

        'name' -- A string naming a property.

        'default' -- The value to return if the property is not
        otherwise defined.

        returns -- The value associated with that property in the
        'target_spec' used to construct this 'Target', or the
        'default' if there is no such value.

        Derived classes must not override this method."""
        
        return self.__properties.get(name, default)


    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.IsIdle"


    def Start(self):
        """Start the target.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.Start"

        
    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used.

        Derived classes must override this method."""
        
        raise qm.common.MethodShouldBeOverriddenError, "Target.Stop"


    def RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.RunTest"


    def SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "Target.SetUpResource"


    def CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "Target.CleanUpResource"


    def RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution.

        This method may be called from a thread other than the main
        thread.
        
        Derived classes must not override this method."""

        # Record the target in the result.
        result[Result.TARGET] = self.GetName()
        # Put the result into the response queue.
        self.__response_queue.put(result)


class CommandThread(Thread):
    """A 'CommandThread' is a thread that executes commands.

    The commands are written to a 'Queue' by a controlling thread.
    The 'CommandThread' extracts the commands and dispatches them to
    derived class methods that process them.  This class is used as a
    base class for thread classes used by some targets.

    The commands are written to the 'Queue' as Python objects.  The
    normal commands have the form '(method, id, context)' where
    'method' is a string: one of '_RunTest', '_SetUpResource', or
    '_CleanUpResource'.  In that case 'id' is a test name or resource
    name, and 'context' is a 'Context'.  The 'Stop' command is
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


    def RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test.

        This method is called by the controlling thread.
        
        Derived classes must not override this method."""

        self.__command_queue.put(("_RunTest", test_id, context))


    def SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must not override this method."""

        self.__command_queue.put(("_SetUpResource", resource_id, context))


    def CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must not override this method."""

        self.__command_queue.put(("_CleanUpResource", resource_id, context))


    def Stop(self):
        """Stop the thread.

        Derived classes must not override this method."""

        self.__command_queue.put("Stop")

        
    def _RunTest(self, test_id, context):
        """Run the test given by 'test_id' in the thread.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "CommandThread._RunTest"


    def _SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "CommandThread._SetUpResource"


    def _CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "CommandThread._CleanUpResource"


    def _Stop(self):
        """Stop the thread.

        This method is called in the thread after 'Stop' is called
        from the controlling thread.  Derived classes can use this
        method to release resources before the thread is destroyed.
        
        Derived classes may override this method."""

        pass

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
from   qm.test.context import *
from   qm.test.result import *
import Queue
from   threading import *
import re
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

    def __init__(self, name, group, concurrency, properties, database):
        """Construct a 'Target'.

        'name' -- A string giving a name for this target.

        'group' -- A string giving a name for the target group
        containing this target.

        'concurrency' -- The amount of parallelism desired.  If 1, the
        target will execute only a single command at once.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
        run."""

        self.__name = name
        self.__group = group
        self.__concurrency = concurrency
        self.__properties = properties
        self.__database = database

        # There are no resources available on this target.
        self.__resources = {}
        

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


    def IsInGroup(self, group_pattern):
        """Returns true if this 'Target' is in a particular group.

        'group_pattern' -- A string giving a regular expression.

        returns -- Returns true if the 'group_pattern' denotes a
        regular expression that matches the group for this 'Target',
        false otherwise."""

        return re.match(group_pattern, self.GetGroup())
        
        
    def Start(self, response_queue):
        """Start the target.

        'response_queue' -- The 'Queue' in which the results of test
        executions are placed.
        
        Derived classes may override this method, but the overriding
        method must call this method at some point during its
        execution."""

        self.__response_queue = response_queue

        
    def Stop(self):
        """Stop the target.

        Clean up all resources that have been set up on this target
        and take whatever other actions are required to stop the
        target.
        
        Derived classes may override this method."""
        
        # Clean up any available resources.
        for (name, rop) in self.__resources.items():
            if rop and rop[1] == Result.PASS:
                self._CleanUpResource(name, rop[0])


    def RunTest(self, descriptor, context):
        """Run the test given by 'test_id'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test.

        Derived classes may override this method."""
        
        # See if the test requires any resources.
        resources = descriptor.GetResources()
        # There are not yet any additional context properties that
        # need to be passed to the test.
        properties = {}
        # See if there are resources that need to be set up.
        for resource in descriptor.GetResources():
            (r, outcome, resource_properties) \
                = self._SetUpResource(resource, context)
            
            # If the resource was not set up successfully,
            # indicate that the test itself could not be run.
            if outcome != Result.PASS:
                result = Result(Result.TEST, descriptor.GetId(),
                                context, Result.UNTESTED)
                result[Result.CAUSE] = qm.message("failed resource")
                result[Result.RESOURCE] = resource
                self._RecordResult(result)
                return
            # Update the list of additional context properties.
            properties.update(resource_properties)
        # Create the modified context.
        context = ContextWrapper(context, properties)
        # Run the test.
        result = Result(Result.TEST, descriptor.GetId(), context)
        try:
            descriptor.Run(context, result)
        except:
            result.NoteException()
        # Record the result.
        self._RecordResult(result)


    def _RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution.

        Derived classes may override this method, but the overriding
        method must call this method at some point during its
        execution."""

        # Record the target in the result.
        result[Result.TARGET] = self.GetName()
        # Put the result into the response queue.
        self.__response_queue.put(result)
            

    def _BeginResourceSetUp(self, resource_name):
        """Begin setting up the indicated resource.

        'resource_name' -- A string naming a resource.

        returns -- If the resource has already been set up, returns a
        tuple '(resource, outcome, properties)'.  The 'resource' is
        the 'Resource' object itself.  The 'outcome' indicates the
        outcome that resulted when the resource was set up.  The
        'properties' are a map from strings to strings indicating
        properties added by this resource.  If the resource has not
        been set up, but _BeginResourceSetUp has already been called
        for the resource, then the contents of the tuple will all be
        'None'.

        If this is the first time _BeginResourceSetUp has been called
        for this resource, then 'None' is returned, but the resource
        is marked as in the process of being set up.  It is the
        caller's responsibility to finish setting it up by calling
        '_FinishResourceSetUp'."""

        rop = self.__resources.get(resource_name)
        if rop:
            return rop
        self.__resources[resource_name] = (None, None, None)
        return None


    def _FinishResourceSetUp(self, resource, result):
        """Finish setting up a resource.

        'resource' -- The 'Resource' itself.
        
        'result' -- The 'Result' associated with setting up the
        resource.

        returns -- A tuple of the same form as is returned by
        '_BeginResourceSetUp' with the resource has already been set
        up."""

        rop = (resource,
               result.GetOutcome(),
               result.GetContext().GetAddedProperties())
        self.__resources[result.GetId()] = rop
        return rop


    def _SetUpResource(self, resource_name, context):
        """Set up the resource given by 'resource_id'.

        'resource_name' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        returns -- A map from strings to strings indicating additional
        properties added by this resource."""

        # Begin setting up the resource.
        rop = self._BeginResourceSetUp(resource_name)
        # If it has already been set up, there is no need to do it
        # again.
        if rop:
            return rop
        # Get the resource descriptor.
        resource = self.GetDatabase().GetResource(resource_name)
        # Set up the resource.
        context = ContextWrapper(context)
        result = Result(Result.RESOURCE, resource.GetId(), context,
                        Result.PASS, { Result.ACTION : "setup" } )
        # Set up the resource.
        try:
            resource.SetUp(context, result)
        except:
            result.NoteException()
        # Record the result.
        self._RecordResult(result)
        # And update the table of available resources.
        return self._FinishResourceSetUp(resource.GetItem(), result)


    def _CleanUpResource(self, name, resource):
        """Clean up the 'resource'.

        'resource' -- The 'Resource' that should be cleaned up.

        'name' -- The name of the reosurce itself."""

        result = Result(Result.RESOURCE, name, 
                        ContextWrapper(Context()),
                        Result.PASS, { Result.ACTION : "cleanup" } )
        # Clean up the resource.
        try:
            val = resource.CleanUp(result)
        except:
            result.NoteException()
        self._RecordResult(result)


        
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

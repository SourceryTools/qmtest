########################################################################
#
# File:   thread_target.py
# Author: Mark Mitchell
# Date:   10/30/2001
#
# Contents:
#   QMTest ThreadTarget class.
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

from   qm.test.base import *
from   qm.test.target import *
import Queue
from   threading import *

########################################################################
# classes
########################################################################

class LocalThread(CommandThread):
    """A 'LocalThread' executes commands locally."""

    def __init__(self, target):
	"""Construct a new 'LocalThread'.

	'target' -- The 'ThreadTarget' that owns this thread."""

	CommandThread.__init__(self, target)


    def _RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test."""

        test = self.GetTarget().GetDatabase().GetTest(test_id)
        result = run_test(test, context)
        self.RecordResult(result)
        

    def _SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        resource = self.GetTarget().GetDatabase().GetResource(resource_id)
        result = set_up_resource(resource, context)
        self.RecordResult(result)


    def _CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        resource = self.GetTarget().GetDatabase().GetResource(resource_id)
        result = clean_up_resource(resource, context)
        self.RecordResult(result)


    def RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution."""

        # Tell the target that we have nothing to do.
        self.GetTarget().NoteIdleThread(self)
        # Pass the result back to the target.
        self.GetTarget().RecordResult(result)



class ThreadTarget(Target):
    """A target implementation that runs tests in local threads.

    This target starts one thread for each degree of concurrency.  Each
    thread executes one test or resource function at a time."""

    def __init__(self, name, group, concurrency, properties,
                 database):
	"""Construct a 'ThreadTarget'.

        'name' -- A string giving a name for this target.

        'group' -- A string giving a name for the target group
        containing this target.

        'concurrency' -- The amount of parallelism desired.  If 1, the
        target will execute only a single command at once.

        'properties'  -- A dictionary mapping strings (property names)
        to strings (property values).
        
        'database' -- The 'Database' containing the tests that will be
	run."""

        # Initialize the base class.
        Target.__init__(self, name, group, concurrency, properties,
                        database)


        # Create a lock to guard all accesses to __ready_threads.
        self.__lock = Lock()


    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""

        # Acquire the lock.  (Otherwise, a thread that terminates
        # right as we are checking for idleness may alter
        # __ready_threads.)
        self.__lock.acquire()
        
        # This target is idle if there are any ready threads.
        if self.__ready_threads:
            idle=1
        else:
            idle=0

        # Release the lock.
        self.__lock.release()

        return idle


    def Start(self, response_queue):
        """Start the target.
        
        'response_queue' -- The 'Queue' in which the results of test
        executions are placed."""

        Target.Start(self, response_queue)
        
        # Build the threads.
        self.__threads = []
        for i in xrange(0, self.GetConcurrency()):
	    # Create the new thread.
	    thread = LocalThread(self)
	    # Start the thread.
	    thread.start()
	    # Remember the thread.
            self.__threads.append(thread)

        # Initially, all threads are ready.
        self.__ready_threads = self.__threads[:]
        self.__command_queue = []
        

    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used."""

        # Send each thread a "quit" command.
        for thread in self.__threads:
	    thread.Stop()
        # Now wait for each thread process to finish.
        for thread in self.__threads:
	    thread.join()


    def RunTest(self, test_id, context):
        """Run the test given by 'test_id'.

        'test_id' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test."""

        self.__lock.acquire()
        thread = self.__ready_threads.pop(0)
        self.__lock.release()
        thread.RunTest(test_id, context)
            

    def SetUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource."""

        self.__lock.acquire()
        thread = self.__ready_threads.pop(0)
        self.__lock.release()
        thread.SetUpResource(resource_id, context)


    def CleanUpResource(self, resource_id, context):
        """Set up the resource given by 'resource_id'.

        'resource_id' -- The name of the resource to be set up.

        'context' -- The 'Context' in which to run the resource.

        Derived classes must override this method."""

        self.__lock.acquire()
        thread = self.__ready_threads.pop(0)
        self.__lock.release()
        thread.CleanUpResource(resource_id, context)


    def NoteIdleThread(self, thread):
        """Note that 'thread' has become idle.

        This method is called by the thread when it has completed a
        task."""

        # Acquire the lock.  (Otherwise, IsIdle might be called right
        # as we are accessing __ready_threads.)
        self.__lock.acquire()

        # Now that we have acquired the lock make sure that we release
        # it, even if an exception occurs.
        try:
            assert thread not in self.__ready_threads
            self.__ready_threads.append(thread)
        finally:
            # Release the lock.
            self.__lock.release()


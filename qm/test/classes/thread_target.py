########################################################################
#
# File:   thread_target.py
# Author: Mark Mitchell
# Date:   10/30/2001
#
# Contents:
#   QMTest ThreadTarget class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from   qm.test.base import *
from   qm.test.command_thread import *
from   qm.test.target import *
import Queue
from   threading import *

########################################################################
# classes
########################################################################

class LocalThread(CommandThread):
    """A 'LocalThread' executes commands locally."""

    def _RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The name of the test to be run.

        'context' -- The 'Context' in which to run the test."""

        self.GetTarget()._RunTest(descriptor, context)
        

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

        # Create a lock to guard accesses to __ready_threads.
        self.__ready_threads_lock = Lock()
        # Create a condition variable to guard accesses to the
        # available resources table.
        self.__resources_condition = Condition()
        

    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it."""

        # Acquire the lock.  (Otherwise, a thread that terminates
        # right as we are checking for idleness may alter
        # __ready_threads.)
        self.__ready_threads_lock.acquire()
        
        # This target is idle if there are any ready threads.
        if self.__ready_threads:
            idle=1
        else:
            idle=0

        # Release the lock.
        self.__ready_threads_lock.release()

        return idle


    def Start(self, response_queue, engine=None):
        """Start the target.
        
        'response_queue' -- The 'Queue' in which the results of test
        executions are placed.

        'engine' -- The 'ExecutionEngine' that is starting the target,
        or 'None' if this target is being started without an
        'ExecutionEngine'."""

        Target.Start(self, response_queue, engine)
        
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
        

    def Stop(self):
        """Stop the target.

        postconditions -- The target may no longer be used."""

        Target.Stop(self)
        
        # Send each thread a "quit" command.
        for thread in self.__threads:
	    thread.Stop()
        # Now wait for each thread process to finish.
        for thread in self.__threads:
	    thread.join()


    def RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test.

        Derived classes may override this method."""

        self.__ready_threads_lock.acquire()

        # The execution engine should never be trying to run a test
        # when the target is not already idle.
        assert self.__ready_threads
        # Pick an idle thread to run the test.
        thread = self.__ready_threads.pop(0)
        
        self.__ready_threads_lock.release()

        thread.RunTest(descriptor, context)
            

    def _RunTest(self, descriptor, context):
        """Run the test given by 'descriptor'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test.

        This method will be called from the thread that has been
        assigned the test."""

        Target.RunTest(self, descriptor, context)


    def _RecordResult(self, result):
        """Record the 'result'.

        'result' -- A 'Result' of a test or resource execution."""

        # If this is a test result, then this thread has finished all
        # of its work.
        if result.GetKind() == Result.TEST:
            self._NoteIdleThread()
        # Pass the result back to the execution engine.
        Target._RecordResult(self, result)
        
            
    def _BeginResourceSetUp(self, resource_name):
        """Begin setting up the indicated resource.

        'resource_name' -- A string naming a resource.

        returns -- If the resource has already been set up, returns a
        tuple '(outcome, map)'.  The 'outcome' indicates the outcome
        that resulted when the resource was set up; the 'map' is a map
        from strings to strings indicating properties added by this
        resource.  Otherwise, returns 'None', but marks the resource
        as in the process of being set up; it is the caller's
        responsibility to finish setting it up by calling
        '_FinishResourceSetUp'."""

        # Acquire the lock.
        self.__resources_condition.acquire()
        try:
            # Loop until either we are assigned to set up the resource
            # or until some other thread has finished setting it up.
            while 1:
                rop = Target._BeginResourceSetUp(self, resource_name)
                # If this is the first thread to call _BeginResourceSetUp
                # for this thread will set up the resource.
                if not rop:
                    return rop
                # If this resource has already been set up, we do not
                # need to do anything more.
                if rop[0]:
                    return rop
                # Otherwise, some other thread is in the process of
                # setting up this resource so we just wait for it to
                # finish its job.
                self.__resources_condition.wait()
        finally:
            # Release the lock.
            self.__resources_condition.release()
                

    def _FinishResourceSetUp(self, resource, result):
        """Finish setting up a resource.

        'resource' -- The 'Resource' itself.

        'result' -- The 'Result' associated with setting up the
        resource.

        returns -- A tuple of the same form as is returned by
        '_BeginResourceSetUp' with the resource has already been set
        up."""

        # Acquire the lock.
        self.__resources_condition.acquire()
        # Record the fact that the resource is set up.
        rop = Target._FinishResourceSetUp(self, resource, result)
        # Tell all the other threads that the resource has been set
        # up.
        self.__resources_condition.notifyAll()
        # Release the lock.
        self.__resources_condition.release()

        return rop

        
    def _NoteIdleThread(self):
        """Note that the current thread.

        This method is called by the thread when it has completed a
        task."""

        # Acquire the lock.  (Otherwise, IsIdle might be called right
        # as we are accessing __ready_threads.)
        self.__ready_threads_lock.acquire()

        # Now that we have acquired the lock make sure that we release
        # it, even if an exception occurs.
        try:
            thread = currentThread()
            assert thread not in self.__ready_threads
            self.__ready_threads.append(thread)
        finally:
            # Release the lock.
            self.__ready_threads_lock.release()

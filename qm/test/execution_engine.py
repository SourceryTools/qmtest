########################################################################
#
# File:   execution_engine.py
# Author: Mark Mitchell
# Date:   01/02/2002
#
# Contents:
#   ExecutionEngine
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import os
import qm.common
import qm.queue
from   qm.test.base import *
import qm.test.cmdline
import qm.test.database
from   qm.test.context import *
import qm.xmlutil
from   result import *
import select
import sys
import time

########################################################################
# Classes
########################################################################

class TerminationRequested(qm.common.QMException):
    """A target requested termination of the test loop."""
    
    pass



class ExecutionEngine:
    """A 'ExecutionEngine' executes tests.

    A 'ExecutionEngine' object handles the execution of a collection
    of tests.

    This class schedules the tests across one or more targets.

    The shedule is determined dynamically as the tests are executed
    based on which targets are idle and which are not.  Therefore, the
    testing load should be reasonably well balanced, even across a
    heterogeneous network of testing machines."""


    class __TestStatus(object):
        """A '__TestStatus' indicates whether or not a test has been run.

        The 'outcome' slot indicates whether the test has not be queued so
        that it can be run, has completed, or has not been processed at all.

        If there are tests that have this test as a prerequisite, they are
        recorded in the 'dependants' slot.

        Ever test passes through the following states, in the following
        order:

        1. Initial

           A test in this state has not yet been processed.  In this state,
           the 'outcome' slot is 'None'.

        2. Queued

           A test in this state has been placed on the stack of tests
           waiting to run.  In this state, the 'outcome' slot is
           'QUEUED'.  Such a test may be waiting for prerequisites to
           complete before it can run.

        3. Ready

           A test in this state is ready to run.  All prerequisites have
           completed, and their outcomes were as expected.  In this
           state, the 'outcome' slot is 'READY'.

        4. Finished

           A test in this state has finished running.  In this state, the
           'outcome' slot is one of the 'Result.outcomes'.

        The only exception to this order is that when an error is noted
        (like a failure to load a test from the database, or a
        prerequisite has an unexpected outcome) a test may jump to the
        "finished" state without passing through intermediate states."""

        __slots__ = "outcome", "dependants"

        QUEUED = "QUEUED"
        READY = "READY"

        def __init__(self):

            self.outcome = None
            self.dependants = None


        def GetState(self):
            """Return the state of this test.

            returns -- The state of this test, using the representation
            documented above."""
            
            return self.outcome
        
        
        def NoteQueued(self):
            """Place the test into the "queued" state."""

            assert self.outcome is None
            self.outcome = self.QUEUED


        def HasBeenQueued(self):
            """Returns true if the test was ever queued.

            returns -- True if the test has ever been on the queue.
            Such a test may be ready to run, or may in fact have already
            run to completion."""

            return self.outcome == self.QUEUED or self.HasBeenReady()


        def NoteReady(self):
            """Place the test into the "ready" state."""

            assert self.outcome is self.QUEUED
            self.outcome = self.READY
            

        def HasBeenReady(self):
            """Returns true if the test was ever ready.

            returns -- True if the test was every ready to run.  Such a
            test may have already run to completion."""

            return self.outcome == self.READY or self.IsFinished()


        def IsFinished(self):
            """Returns true if the test is in the "finished" state.

            returns -- True if this test is in the "finished" state."""

            return not (self.outcome is None
                        or self.outcome is self.READY
                        or self.outcome is self.QUEUED)


        def NoteDependant(self, test_id):
            """Note that 'test_id' depends on 'self'.

            'test_id' -- The name of a test.  That test has this test as a
            prerequisite."""

            if self.dependants is None:
                self.dependants = [test_id]
            else:
                self.dependants.append(test_id)


    # Every target is in one of three states: busy, idle, or starving.
    # A busy target is running tests, an idle target is ready to run
    # tests, and a starving target is ready to run tests, but no tests
    # are available for it to run.
    __TARGET_IDLE = "IDLE"
    __TARGET_BUSY = "BUSY"
    __TARGET_STARVING = "STARVING"


    def __init__(self,
                 database,
                 test_ids,
                 context,
                 targets,
                 result_streams = None,
                 expectations = None):
        """Set up a test run.

        'database' -- The 'Database' containing the tests that will be
        run.
        
        'test_ids' -- A sequence of IDs of tests to run.  Where
        possible, the tests are started in the order specified.
        
        'context' -- The context object to use when running tests.

        'targets' -- A sequence of 'Target' objects, representing
        targets on which tests may be run.

        'result_streams' -- A sequence of 'ResultStream' objects.  Each
        stream will be provided with results as they are available.

        'expectations' -- If not 'None', a dictionary mapping test IDs
        to expected outcomes."""

        self.__database = database
        self.__test_ids = test_ids
        self.__context = context
        self.__targets = targets
        if result_streams is not None:
            self.__result_streams = result_streams
        else:
            self.__result_streams = []
        if expectations is not None:
            self.__expectations = expectations
        else:
            self.__expectations = {}
            
        # There are no input handlers.
        self.__input_handlers = {}
        
        # There are no responses from the targets yet.
        self.__response_queue = qm.queue.Queue(0)
        # There no pending or ready tests yet.
        self.__running = 0

        self.__any_unexpected_outcomes = 0
        
        # Termination has not yet been requested.
        self.__terminated = 0
        

    def RequestTermination(self):
        """Request that the execution engine stop executing tests.

        Request that the execution thread be terminated.  Termination
        may take some time; tests that are already running will continue
        to run, for example."""

        self._Trace("Test loop termination requested.")
        self.__terminated = 1


    def _IsTerminationRequested(self):
        """Returns true if termination has been requested.

        returns -- True if no further tests should be executed.  If the
        value is -1, the execution engine should simply terminate
        gracefully."""

        return self.__terminated
    

    def Run(self):
        """Run the tests.

        This method runs the tests specified in the __init__
        function.

        returns -- True if any tests had unexpected outcomes."""

        # Write out run metadata.
        self._WriteInitialAnnotations()

        # Start all of the targets.
        for target in self.__targets:
            target.Start(self.__response_queue, self)

        # Run all of the tests.
        self._Trace("Starting test loop")
        try:
            try:
                self._RunTests()
            except:
                self._Trace("Test loop exited with exception: %s"
                            % str(sys.exc_info()))
                for rs in self.__result_streams:
                    rs.WriteAnnotation("qmtest.run.aborted", "true")
                raise
        finally:
            self._Trace("Test loop finished.")

            # Stop the targets.
            self._Trace("Stopping targets.")
            for target in self.__targets:
                target.Stop()

            # Read responses until there are no more.
            self._Trace("Checking for final responses.")
            while self.__CheckForResponse(wait=0):
                pass
            
            # Let all of the result streams know that the test run is
            # complete.
            end_time_str = qm.common.format_time_iso()
            for rs in self.__result_streams:
                rs.WriteAnnotation("qmtest.run.end_time", end_time_str)
                rs.Summarize()

        return self.__any_unexpected_outcomes


    def AddInputHandler(self, fd, function):
        """Add an input handler for 'fd'.

        'fd' -- A file descriptor, open for reading.

        'function' -- A callable object taking a single parameter.

        The execution engine will periodically monitor 'fd'.  When input
        is available, it will call 'function' passing it 'fd'."""

        self.__input_handlers[fd] = function
        

    def _RunTests(self):

        num_tests = len(self.__test_ids)

        # No tests have been started yet.
        self.__num_tests_started = 0

        self.__tests_iterator = iter(self.__test_ids)

        # A map from the tests we are supposed to run to their current
        # status.
        self.__statuses = {}
        for id in self.__test_ids:
            self.__statuses[id] = self.__TestStatus()

        # A stack of tests.  If a test has prerequisites, the
        # prerequisites will appear nearer to the top of the stack.
        self.__test_stack = []
        # A hash-table giving the names of the tests presently on the
        # stack.  The names are the keys; the values are unused.
        self.__ids_on_stack = {}

        # All targets are initially idle.
        self.__target_state = {}
        for target in self.__targets:
            self.__target_state[target] = self.__TARGET_IDLE
        self.__has_idle_targets = 1
        
        # Figure out what target groups are available.
        self.__target_groups = {}
        for target in self.__targets:
            self.__target_groups[target.GetGroup()] = None
        self.__target_groups = self.__target_groups.keys()
        
        # A hash-table indicating whether or not a particular target
        # pattern is matched by any of our targets.
        self.__pattern_ok = {}
        # A map from target groups to patterns satisfied by the group.
        self.__patterns = {}
        # A map from target patterns to lists of test descriptors ready
        # to run.
        self.__target_pattern_queues = {}
        
        while self.__num_tests_started < num_tests:
            # If the user interrupted QMTest, stop executing tests.
            if self._IsTerminationRequested():
                self._Trace("Terminating test loop as requested.")
                raise TerminationRequested, "Termination requested."

            # Process any responses and update the count of idle targets.
            while self.__CheckForResponse(wait=0):
                pass

            # Now look for idle targets.
            if not self.__has_idle_targets:
                # Block until one of the running tests completes.
                self._Trace("All targets are busy -- waiting.")
                self.__CheckForResponse(wait=1)
                self._Trace("Response received.")
                continue

            # Go through each of the idle targets, finding work for it
            # to do.
            self.__has_idle_targets = 0
            for target in self.__targets:
                if self.__target_state[target] != self.__TARGET_IDLE:
                    continue
                # Try to find work for the target.  If there is no
                # available work, the target is starving.
                if not self.__FeedTarget(target):
                    self.__target_state[target] = self.__TARGET_STARVING
                else:
                    # We gave the target some work, which may have
                    # changed its idle state, so update the status.
                    if target.IsIdle():
                        self.__target_state[target] = self.__TARGET_IDLE
                        self.__has_idle_targets = 1
                    else:
                        self.__target_state[target] = self.__TARGET_BUSY

        # Now every test that we're going to start has started; we just
        # have wait for them all to finish.
        self._Trace("Waiting for remaining tests to finish.")
        while self.__running:
            self.__CheckForResponse(wait=1)


    def __FeedTarget(self, target):
        """Run a test on 'target'

        'target' -- The 'Target' on which the test should be run.

        returns -- True, iff a test could be found to run on 'target'.
        False otherwise."""

        self._Trace("Looking for a test for target %s" % target.GetName())

        # See if there is already a ready-to-run test for this target.
        for pattern in self.__patterns.get(target.GetGroup(), []):
            tests = self.__target_pattern_queues.get(pattern, [])
            if tests:
                descriptor = tests.pop()
                break
        else:
            # There was no ready-to-run test queued, so try to find one
            # another one.
            descriptor = self.__FindRunnableTest(target)
            if descriptor is None:
                # There really are no more tests ready to run.
                return 0
                
        target_name = target.GetName()
        test_id = descriptor.GetId()
        self._Trace("Running %s on %s" % (test_id, target_name))
        assert self.__statuses[test_id].GetState() == self.__TestStatus.READY
        self.__num_tests_started += 1
        self.__running += 1
        target.RunTest(descriptor, self.__context)
        return 1


    def __FindRunnableTest(self, target):
        """Return a test that is ready to run.

        'target' -- The 'Target' on which the test will run.
        
        returns -- the 'TestDescriptor' for the next available ready
        test, or 'None' if no test could be found that will run on
        'target'.

        If a test with unsatisfied prerequisites is encountered, the
        test will be pushed on the stack and the prerequisites processed
        recursively."""

        while 1:
            if not self.__test_stack:
                # We ran out of prerequisite tests, so pull a new one
                # off the user's list.
                try:
                    test_id = self.__tests_iterator.next()
                except StopIteration:
                    # We're entirely out of fresh tests; give up.
                    return None
                if self.__statuses[test_id].HasBeenQueued():
                    # This test has already been handled (probably
                    # because it's a prereq of a test already seen).
                    continue
                # Try to add the new test to the stack.
                if not self.__AddTestToStack(test_id):
                    # If that failed, look for another test.
                    continue
                self._Trace("Added new test %s to stack" % test_id)

            descriptor, prereqs = self.__test_stack[-1]
            # First look at the listed prereqs.
            if prereqs:
                new_test_id = prereqs.pop()
                # We must filter tests that are already in the process
                # here; if we were to do it earlier, we would be in
                # danger of being confused by dependency graphs like
                # A->B, A->C, B->C, where we can't know ahead of time
                # that A's dependence on C is unnecessary.
                if self.__statuses[new_test_id].HasBeenQueued():
                    # This one is already in process.  This might
                    # indicate a dependency cycle, so check for that
                    # now.
                    if new_test_id in self.__ids_on_stack:
                        self._Trace("Cycle detected (%s)"
                                    % (new_test_id,))
                        self.__AddUntestedResult \
                                 (new_test_id,
                                  qm.message("dependency cycle"))
                    continue
                else:
                    self.__AddTestToStack(new_test_id)
                    continue
            else:
                # Remove the test from the stack.
                test_id = descriptor.GetId()
                del self.__ids_on_stack[test_id]
                self.__test_stack.pop()

                # Check to see if the test is already ready to run, or
                # has completed.  The first case occurs when the test
                # has prerequisites that have completed after it was
                # placed on the stack; the second occurs when a test
                # is marked UNTESTED after a cycle is detected.
                if self.__statuses[test_id].HasBeenReady():
                    continue

                # Now check the prerequisites.
                prereqs = self.__GetPendingPrerequisites(descriptor)
                # If one of the prerequisites failed, the test will have
                # been marked UNTESTED.  Keep looking for a runnable
                # test.
                if prereqs is None:
                    continue
                # If there are prerequisites, request notification when
                # they have completed.
                if prereqs:
                    for p in prereqs:
                        self.__statuses[p].NoteDependant(test_id)
                    # Keep looking for a runnable test.                        
                    continue

                # This test is ready to run.  See if it can run on
                # target.
                if not target.IsInGroup(descriptor.GetTargetGroup()):
                    # This test can't be run on this target, but it can be
                    # run on another target.
                    self.__AddToTargetPatternQueue(descriptor)
                    continue
                    
                self.__statuses[descriptor.GetId()].NoteReady()
                return descriptor


    def __AddTestToStack(self, test_id):
        """Adds 'test_id' to the stack of current tests.

        returns -- True if the test was added to the stack; false if the
        test could not be loaded.  In the latter case, an 'UNTESTED'
        result is recorded for the test."""
        
        self._Trace("Trying to add %s to stack" % test_id)

        # Update test status.
        self.__statuses[test_id].NoteQueued()

        # Load the descriptor.
        descriptor = self.__GetTestDescriptor(test_id)
        if not descriptor:
            return 0

        # Ignore prerequisites that are not going to be run at all.
        prereqs_iter = iter(descriptor.GetPrerequisites())
        relevant_prereqs = filter(self.__statuses.has_key, prereqs_iter)

        # Store the test on the stack.
        self.__ids_on_stack[test_id] = None
        self.__test_stack.append((descriptor, relevant_prereqs))

        return 1

        
    def __AddToTargetPatternQueue(self, descriptor):
        """A a test to the appropriate target pattern queue.

        'descriptor' -- A 'TestDescriptor'.

        Adds the test to the target pattern queue indicated in the
        descriptor."""

        test_id = descriptor.GetId()
        self.__statuses[test_id].NoteReady()

        pattern = descriptor.GetTargetGroup()

        # If we have not already determined whether or not this pattern
        # matches any of the targets, do so now.
        if not self.__pattern_ok.has_key(pattern):
            self.__pattern_ok[pattern] = 0
            for group in self.__target_groups:
                if re.match(pattern, group):
                    self.__pattern_ok[pattern] = 1
                    patterns = self.__patterns.setdefault(group, [])
                    patterns.append(pattern)
        # If none of the targets can run this test, mark it untested.
        if not self.__pattern_ok[pattern]:
            self.__AddUntestedResult(test_id,
                                     "No target matching %s." % pattern)
            return

        queue = self.__target_pattern_queues.setdefault(pattern, [])
        queue.append(descriptor)


    def __GetPendingPrerequisites(self, descriptor):
        """Return pending prerequisite tests for 'descriptor'.

        'descriptor' -- A 'TestDescriptor'.
        
        returns -- A list of prerequisite test ids that have to
        complete, or 'None' if one of the prerequisites had an
        unexpected outcome."""

        needed = []

        prereqs = descriptor.GetPrerequisites()
        for prereq_id, outcome in prereqs.iteritems():
            try:
                prereq_status = self.__statuses[prereq_id]
            except KeyError:
                # This prerequisite is not being run at all, so skip
                # it.
                continue

            if prereq_status.IsFinished():
                prereq_outcome = prereq_status.outcome
                if outcome != prereq_outcome:
                    # Failed prerequisite.
                    self.__AddUntestedResult \
                        (descriptor.GetId(),
                         qm.message("failed prerequisite"),
                         {'qmtest.prequisite': prereq_id,
                          'qmtest.outcome': prereq_outcome,
                          'qmtest.expected_outcome': outcome })
                    return None
            else:
                # This prerequisite has not yet completed.
                needed.append(prereq_id)

        return needed


    def __AddResult(self, result):
        """Report the result of running a test or resource.
        
        'result' -- A 'Result' object representing the result of running
        a test or resource."""

        # Output a trace message.
        id = result.GetId()
        self._Trace("Recording %s result for %s." % (result.GetKind(), id))

        # Find the target with the name indicated in the result.
        if result.has_key(Result.TARGET):
            for target in self.__targets:
                if target.GetName() == result[Result.TARGET]:
                    break
            else:
                assert 0, ("No target %s exists (test id: %s)"
                           % (result[Result.TARGET], id))
        else:
            # Not all results will have associated targets.  If the
            # test was not run at all, there will be no associated
            # target.
            target = None

        # Having no target is a rare occurrence; output a trace message.
        if not target:
            self._Trace("No target for %s." % id)

        # This target might now be idle.
        if (target and target.IsIdle()):
            # Output a trace message.
            self._Trace("Target is now idle.\n")
            self.__target_state[target] = self.__TARGET_IDLE
            self.__has_idle_targets = 1
            
        # Only tests have expectations or scheduling dependencies.
        if result.GetKind() == Result.TEST:
            # Record the outcome for this test.
            test_status = self.__statuses[id]
            test_status.outcome = result.GetOutcome()

            # If there were tests waiting for this one to complete, they
            # may now be ready to execute.
            if test_status.dependants:
                for dependant in test_status.dependants:
                    if not self.__statuses[dependant].HasBeenReady():
                        descriptor = self.__GetTestDescriptor(dependant)
                        if not descriptor:
                            continue
                        prereqs = self.__GetPendingPrerequisites(descriptor)
                        if prereqs is None:
                            continue
                        if not prereqs:
                            # All prerequisites ran and were satisfied.
                            # This test can now run.
                            self.__AddToTargetPatternQueue(descriptor)
                # Free the memory consumed by the list.
                del test_status.dependants

            # Check for unexpected outcomes.
            if result.GetKind() == Result.TEST:
                if (self.__expectations.get(id, Result.PASS)
                    != result.GetOutcome()):
                    self.__any_unexpected_outcomes = 1

            # Any targets that were starving may now be able to find
            # work.
            for t in self.__targets:
                if self.__target_state[t] == self.__TARGET_STARVING:
                    self.__target_state[t] = self.__TARGET_IDLE
            
        # Output a trace message.
        self._Trace("Writing result for %s to streams." % id)

        # Report the result.
        for rs in self.__result_streams:
            rs.WriteResult(result)


    def __CheckForResponse(self, wait):
        """See if any of the targets have completed a task.

        'wait' -- If false, this function returns immediately if there
        is no available response.  If 'wait' is true, this function
        continues to wait until a response is available.

        returns -- True iff a response was received."""

        while 1:
            try:
                # Read a reply from the response_queue.
                result = self.__response_queue.get(0)
                # Output a trace message.
                self._Trace("Got %s result for %s from queue."
                             % (result.GetKind(), result.GetId()))
                # Record the result.
                self.__AddResult(result)
                if result.GetKind() == Result.TEST:
                    assert self.__running > 0
                    self.__running -= 1
                # Output a trace message.
                self._Trace("Recorded result.")
                return result
            except qm.queue.Empty:
                # If there is nothing in the queue, then this exception will
                # be thrown.
                if not wait:
                    return None
                
                # Give other threads and processes a chance to run.
                if self.__input_handlers:
                    # See if there is any input that might indicate that
                    # work has been done.
                    fds = self.__input_handlers.keys()
                    fds = select.select (fds, [], [], 0.1)[0]
                    for fd in fds:
                        self.__input_handlers[fd](fd)
                else:
                    time.sleep(0.1)
                
                # There may be a response now.
                continue


    def __AddUntestedResult(self, test_name, cause, annotations={},
                            exc_info = None):
        """Add a 'Result' indicating that 'test_name' was not run.

        'test_name' -- The label for the test that could not be run.

        'cause' -- A string explaining why the test could not be run.

        'annotations' -- A map from strings to strings giving
        additional annotations for the result.

        'exc_info' -- If this test could not be tested due to a thrown
        exception, 'exc_info' is the result of 'sys.exc_info()' when the
        exception was caught.  'None' otherwise."""

        # Remember that this test was started.
        self.__num_tests_started += 1

        # Create and record the result.
        result = Result(Result.TEST, test_name, annotations = annotations)
        if exc_info:
            result.NoteException(exc_info, cause, Result.UNTESTED)
        else:
            result.SetOutcome(Result.UNTESTED, cause)
        self.__AddResult(result)


    ### Utility methods.

    def __GetTestDescriptor(self, test_id):
        """Return the 'TestDescriptor' for 'test_id'.

        returns -- The 'TestDescriptor' for 'test_id', or 'None' if the
        descriptor could not be loaded.

        If the database cannot load the descriptor, an 'UNTESTED' result
        is recorded for 'test_id'."""

        try:
            return self.__database.GetTest(test_id)
        except:
            self.__AddUntestedResult(test_id,
                                     "Could not load test.",
                                     exc_info = sys.exc_info())
            return None
        
        
    def _Trace(self, message):
        """Write a trace 'message'.

        'message' -- A string to be output as a trace message."""

        if __debug__:
            tracer = qm.test.cmdline.get_qmtest().GetTracer()
            tracer.Write(message, "exec")

    
    def _WriteInitialAnnotations(self):

        # Calculate annotations.
        start_time_str = qm.common.format_time_iso()

        try:
            username = qm.common.get_username()
        except:
            username = None

        try:
            uname = " ".join(os.uname())
        except:
            uname = None

        # Write them.
        for rs in self.__result_streams:
            rs.WriteAllAnnotations(self.__context)
            rs.WriteAnnotation("qmtest.run.start_time", start_time_str)
            if username is not None:
                rs.WriteAnnotation("qmtest.run.user", username)
            rs.WriteAnnotation("qmtest.run.version", qm.version)
            rs.WriteAnnotation("qmtest.run.uname", uname)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

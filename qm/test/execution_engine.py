########################################################################
#
# File:   execution_engine.py
# Author: Mark Mitchell
# Date:   01/02/2002
#
# Contents:
#   ExecutionEngine
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
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
from   qm.test.context import *
import qm.xmlutil
from   result import *
import sys

########################################################################
# Classes
########################################################################

class ExecutionEngine:
    """A 'ExecutionEngine' executes tests.

    A 'ExecutionEngine' object handles the execution of a collection
    of tests.

    This class schedules the tests, plus the setup and cleanup of any
    resources they require, across one or more targets.

    The shedule is determined dynamically as the tests are executed
    based on which targets are idle and which are not.  Therefore, the
    testing load should be reasonably well balanced, even across a
    heterogeneous network of testing machines."""
    
    def __init__(self,
                 database,
                 test_ids,
                 context,
                 targets,
                 result_streams = None):
        """Set up a test run.

        'database' -- The 'Database' containing the tests that will be
        run.
        
        'test_ids' -- A sequence of IDs of tests to run.  Where
        possible, the tests are started in the order specified.

        'context' -- The context object to use when running tests.

        'targets' -- A sequence of 'Target' objects, representing
        targets on which tests may be run.

        'result_streams' -- A sequence of 'ResultStream' objects.  Each
        stream will be provided with results as they are available."""

        self.__database = database
        self.__test_ids = test_ids
        self.__context = context
        self.__targets = targets
        if result_streams is not None:
            self.__result_streams = result_streams
        else:
            self.__result_streams = []
        
        # All of the targets are idle at first.
        self.__idle_targets = targets[:]
        # There are no responses from the targets yet.
        self.__response_queue = qm.queue.Queue(0)
        # There no pending or ready tests yet.
        self.__pending = []
        self.__ready = []

        # The descriptor graph has not yet been created.
        self.__descriptors = {}
        self.__descriptor_graph = {}
        
        # There are no results yet.
        self.__test_results = {}
        self.__resource_results = []

        # Termination has not yet been requested.
        self.__terminated = 0
        

    def RequestTermination(self):
        """Request termination.

        Request that the execution thread be terminated.  This may
        take some time; tests that are already running will continue
        to run, for example."""

        self.__terminated = 1
        
        
    def IsTerminationRequested(self):
        """Returns true if termination has been requested.

        return -- True if Terminate has been called."""

        return self.__terminated
    

    def Run(self):
        """Run the tests.

        This method runs the tests specified in the __init__
        function."""

        # Start all of the targets.
        for target in self.__targets:
            target.Start(self.__response_queue, self)

        # Run all of the tests.
        try:
            self._RunTests()
        finally:
            # Stop the targets.
            for target in self.__targets:
                target.Stop()

            # Read responses until there are no more.
            while self._CheckForResponse(wait=0):
                pass
            
            # Let all of the result streams know that the test run is
            # complete.
            for rs in self.__result_streams:
                rs.Summarize()


    def _RunTests(self):
        """Run all of the tests.

        This function assumes that the targets have already been
        started."""

        # Create a directed graph where each node is a pair
        # (descriptor, count).  There is an edge from one node
        # to another if the first node is a prerequisite for the
        # second.  Begin by creating the nodes of the graph.
        for id in self.__test_ids:
            try:
                descriptor = self.__database.GetTest(id)
                self.__descriptors[id] = descriptor
                self.__descriptor_graph[descriptor] = [0, []]
            except:
                result = Result(Result.TEST, id, self.__context)
                result.NoteException(cause = "Could not load test.",
                                     outcome = Result.UNTESTED)
                self._AddResult(result)
                
        # Create the edges.
        for descriptor in self.__descriptors.values():
            prereqs = descriptor.GetPrerequisites()
            if prereqs:
                for (prereq_id, outcome) in prereqs.items():
                    prereq_desc = self.__descriptors[prereq_id]
                    self.__descriptor_graph[prereq_desc][1] \
                        .append((descriptor, outcome))
                self.__descriptor_graph[descriptor][0] = len(prereqs)
            else:
                # A node with no prerequisites is ready.
                self.__ready.append(descriptor)

        # Iterate until there are no more tests to run.
        self.__pending = self.__descriptors.values()
        while ((self.__pending or self.__ready)
               and not self.IsTerminationRequested()):
            # If there are no idle targets, block until we get a
            # response.  There is nothing constructive we can do.
            idle_targets = self.__idle_targets
            if not idle_targets:
                if __debug__:
                    self._Trace("All targets are idle -- waiting.")
                # Read a reply from the response_queue.
                self._CheckForResponse(wait=1)
                if __debug__:
                    self._Trace("Response received.")
                # Keep going.
                continue

            # There is at least one idle target.  Try to find something
            # that it can do.
            wait = 1
            for descriptor in self.__ready:
                for target in idle_targets:
                    if target.IsInGroup(descriptor.GetTargetGroup()):
                        # This test can be run on this target.  Remove
                        # it from the ready list.
                        self.__ready.remove(descriptor)
                        # And from the pending list.
                        self.__pending.remove(descriptor)
                        # Output a trace message.
                        if __debug__:
                            self._Trace(("About to run %s."
                                         % descriptor.GetId()))
                        # Run it.
                        target.RunTest(descriptor, self.__context)
                        # If the target is no longer idle, remove it
                        # from the idle_targets list.
                        if not target.IsIdle():
                            if __debug__:
                                self._Trace("Target is no longer idle.")
                            self.__idle_targets.remove(target)
                        else:
                            if __debug__:
                                self._Trace("Target is still idle.")
                        # We have done something useful on this
                        # iteration.
                        wait = 0
                        break

                if not wait:
                    break

            # Output a trace message.
            if __debug__:
                self._Trace("About to check for a response in %s mode."
                            % ((wait and "blocking") or "nonblocking"))
                    
            # See if any targets have finished their assignments.  If
            # we did not schedule any additional work during this
            # iteration of the loop, there's no point in continuing
            # until some target finishes what its doing.
            self._CheckForResponse(wait=wait)

            # Output a trace message.
            if __debug__:
                self._Trace("Done checking.")

        # Any tests that are still pending are untested, unless there
        # has been an explicit request that we exit immediately.
        if not self.IsTerminationRequested():
            for descriptor in self.__pending:
                self._AddUntestedResult(descriptor.GetId(),
                                        qm.message("execution terminated"))


    def _CheckForResponse(self, wait):
        """See if any of the targets have completed a task.

        'wait' -- If 1, block until a response is available.  If 0,
        return immediately if there is no available response.

        returns -- True iff a response was received."""

        # Read a reply from the response_queue.
        try:
            result = self.__response_queue.get(wait)
            # Output a trace message.
            if __debug__:
                self._Trace(("Got response for %s from queue."
                             % result.GetId()))
            # Handle it.
            self._AddResult(result)
            # Output a trace message.
            if __debug__:
                self._Trace("Recorded result.")
            # If this was a test result, there may be other tests that
            # are now eligible to run.
            if result.GetKind() == Result.TEST:
                # Get the descriptor for this test.
                descriptor = self.__descriptors[result.GetId()]
                # Get the graph node corresponding to this test.
                node = self.__descriptor_graph[descriptor]
                # Iterate through each of the dependent tests.
                for (d, outcome) in node[1]:
                    # Find the node for the dependent test.
                    n = self.__descriptor_graph[d]
                    # If some other prerequisite has already had
                    # an undesired outcome, there is nothing more to do.
                    if n[0] == 0:
                        continue
                    
                    # If the actual outcome is not the outcmoe that
                    # was expected, the dependent test cannot be run.
                    if result.GetOutcome() != outcome:
                        self._AddUntestedResult(
                            d.GetId(),
                            qm.message("failed prerequisite"),
                            { 'qmtest.prequisite' :
                                result.GetId(),
                              'qmtest.outcome' : 
                                result.GetOutcome(),
                              'qmtest.expected_outcome' :
                                outcome })
                        # This test will never be run.
                        n[0] = 0
                        self.__pending.remove(d)
                    else:
                        # Decrease the count associated with the node, if
                        # the test has not already been declared a failure.
                        n[0] = n[0] - 1
                        # If this was the last prerequisite, this test
                        # is now ready.
                        if n[0] == 0:
                            self.__ready.append(d)

            return result
        except qm.queue.Empty:
            # If wait is zero, and there is nothing in the queue, then
            # this exception will be thrown.  Just return.
            return None

        
    def _AddResult(self, result):
        """Report the result of running a test or resource.

        'result' -- A 'Result' object representing the result of running
        a test or resource."""

        # Output a trace message.
        if __debug__:
            self._Trace("Recording result for %s." % result.GetId())

        # Find the target with the name indicated in the result.
        if result.has_key(Result.TARGET):
            for target in self.__targets:
                if target.GetName() == result[Result.TARGET]:
                    break
        else:
            # Not all results will have associated targets.  If the
            # test was not run at all, there will be no associated
            # target.
            target = None

        # Having no target is a rare occurrence; output a trace message.
        if __debug__ and not target:
            self._Trace("No target for %s." % result.GetId())
                        
        # Store the result.
        if result.GetKind() == Result.TEST:
            self.__test_results[result.GetId()] = result
        elif result.GetKind() == Result.RESOURCE:
            self.__resource_results.append(result)
        else:
            assert 0
            
        # This target might now be idle.
        if (target and target not in self.__idle_targets
            and target.IsIdle()):
            # Output a trace message.
            if __debug__:
                self._Trace("Target is now idle.\n")
            self.__idle_targets.append(target)

        # Output a trace message.
        if __debug__:
            self._Trace("Writing result for %s to streams." % result.GetId())

        # Report the result.
        for rs in self.__result_streams:
            rs.WriteResult(result)


    def _AddUntestedResult(self, test_name, cause, annotations={}):
        """Add a 'Result' indicating that 'test_name' was not run.

        'test_name' -- The label for the test that could not be run.

        'cause' -- A string explaining why the test could not be run.

        'annotations' -- A map from strings to strings giving
        additional annotations for the result."""

        result = Result(Result.TEST, test_name, self.__context,
                        Result.UNTESTED, annotations)
        result[Result.CAUSE] = cause
        self._AddResult(result)


    def _Trace(self, message,):
        """Write a trace 'message'.

        'message' -- A string to be output as a trace message."""

        tracer = qm.test.cmdline.get_qmtest().GetTracer()
        tracer.Write(message, "exec")

    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   run.py
# Author: Alex Samuel
# Date:   2001-08-04
#
# Contents:
#   Code for coordinating the running of tests.
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

import base
import cPickle
import os
import qm.common
from   qm.test.base import *
import qm.xmlutil
import Queue
import re
from   result import *
import string
import sys
from   threading import *

########################################################################
# exceptions
########################################################################

class NoTargetForGroupError(Exception):
    """There is no target whose group matches the test's group pattern."""

    pass



class FailedResourceError(Exception):
    """A resource required for a test failed during setup.

    The exception message is the resource's ID."""

    pass



class IncorrectOutcomeError(Exception):
    """A test's prerequisite produced an incorrect outcome.

    The exception message is the prerequisite test ID."""

    pass



########################################################################
# classes
########################################################################

class TestRun:
    """A test run.

    A 'TestRun' object represents the execution of a collection of
    tests.  Generally, each invocation of QMTest results in a single
    test run, incorporating all the specified tests.

    This class schedules the tests, plus the setup and cleanup of any
    resources they require, across one or more targets.  The schedule
    follows these rules:

      * A test may be run on any target whose target group is allowed
        for the test.

      * If a test's prerequisite test is included in the test run, the
        test is not started until its prerequisite completes.  If the
        prerequisite produced the wrong outcome, the test is not run at
        all.

      * A test is not run until and unless all the resources required by
        it have been set up successfully on the same target.

      * Resources may be set up on more than one target.

      * Resources are cleaned up before the test run ends.

      * If a resource setup function fails, the resource setup is not
        attempted again, even on a different target.

      * Tests and resource functions may be run concurrently on targets
        which support that. 

      * Subject to the above rules, tests are started in the order
        specified.  They may complete in a different order, however.

    This class schedules tests and resource functions incrementally,
    using a simple greedy algorithm.

    Note that this class does not parallelize the communications with
    multiple concurrent targets and their concurrent subcomponents.  The
    'Schedule' method should be called iteratively, interleved with
    polls of the targets' IPC mechanism, to complete the schedule
    incrementally.  Each call to 'Schedule' attempts to keep all the
    targets busy, but does not necessarily schedule all tests.  When
    processing the replies from targets (handled elsewhere), call the
    'AddResult' method to accumulate results."""

    # Attributes:
    #
    # '__test_ids' -- The complete sequence of IDs of tests in the test
    # run.
    #
    # '__context' -- The 'Context' object with which to run tests and
    # resource functions.
    #
    # '__targets' -- The sequence of 'Target' objects on which to run
    # tests.
    #
    # '__test_results' -- A map from test ID to the 'Result' object for
    # that test.
    #
    # '__resource_results' -- A sequence of 'Result' objects for
    # resource functions that have been run.
    #
    # '__failed_resources' -- A map indicating resources whose setup
    # functions have failed.  The keys are IDs of failed resources; the
    # corresponding values are ignored.
    #
    # '__valid_tests' -- A map indicating tests which have been checked
    # for validity in this run; see '__ValidateTest'.  The keys are IDS
    # of tests that have been checked; the corresponding values are
    # ignored.
    #
    # '__remaining_test_ids' -- The sequence of IDs of tests that remain
    # to be run.
    #
    # '__resources' -- A representation of resources active on a given
    # target.  For each target, '__resources[target]' is a map, whose
    # keys are the IDs of resources active on the target.  For each such
    # resource, '__resources[target][resource_id]' is a map of context
    # properties added by the resource setup function.  These properties
    # are added to the contexts of tests which depend on the resource.


    def __init__(self,
                 database,
                 test_ids,
                 context,
                 targets,
                 result_streams=[]):
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
        self.__result_streams = result_streams
        
        # For each target, construct an initially empty map of resources
        # active for that target.
        self.__resources = {}
        for target in targets:
            self.__resources[target] = {}

        self.__test_results = {}
        self.__resource_results = []
        self.__failed_resources = {}
        self.__valid_tests = {}
        self.__remaining_test_ids = list(test_ids)


    def Schedule(self):
        """Schedule tests and resource functions.

        This method attempts to schedule tests and resource functions so
        that each target has something to do.  Not all tests are
        necessarily scheduled.  Call this method repeatedly, when at
        least one target has completed its work, until the return value
        is zero.

        returns -- The number of commands that have been issued to 
	targets; or zero if no more tests and resource remain."""

        database = self.__database

        # For each call, we'll maintain a list of targets which are
        # ready to accept more work.
        ready_targets = filter(lambda t: t.IsIdle(), self.__targets)

	count = 0

        if len(self.__remaining_test_ids) == 0:
            # There are no tests left to be run, so the test run is
            # almost over.  Clean up resources now.  Since we're
            # scheduling greedily, it's hard to clean up resources
            # eariler than the very end of the test run.
            for target in self.__targets:
                resources = self.__resources[target].items()
                for resource_id, properties in resources:
                    # Properties added to the context in the resource's
                    # setup function are available in the cleanup
                    # functions' context.
                    context_wrapper = \
                        base.ContextWrapper(self.__context, properties)
                    target.CleanUpResource(resource_id, context_wrapper)
		    count = count + 1

            # That's it for the test run.
            return count

        # Scan through all remaining tests, attempting to schedule each
        # on a target.
        for test_id in self.__remaining_test_ids:
            # If there are no targets ready to accept additional work,
            # stop scheduling immediately.
            if len(ready_targets) == 0:
                break

            # Load the test. 
            test = database.GetTest(test_id)
            try:
                # Is it ready to run?
                test_is_ready = self.__TestIsReady(test)

            except NoTargetForGroupError:
                # There is no target whose target group is allowable for
                # this test.  We therefore can't run this test.  Add an
                # 'UNTESTED' result for it.
                cause = qm.message("no target for group")
                group_pattern = test.GetTargetGroup()
                result = Result(test_id, Result.TEST,
                                self.__context, Result.UNTESTED,
                                { Result.CAUSE : cause,
                                  'group_pattern' : group_pattern })
                self.AddResult(result)
                self.__remaining_test_ids.remove(test_id)
                continue

            except IncorrectOutcomeError, error:
                prerequisite_id = str(error)
                # One of the test's prerequisites was run and produced
                # the incorrect outcome.  We won't run this test.  Add
                # an 'UNTESTED' result for it.
                cause = qm.message("failed prerequisite")
                prerequisite_outcome = \
                    self.__test_results[prerequisite_id].GetOutcome()
                expected_outcome = test.GetPrerequisites()[prerequisite_id]
                result = Result(test_id, Result.TEST,
                                self.__context, Result.UNTESTED,
                                { Result.CAUSE : cause,
                                  'prerequisite_id' : prerequisite_id,
                                  'prerequisite_outcome' :
                                    prerequisite_outcome,
                                  'expected_outcome' : expected_outcome })
                self.AddResult(result)
                self.__remaining_test_ids.remove(test_id)
                continue

            except FailedResourceError, error:
                resource_id = str(error)
                # One of the resources required for this test failed
                # during setup, so we can't run the test.  Add an
                # 'UNTESTED' result for it.
                cause = qm.message("failed resource")
                result = Result(test_id, Result.TEST, self.__context,
                                Result.UNTESTED)
                result[Result.CAUSE] = cause
                result['resource_id'] = resource_id
                self.AddResult(result)
                self.__remaining_test_ids.remove(test_id)
                continue

            else:
                if not test_is_ready:
                    # The test isn't ready yet.  Defer it.
                    continue

            # Determine the best available target for running this test.
            target = self.__FindBestTarget(test, ready_targets)
            if target is None:
                # None of the currently-available targets can run this
                # test.  Must be that all the targets that can are
                # currently busy.  Defer the test.
                continue

            # Even the best target may not have all the required
            # resources currently set up.  Determine whether there are
            # any resources missing.
            test_resources = test.GetResources()
            missing_resource_ids = qm.common.sequence_difference(
                test_resources, self.__resources[target].keys())
            # Are there any?
            if len(missing_resource_ids) == 0:
                # No, we have all the required resources.  Run the test
                # itself.  First, contstruct a map of additional
                # properties added to the context by all resources
                # required by this test.
                properties = {}
                for resource_id in test.GetResources():
                    resource_properties = \
                        self.__resources[target][resource_id]
                    properties.update(resource_properties)
                # These properties are made available to the test
                # through its context.
                context_wrapper = base.ContextWrapper(self.__context,
                                                      properties)
                # Run the test.
                target.RunTest(test_id, context_wrapper)
		count = count + 1
                self.__remaining_test_ids.remove(test_id)
            else:
                # Yes, there's at least one resource missing for the
                # target.  Instead of running the test, set up all the
                # missing resources.  Defer the test; it'll probably be
                # scheduled for this target later.
                for resource_id in missing_resource_ids:
                    context_wrapper = base.ContextWrapper(self.__context)
                    target.SetUpResource(resource_id, context_wrapper)
		    count = count + 1
                    if not target.IsIdle():
                        break

            # If we just gave the target enough work to keep it busy for
            # now, remove it from the list of available targets.
            if not target.IsIdle():
                ready_targets.remove(target)

        # We've scheduled as much as we can for now.
        return count


    def AddResult(self, result):
        """Report the result of running a test or resource.

        'result' -- A 'Result' object representing the result of running
        a test or resource."""

        # Store the result.
        if result.GetKind() == Result.TEST:
            self.__test_results[result.GetId()] = result
        elif result.GetKind() == Result.RESOURCE:
            self.__resource_results.append(result)

            # Extract information from the result.
            resource_id = result.GetId()
            outcome = result.GetOutcome()
            action = result["action"]
            assert action in ["setup", "cleanup"]

            # Find the target with the name indicated in the result.
            if result[Result.TARGET]:
                for target in self.__targets:
                    if target.GetName() == result[Result.TARGET]:
                        break
                        
            if action == "setup" and outcome == Result.PASS:
                # A resource has successfully been set up.  Record it as an
                # active resource for the target.  For that resource and
                # target combination, store the context properties that were
                # added by the resource setup function, so that these can be
                # made available to tests that use the resource.
                added_properties = \
                    result.GetContext().GetAddedProperties()
                self.__resources[target][resource_id] = added_properties

            elif action == "setup" and outcome != Result.PASS:
                # A resource's setup function failed.  Note this, so that
                # the resource setup is not reattempted.
                self.__failed_resources[resource_id] = None
                # Schedule the cleanup function for this resource
                # immediately. 
                context_wrapper = base.ContextWrapper(self.__context)
                target.CleanUpResource(resource_id, context_wrapper)

            elif action == "cleanup" and outcome == Result.PASS:
                # A resource has successfully been cleaned up.  Remove it
                # from the list of active resources for the target.
                del self.__resources[target][resource_id]
        else:
            assert 0
            
        # Report the result.
        self.__ReportResult(result)

    # Helper functions.

    def __ReportResult(self, result):
        """Report the 'result'.

        'result' -- A 'Result' indicating the outcome of a test or
        resource run.

        The result is provided to all of the 'ResultStream' objects."""

        for rs in self.__result_streams:
            rs.WriteResult(result)


    def __ValidateTest(self, test):
        """Make sure a test is valid for this test run.

        'test' -- The test to validate.

        raises -- 'NoTargetForGroupError' if there is no target in
        the test run whose group matches the test's group."""

        test_id = test.GetId()

        # A test needs to be checked only once per run.  If this test
        # was already checked, don't re-check it.
        if self.__valid_tests.has_key(test_id):
            return

        # Find a target in the correct group.
        group_pattern = test.GetTargetGroup()
        match = 0
        for target in self.__targets:
            if is_group_match(group_pattern, target.GetGroup()):
                # Found a match.
                match = 1
                break
        if not match:
            # No target is in a matching group.  This test can't be
            # run with the specified set of targets.
            raise NoTargetForGroupError, test_id
        
        # Mark the test as checked, so it isn't re-checked next time.
        self.__valid_tests[test_id] = None


    def __TestIsReady(self, test):
        """Check whether 'test' is ready to be run.

        'test' -- The test to check.

        returns -- True if the test is ready to run, false otherwise.
        Note that a test may be ready to run even if there is no target
        which currently has all the required resources set up.

        raises -- 'IncorrectOutcomeError' if one of the test's a
        prerequisites has already been run but produced the incorrect
        outcome.  The exception string is the ID of the prerequisite
        test.

        raises -- 'FailedResourceError' if one of the test's resources
        has failed during setup.  The exception string is the ID of the
        resource."""

        # Check the test itself.
        self.__ValidateTest(test)

        # Check resources.
        for resource_id in test.GetResources():
            if self.__failed_resources.has_key(resource_id):
                raise FailedResourceError, resource_id

        # Check prerequisites.
        prerequisite_ids = test.GetPrerequisites()
        for prerequisite_id, outcome in prerequisite_ids.items():
            if prerequisite_id not in self.__test_ids:
                # This prerequisite test is not in the test run; ignore
                # it.
                continue

            try:
                # Obtain the prerequisite's result.
                prerequisite_result = self.__test_results[prerequisite_id]
            except KeyError:
                # No result yet; the prerequisite test hasn't
                # completed.  Don't run this test yet.
                return 0

            # Did the test produce the right outcome?
            if prerequisite_result.GetOutcome() != outcome:
                raise IncorrectOutcomeError, prerequisite_id
                
            else:
                # Correct outcome.  Move on to the next prerequisite.
                continue

        # Everything is OK.
        return 1


    def __FindBestTarget(self, test, targets):
        """Determine the best target for running 'test'.

        'test' -- The 'Test' to consider.

        'targets' -- A sequence of targets from which to choose the
        best.

        returns -- The target on which to run the test."""
        
        test_resource_ids = test.GetResources()
        group_pattern = test.GetTargetGroup()

        best_target = None
        # Scan over targets to find the best one.
        for target in targets:
            # Disqualify this target if its group does not match.
            if not is_group_match(group_pattern, target.GetGroup()):
                continue
            # Count the number of resources required by the test that
            # aren't currently active on this target.
            target_resource_ids = self.__resources[target].keys()
            missing_resource_count = \
                len(qm.common.sequence_difference(target_resource_ids,
                                                  test_resource_ids))
            # Were there any?
            if missing_resource_count == 0:
                # We have all the resources we need.  This target is
                # good enough. 
                best_target = target
                break
            # Is this the best (or first) target so far?
            if best_target is None \
               or missing_resource_count < best_missing_resource_count:
                # Yes; remember it.
                best_target = target
                best_missing_resource_count = missing_resource_count

        # Return the best target we found.
        return best_target

            

########################################################################
# functions
########################################################################

def test_run(database,
             test_ids,
             context,
             targets,
             response_queue,
             result_streams=[]):
    """Perform a test run.

    This function coordinates the scheduling of tests and the IPC
    between the main thread of execution (in which this function is
    called) and subthreads (created by targets) which run the tests.

    'datbabase' -- The 'Database' containing the tests that will
    be run.
    
    'test_ids' -- The sequence of IDs of tests to include in the test
    run.

    'context' -- The 'Context' object to use when running tests and
    resource functions.

    'targets' -- A sequence of 'Target' objects on which the tests can
    be run.

    'response_queue' - The 'Queue' to which the targets will write
    results.
    
    'result_streams' -- A sequence of 'ResultStream' objects.  Each
    stream will be provided with results as they are available."""
    
    # Construct the test run.
    run = TestRun(database, test_ids, context, targets, result_streams)

    # Start all of the targets.
    for target in targets:
        target.Start()
    
    # Schedule all the tests and resource functions in the test run.
    try:
        # Schedule the first batch of work.
        count = run.Schedule()
        # If some work was scheduled, process it.
        while count != 0:
            # Loop until we've received responses for all of the tests
            # and resources that have been scheduled.
            while count > 0:
                # Read a reply from the response_queue.
                result = response_queue.get()
                # Process the response.
                run.AddResult(result)
                # We're waiting for one less test.
                count = count - 1

            # Schedule some more work.
            count = run.Schedule()
    finally:
        # Stop the targets.
        for target in targets:
            target.Stop()

        # Let all of the result streams know that the test run is complete.
        for rs in result_streams:
            rs.Summarize()


def is_group_match(group_pattern, group):
    """Return true if 'group' matches 'group_pattern'.

    'group_pattern' -- A target group pattern.

    'group' -- A target group."""

    return re.match(group_pattern, group)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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
import qm.async
import qm.common
import qm.xmlutil
import re
import string
import sys

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



class ProtocolError(Exception):
    """A malformed command or reply was received."""

    pass



########################################################################
# classes
########################################################################

class TargetSpec:
    """The specification of a machine or other entity that runs tests."""

    def __init__(self, name, class_name, group, concurrency, properties):
        """Construct a target specification.

        'name' -- The target's name.

        'class_name' -- The fully-qualified name of the Python class
        of which the target is to be an instance.

        'group' -- A string specifying the target group.

        'concurrency' -- The number of simultaneous tests and resource
        functions to run on this target.  Must be a positive integer.

        'properties' -- A map of additional target properties.  Keys and
        values are strings."""

        self.name = name
        self.class_name = class_name
        self.group = group
        concurrency = int(concurrency)
        assert concurrency > 0
        self.concurrency = concurrency
        self.properties = properties

        
    def MakeDomNode(self, document):
        """Construct a DOM element node for this target specification.

        'document' -- The DOM document for which to construct the
        element."""

        element = document.createElement("target")

        element.appendChild(qm.xmlutil.create_dom_text_element(
            document, "name", self.name))
        element.appendChild(qm.xmlutil.create_dom_text_element(
            document, "class", self.class_name))
        element.appendChild(qm.xmlutil.create_dom_text_element(
            document, "group", self.group))
        element.appendChild(qm.xmlutil.create_dom_text_element(
            document, "concurrency", str(self.concurrency)))

        for name, value in self.properties.items():
            property_element = qm.xmlutil.create_dom_text_element(
                document, "property", value)
            property_element.setAttribute("name", name)
            element.appendChild(property_element)

        return element



class Target:
    """Base class for target implementations.

    A target is an entity that can run tests.  A target supports these
    features:

      * A target can run tests, as well as setup and cleanup functions
        for resources.

      * A target maintains a queue of tests and resource functions that
        have been assigned to it.

      * A target may execute more than one test or resource function at
        a time.  Its concurrency specifies the number of simultaneous
        operations it can carry out.

    While the target may create parallel threads of execution on the
    local or remote machine, as well as IPC mechanisms to communicate
    them them, the target need not serialize or multiplex communications
    with these threads.  This coordination is handled externally.  The
    target manages its outgoing communications when the 'ProcessQueue'
    method is invoked, and handles incoming communications when the
    'OnReplyReady' method is invoked."""

    def __init__(self, target_spec):
        """Instantiate a target.

        'target_spec' -- A 'TargetSpec' object describing the target.

        postconditions -- The target, including parallel threads of
        execution and requisite IPC channels, is set up, and is ready to
        execute tests."""

        self.__spec = target_spec


    def GetName(self):
        """Return the name of the target."""
        
        return self.__spec.name


    def GetGroup(self):
        """Return the group of which the target is a member."""

        return self.__spec.group


    def GetConcurrency(self):
        """Return the number of tests the target may run concurrently."""

        return self.__spec.concurrency


    def GetProperty(self, name, default=None):
        return self.__spec.properties.get(name, default)


    def GetChannels(self):
        """Return the target's communication channels.

        returns -- A sequence of 'Channel' objects.  These objects are
        used by the target to communicate with its threads of
        execution."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.GetChannels"


    def Stop(self):
        """Stop the target.

        preconditions -- The target must be idle.

        postconditions -- The target may no longer be used."""
        
        raise qm.common.MethodShouldBeOverriddenError, "Target.Stop"


    def EnqueueRunTest(self, test_id, context):
        """Place a test in the work queue."""

        self._EnqueueCommand("run test", test_id, context)


    def EnqueueSetUpResource(self, resource_id, context):
        """Place a resource setup function in the work queue."""

        self._EnqueueCommand("set up resource", resource_id, context)


    def EnqueueCleanUpResource(self, resource_id, context):
        """Place a resource cleanup function in the work queue."""

        self._EnqueueCommand("clean up resource", resource_id, context)


    def GetQueueLength(self):
        """Return the number of items in the work queue."""
        
        raise qm.common.MethodShouldBeOverriddenError, "Target.GetQueueLength"


    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the work queue is empty and no tests or
        resource functions are currently being executed."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.IsIdle"


    def OnReplyReady(self, channel, test_run):
        """Process an incoming reply.

        'channel' -- The 'Channel' object from which the reply is
        waiting to be read.

        'test_run' -- The 'TestRun' object in which to accumulate test
        and resource results."""

        # Read the reply object from the channel.
        reply_type, result = _receive(channel)
        if reply_type == "test result":
            # It contains a test result.  Accumulate it in the provided
            # test run.
            test_run.AddTestResult(result, self)
        elif reply_type == "resource result":
            # It contains a resource function result.  Accumulate it in
            # the provided test run.
            test_run.AddResourceResult(result, self)
        else:
            # Something we don't recognize.
            raise ProtocolError, "invalid reply type: %s" % reply_type


    def ProcessQueue(self):
        """Process work in the work queue."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.ProcessQueue"



class SubprocessTarget(Target):
    """A target implementation that runs tests in local subprocesses.

    This target forks one child process for each degree of concurrency.
    Each child executes one test or resource function at a time.
    Communication with children is via pairs of pipes."""

    class ChildProcess:
        """A record representing one child process."""

        def __init__(self, pid, channel):
            self.pid = pid
            self.channel = channel


    # The target communicates with its children using the command
    # protocol described in 'process_commands'.  A child process
    # activity (test or resource function) is initiated by sending it a
    # command object.  When the activity completes, the child process
    # responds with a reply object, and awaits its next command.

    # Attributes:
    #
    # '_children' -- A list of 'ChildProcess' instances representing
    # the child processes.
    #
    # '_ready_children' -- A subset list of '_children' containing
    # those child processes that are not running a test or resource
    # function.
    #
    # '__command_queue' -- A list of queued commands.  The commands have
    # not yet been assigned to individual children.


    def __init__(self, target_spec):
        # Initialize the base class.
        Target.__init__(self, target_spec)

        # Build the children.
        self._children = []
        for i in xrange(0, self.GetConcurrency()):
            # Fork a child process.
            child_pid, channel = qm.async.fork_with_channel()
            if child_pid == 0:
                # This is a child process.  Process commands from the
                # channel. 
                try:
                    # Process commands from the channel, until the
                    # "quit" command is received.
                    process_commands(channel)
                except KeyboardInterrupt:
                    pass
                except:
                    exc_info = sys.exc_info()
                    sys.stderr.write(qm.common.format_exception(exc_info))
                # Done with this engine.  Close the channel.
                channel.Close()
                # Terminate Python unceremoniously; don't run cleanups
                # in this child process.
                os._exit(0)
            else:
                # This is the parent process.  Store the child PID and
                # the channel.
                self._children.append(self.ChildProcess(child_pid, channel))

        # Initially, all children are ready
        self._ready_children = self._children[:]
        self.__command_queue = []


    def GetChannels(self):
        # Extract the channel for each child.
        return map(lambda child: child.channel, self._children)


    def Stop(self):
        # Make sure we're not doing anything.
        assert self.IsIdle()
        # Send each child a "quit" command.
        for child in self._children:
            _send(child.channel, ("quit", None, None))
            # Make sure the data goes out.
            child.channel.Flush()
        # Now wait for each child process to finish.
        for child in self._children:
            os.waitpid(child.pid, 0)
            child.channel.Close()

        # Erase attributes.  This instance is now no longer usable.
        del self._ready_children 
        del self._children


    def GetQueueLength(self):
        return len(self.__command_queue) - len(self._ready_children)


    def IsIdle(self):
        return len(self.__command_queue) == 0 \
               and len(self._ready_children) == len(self._children)


    def OnReplyReady(self, channel, test_run):
        # Run the base class version.  This reads and processes the
        # reply object itself, and accumulates results appropriately.
        Target.OnReplyReady(self, channel, test_run)
        # Put the child process corresponding to this channel on the
        # ready list.  Find the child process associated with 'channel'.
        for child in self._children:
            if child.channel == channel:
                break
        assert child not in self._ready_children
        # The child process is now ready to receive additional work.
        self._ready_children.append(child)
        

    def ProcessQueue(self):
        # Feed commands to ready children until either is exhausted.
        while len(self._ready_children) > 0 \
              and len(self.__command_queue) > 0:
            child = self._ready_children.pop(0)
            command = self.__command_queue.pop(0)
            _send(child.channel, command)


    # Helper functions.

    def _EnqueueCommand(self, command_type, id, context):
        # The command object is simply a Python triple.
        self.__command_queue.append((command_type, id, context))



class RemoteShellTarget(Target):
    """A target that runs tests via a remote shell invocation.

    A 'RemoteShellTarget' runs tests on a remote computer via a remote
    shell call.  The remote shell is in the style of 'rsh' and 'ssh'.
    Using the remote shell, the target invokes the 'qmtest-remote'
    script, which services commands sent via 'stdin', and replies via
    'stdout'.

    This target recognizes the following properties:

      'remote_shell' -- The path to the remote shell executable to use.
      If omitted, the configuration variable 'remote_shell' is used
      instead.  If both are not specified, the default is
      '/usr/bin/ssh'.  The remote shell program must accept the
      command-line syntax 'remote_shell *remote_host* *remote_command*'.

      'host' -- The remote host name.  If omitted, the target name is
      used.

      'database_path' -- The path to the test database on the remote
      computer.  The test database must be identical to the local test
      database.  If omitted, the local test database path is used.

      'qmtest_remote' -- The path to the 'qmtest_remote' command on the
      remote computer.  The default is '/usr/local/bin/qmtest_remote'.

      'arguments' -- Additional command-line arguments to pass to the
      remote shell program.  The value of this property is split at
      space characters, and the arguments are added to the command line
      before the name of the remote host.

    """

    # To keep the remote process busy even in the face of network
    # latency, we queue some commands ahead of time -- more than the
    # remote process can execute at one time.  This attribute is the
    # number of commands to queue ahead.
    __push_ahead = 2


    def __init__(self, target_spec):
        """Create a remote target."""

        # Initialize the base class.
        Target.__init__(self, target_spec)
        # Determine the host name.
        self.__host_name = self.GetProperty("host", None)
        if self.__host_name is None:
            # None specified; use the target name.
            self.__host_name = self.GetName()

        # Fork a child process, redirecting standard I/O to a channel.
        child_pid, channel = qm.async.fork_with_stdio_channel()
        if child_pid == 0:
            # This is the child process.

            # Determine the test database path to use.
            database_path = self.GetProperty(
                "database_path", default=base.get_database().GetPath())
            # Determine the path to the remote 'qmtest-remote' command.
            qmtest_remote_path = self.GetProperty(
                "qmtest_remote", "/usr/local/bin/qmtest-remote")
            # Construct the command we want to invoke remotely.  The
            # 'qmtest-remote' script processes commands from standard
            # I/O. 
            remote_arg_list = [
                '"%s"' % qmtest_remote_path,
                '"%s"' % database_path,
                str(self.GetConcurrency()),
                ]
            # Determine the remote shell program to use.
            remote_shell_program = self.GetProperty("remote_shell", None)
            if remote_shell_program is None:
                remote_shell_program = qm.rc.Get("remote_shell",
                                                 default="/usr/bin/ssh",
                                                 section="common")
            # Extra command-line arguments to the remote shell program
            # may be specified with the "arguments" property. 
            extra_arguments = self.GetProperty("arguments", None)
            if extra_arguments is None:
                # None specified.
                extra_arguments = []
            else:
                # Split them at spaces.
                extra_arguments = string.split(extra_arguments, " ")
            # Construct the remote shell command.
            arg_list = [
                remote_shell_program,
                ] \
                + extra_arguments \
                + [
                self.__host_name,
                string.join(remote_arg_list, " ")
                ]
            
            # Run the remote shell.
            qm.platform.replace_program(arg_list[0], arg_list)
            # Should be unreachable.
            assert false

        else:
            # This is the parent process.  Remember the child.
            self.__command_queue = []
            self.__child_pid = child_pid
            self.__channel = channel
            self.__ready_threads = self.GetConcurrency()


    def GetChannels(self):
        return [self.__channel]


    def Stop(self):
        assert self.IsIdle()
        # Send a single "quit" command to the remote program.
        _send(self.__channel, ("quit", None, None))
        # Make sure it goes out now.
        self.__channel.Flush()
        # Wait for the remote shell process to terminate.
        os.waitpid(self.__child_pid, 0)
        # Clean up.
        self.__channel.Close()
        del self.__channel
        del self.__child_pid


    def GetQueueLength(self):
        return len(self.__command_queue) - self.__ready_threads


    def IsIdle(self):
        return len(self.__command_queue) == 0 \
               and self.__ready_threads == self.GetConcurrency()


    def OnReplyReady(self, channel, test_run):
        self.__ready_threads = self.__ready_threads + 1
        # Run the base class version.  This reads and processes the
        # reply object itself, and accumulates results appropriately.
        Target.OnReplyReady(self, channel, test_run)
        
                
    def ProcessQueue(self):
        # Keep sending commands to the remote process, until we're out
        # of queued commands, or the remote process is oversaturated by
        # '__ready_threads'. 
        while len(self.__command_queue) > 0 \
              and self.__ready_threads > -self.__push_ahead:
            command = self.__command_queue.pop(0)
            self.__ready_threads = self.__ready_threads - 1
            _send(self.__channel, command)


    # Helper functions.

    def _EnqueueCommand(self, command_type, id, context):
        self.__command_queue.append((command_type, id, context))



class _RemoteDemultiplexerTarget(SubprocessTarget):
    """A special target for implementing remote test targets.

    A '_RemoteDemultiplexerTarget' reads commands from a channel and
    dispatches them to a pool of worker processes on the local
    computer.  Replies from the worker processes are asynchronously
    multiplexed back up the channel.

    In addition to the target mechanism, this class includes an event
    loop, 'RelayCommands', which reads commands from the channel,
    dispatches them, and relays replies back up the channel.

    This target should not be used by users.  It is for internal use."""

    def __init__(self, target_spec, control_channel):
        """Intialize the target.

        'control_channel' -- The channel for communicating with the
        controlling host.  Commands are read from the channel, and
        replies multiplexed into it."""

        # Initialize the base class.
        SubprocessTarget.__init__(self, target_spec)
        # Remember the channel.
        self.__control_channel = control_channel


    def OnReplyReady(self, channel):
        # Don't decode the reply.  Forward it, uninspected, directly to
        # the control channel.
        data = channel.Read()
        self.__control_channel.Write(data)
        # Put the child process corresponding to this channel on the
        # ready list.  Find the child process associated with 'channel'.
        for child in self._children:
            if child.channel == channel:
                break
        assert child not in self._ready_children
        # The child process is now ready to receive additional work.
        self._ready_children.append(child)


    def RelayCommands(self):
        """Read commands from the control channel and forward replies to it.
        
        This command blocks until the "quit" command is received and all
        subprocesses terminate."""

        # Create a multiplexer.  This allows us to listen to the control
        # channel and the various child process channels at the same
        # time.
        mux = qm.async.Multiplexer()
        mux.AddChannel(self.__control_channel)
        map(mux.AddChannel, self.GetChannels())

        while 1:
            # Wait for something to happen.
            mux.Wait()

            # Did we get a command from the control channel?
            while self.__control_channel.IsReadReady():
                # Yes.  Read it.
                command = _receive(self.__control_channel)
                if command[0] == "quit":
                    # The "quit" command.  First wait for all the child
                    # processes to finish what they're doing.
                    while not self.IsIdle():
                        self.ProcessQueue()
                        mux.Wait()
                        self.__ProcessReplies()
                    # Shut down the child processes.
                    self.Stop()
                    # All done.
                    return
                else:
                    # Enqueue the command for execution by a child process.
                    apply(self._EnqueueCommand, command)

            # Handle subprocesses.
            self.__ProcessReplies()
            self.ProcessQueue()


    def __ProcessReplies(self):
        """Process incoming replies from child process channels."""

        for channel in self.GetChannels():
            while channel.IsReadReady():
                self.OnReplyReady(channel)



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
    'AddTestResult' and 'AddResourceResult' methods to accumulate
    results."""

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
    # '__test_results' -- A map from test ID to the 'ResultWrapper'
    # object for that test.
    #
    # '__resource_results' -- A sequence of 'ResultWrapper' objects for
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
                 test_ids,
                 context,
                 targets,
                 progress_function=None):
        """Set up a test run.

        'test_ids' -- A sequence of IDs of tests to run.  Where
        possible, the tests are started in the order specified.

        'context' -- The context object to use when running tests.

        'targets' -- A sequence of 'Target' objects, representing
        targets on which tests may be run.

        'progress_function' -- A function which is called with progress
        messages (as the single argument).  If 'None', it is not
        called."""

        self.__test_ids = test_ids
        self.__context = context
        self.__targets = targets
        self.__progress_function = progress_function
        
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
        is true.

        returns -- True if the test run is finished, and there is
        nothing left to do; false if the test run is not finished."""

        database = base.get_database()

        # For each call, we'll maintain a list of targets which are
        # ready to accept more work.
        ready_targets = filter(self.__TargetIsReady, self.__targets)

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
                    target.EnqueueCleanUpResource(resource_id,
                                                  context_wrapper)
            # That's it for the test run.
            return 1

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
                group_pattern = test.GetProperty("group")
                result = base.Result(base.Result.UNTESTED,
                                     cause=cause,
                                     group_pattern=group_pattern)
                result = base.ResultWrapper(test_id, self.__context, result)
                self.AddTestResult(result)
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
                result = base.Result(
                    base.Result.UNTESTED,
                    cause=cause,
                    prerequisite_id=prerequisite_id,
                    prerequisite_outcome=prerequisite_outcome,
                    expected_outcome=expected_outcome)
                result = base.ResultWrapper(test_id, self.__context, result)
                self.AddTestResult(result)
                self.__remaining_test_ids.remove(test_id)
                continue

            except FailedResourceError, error:
                resource_id = str(error)
                # One of the resources required for this test failed
                # during setup, so we can't run the test.  Add an
                # 'UNTESTED' result for it.
                cause = qm.message("failed resource")
                result = base.Result(base.Result.UNTESTED,
                                     cause=cause,
                                     resource_id=resource_id)
                result = base.ResultWrapper(test_id, self.__context, result)
                self.AddTestResult(result)
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
                target.EnqueueRunTest(test_id, context_wrapper)
                self.__remaining_test_ids.remove(test_id)
            else:
                # Yes, there's at least one resource missing for the
                # target.  Instead of running the test, set up all the
                # missing resources.  Defer the test; it'll probably be
                # scheduled for this target later.
                for resource_id in missing_resource_ids:
                    context_wrapper = base.ContextWrapper(self.__context)
                    target.EnqueueSetUpResource(resource_id, context_wrapper)

            # If we just gave the target enough work to keep it busy for
            # now, remove it from the list of available targets.
            if not self.__TargetIsReady(target):
                ready_targets.remove(target)

        # We've scheduled as much as we can for now.  Return, but ask to be
        # called again.
        return 0


    def AddTestResult(self, result_wrapper, target=None):
        """Report the result of running a test.

        'result_wrapper' -- A 'ResultWrapper' object representing the
        result of running a test.

        'target' -- The target on which the test was run, if any."""

        # If a target was specified, record its name in the result.
        if target is not None:
            result_wrapper["target"] = target.GetName()
        # Store the result.
        self.__test_results[result_wrapper.GetId()] = result_wrapper
        # Print a progress message.
        test_id = result_wrapper.GetId()
        outcome = result_wrapper.GetOutcome()
        message = "test %-60s: %s\n" % (test_id, outcome)
        self.__ProgressMessage(message)


    def AddResourceResult(self, result_wrapper, target):
        """Report the result of running a resource function.

        'result_wrapper' -- A 'ResultWrapper' object representing the
        result of running the resource function.

        'target' -- The target on which the resource function was
        run.""" 

        # If a target was specified, record its name in the result.
        result_wrapper["target"] = target.GetName()
        # Store the result.
        self.__resource_results.append(result_wrapper)

        # Extract information from the result.
        resource_id = result_wrapper.GetId()
        outcome = result_wrapper.GetOutcome()
        action = result_wrapper["action"]
        assert action in ["setup", "cleanup"]

        if action == "setup" and outcome == base.Result.PASS:
            # A resource has successfully been set up.  Record it as an
            # active resource for the target.  For that resource and
            # target combination, store the context properties that were
            # added by the resource setup function, so that tese can be
            # made available to tests that use the resource.
            added_properties = \
                result_wrapper.GetContext().GetAddedProperties()
            self.__resources[target][resource_id] = added_properties

        elif action == "setup" and outcome != base.Result.PASS:
            # A resource's setup function failed.  Note this, so that
            # the resource setup is not reattempted.
            self.__failed_resources[resource_id] = None
            # Schedule the cleanup function for this resource
            # immediately. 
            context_wrapper = base.ContextWrapper(self.__context)
            target.EnqueueCleanUpResource(resource_id, context_wrapper)

        elif action == "cleanup" and outcome == base.Result.PASS:
            # A resource has successfully been cleaned up.  Remove it
            # from the list of active resources for the target.
            del self.__resources[target][resource_id]

        # Print a progress message.
        resource_id = result_wrapper.GetId()
        outcome = result_wrapper.GetOutcome()
        if action == "setup":
            message = "resource setup %-50s: %s\n" % (resource_id, outcome)
        else:
            message = "resource clean up %-47s: %s\n" % (resource_id, outcome)
        self.__ProgressMessage(message)


    def GetTestResults(self):
        """Return the test results from the run.

        returns -- A map from test ID to corresponding results."""

        return self.__test_results


    def GetResourceResults(self):
        """Return the resource function results from the run.

        returns -- A sequence of resource function results."""

        return self.__resource_results


    # Helper functions.

    def __ProgressMessage(self, message):
        """Print a progress message, if appropriate."""

        if self.__progress_function is not None:
            self.__progress_function(message)


    def __TargetIsReady(self, target):
        """Return true if 'target' is ready to accept more work."""

        # Keep at least one element in the work queue for each target.
        return target.GetQueueLength() < 1


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

        # Was a group pattern specified for the test?
        group_pattern = test.GetProperty("group", None)
        if group_pattern is not None:
            # Yes.  Check whether there is a target in a matching
            # group. 
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

        'test' -- The test to consider.

        'targets' -- A sequence of targets from which to choose the
        best.

        returns -- The target on which to run the test."""
        
        test_resource_ids = test.GetResources()
        group_pattern = test.GetProperty("group", None)

        best_target = None
        # Scan over targets to find the best one.
        for target in targets:
            # If the test has a group pattern specified, disqualify this
            # target if its group does not match.
            if group_pattern is not None \
               and not is_group_match(group_pattern, target.GetGroup()):
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

def test_run(test_ids,
             context,
             target_specs,
             message_function=None):
    """Perform a test run.

    This function coordinates the scheduling of tests and the IPC
    between the main thread of execution (in which this function is
    called) and subthreads (created by targets) which run the tests.

    'test_ids' -- The sequence of IDs of tests to include in the test
    run.

    'context' -- The 'Context' object to use when running tests and
    resource functions.

    'target_specs' -- A sequence of 'TargetSpec' objects representing
    the targets on which to run the tests.

    'message_function' -- A function to receive progress messages.  If
    not 'None', it is called periodically with a single argument, a
    string message.

    returns -- A pair '(test_results, resource_results)'.
    'test_results' is a map from test IDs to corresponding
    'ResultWrapper' objects.  'resource_results' is a sequence of
    'ResultWrapper' objects for resource functions that were run."""
    
    # We'll use this multiplexer to coordinate the responses from the
    # various threads of execution that test targets may set up.
    mux = qm.async.Multiplexer()

    targets = []
    channels = []
    # Set up the targets.
    for target_spec in target_specs:
        # Find the target class.
        target_class = qm.common.load_class(target_spec.class_name, sys.path)
        # Build the target.
        target = target_class(target_spec)

        # Accumulate the communication channels used by this target.
        target_channels = target.GetChannels()
        channels.extend(target_channels)
        for channel in target_channels:
            mux.AddChannel(channel)
            # Store the target on each channel, so we can easily figure
            # out later which target is talking through a channel.
            channel.__target = target
    
        # Accumulate targets.
        targets.append(target)

    # Construct the test run.
    run = TestRun(test_ids, context, targets, message_function)

    # Schedule all the tests and resource functions in the test run.

    # Schedule the first batch of work.
    done = run.Schedule()
    # Loop until done scheduling everything in the test run.
    while not done:
        targets_busy = 0
        for target in targets:
            # Give each target a chance to feed its threads some work
            # that was queued up by the scheduler.
            target.ProcessQueue()
            # Remember whether there's at least one target that's not
            # idle, i.e. that's working on a test or resource function.
            if not target.IsIdle():
                targets_busy = 1
        # Are there any targets working on something?
        if targets_busy:
            # Yes.  Wait for at least one of them to reply with
            # something. 
            mux.Wait()
        # Process replies from any channel that has data in it.
        for channel in channels:
            while channel.IsReadReady():
                # The target is responsible for reading from the channel
                # and processing the data accordingly.
                channel.__target.OnReplyReady(channel, run)
        # Schedule some more work.
        done = run.Schedule()

    # Now we've finished scheduling anything, but some targets may still
    # be working.  Give them a chance to finish up by looping until all
    # are idle.

    while len(filter(lambda t: not t.IsIdle(), targets)) > 0:
        # Give the targets a chance to feed their threads some of the
        # remaining work. 
        for target in targets:
            target.ProcessQueue()
        # Wait for at least one of them to reply with something.
        mux.Wait()
        # Process replies from any channel that has data in it.
        for channel in channels:
            while channel.IsReadReady():
                # The target is responsible for reading from the channel
                # and processing the data accordingly.
                channel.__target.OnReplyReady(channel, run)

    # All targets are now idle.  Stop them.
    for target in targets:
        target.Stop()

    # Return the results we've accumulated.
    return run.GetTestResults(), run.GetResourceResults()


def is_group_match(group_pattern, group):
    """Return true if 'group' matches 'group_pattern'.

    'group_pattern' -- A target group pattern.

    'group' -- A target group."""

    return re.match(group_pattern, group)


def _send(channel, object):
    """Send an object through a channel."""

    data = cPickle.dumps(object, 1)
    channel.Write(data)


def _receive(channel):
    """Receive an object from a channel."""

    data = channel.Read()
    return cPickle.loads(data)


def process_commands(channel):
    """Process test commands.

    Read commands from 'channel', process them (synchronously), and
    write back results.  Continue until we get the "quit" command.

    Commands are specified as Python triplets, encoded as by
    'async.write_object'.  The format of the triplet is '(type, id,
    context)'.  'type' specifies the command:

      * "run test" runs a test.  'id' is the test ID.  Responds with a
        "test result" reply.

      * "set up resource" sets up a resource.  'id' is the resource ID.
        Responds with a "resource result" reply.

      * "clean up resource" cleans up a resource.  'id' is the resource
        ID.  Responds with a "resource result" reply.

      * "quit" causes this function to stop processing commands and
        return.  'id' and 'context' are ignored.

    Responses to commands are written to 'write_fd', also encoded by
    'async.write_object'.  Each response is a pair, '(type, result)'.
    'type' is "test result", and 'result' is the corresponding 'Result'
    object.

    'channel' -- The channel from which to read commands and send
    replies. 

    raises -- 'ProtocolError' if a malformed command is received."""

    database = base.get_database()

    while 1:
        try:
            # Block until the next command is available.
            channel.Wait()
            # Read it.
            command_object = _receive(channel)
        except qm.async.ConnectionClosedException:
            # Oops.  The connection closed unexpectedly.  End quietly,
            # anyway.
            return

        try:
            command_type, id, context = command_object
        except ValueError:
            raise ProtocolError, repr(command_object)

        if command_type == "quit":
            # All done; stop processing commands.
            return

        elif command_type == "run test":
            # Run a test.
            result = base.run_test(id, context)
            # Send back the test result.
            _send(channel, ("test result", result))

        elif command_type == "set up resource":
            # Set up a resource.
            result = base.set_up_resource(id, context)
            # Send back the resource setup result.
            _send(channel, ("resource result", result))

        elif command_type == "clean up resource":
            # Clean up a resource.
            result = base.clean_up_resource(id, context)
            # Send back the resource cleanup result.
            _send(channel, ("resource result", result))

        else:
            raise ProtocolError, "unknown command type %s" % command_type

        # Write now whatever we sent via the channel.
        channel.Flush()


def load_target_specs(path):
    """Read target specs from a file.

    'path' -- The file from which to load the results.

    returns -- A sequence of 'TargetSpec' objects."""

    document = qm.xmlutil.load_xml_file(path)
    targets_element = document.documentElement
    assert targets_element.tagName == "targets"
    target_specs = []
    for target_spec_node in targets_element.getElementsByTagName("target"):
        target_spec = _target_spec_from_dom(target_spec_node)
        target_specs.append(target_spec)
    return target_specs
    

def _target_spec_from_dom(node):
    """Extract a target spec from a DOM element.

    'node' -- A DOM node corresponding to a target spec element.

    returns -- A 'TargetSpec' object."""

    # Extract standard elements.
    name = qm.xmlutil.get_child_text(node, "name")
    class_name = qm.xmlutil.get_child_text(node, "class")
    group = qm.xmlutil.get_child_text(node, "group")
    concurrency = qm.xmlutil.get_child_text(node, "concurrency")
    concurrency = int(concurrency)
    # Extract properties.
    properties = {}
    for property_node in node.getElementsByTagName("property"):
        property_name = property_node.getAttribute("name")
        value = qm.xmlutil.get_dom_text(property_node)
        properties[property_name] = value
    # Construct the target spec.
    return TargetSpec(name, class_name, group, concurrency, properties)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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



class ProtocolError(Exception):
    """A malformed command or reply was received."""

    pass



########################################################################
# classes
########################################################################

class CommandThread(Thread):
    """A 'CommandThread' executes commands."""

    def __init__(self, target, response_queue):
	"""Construct a new 'CommandThread'.

	'target' -- The 'Target' that owns this thread.

	'response_queue' -- The queue on which to write responses."""

	Thread.__init__(self, None, None, None)

	self.__target = target
	self.__response_queue = response_queue

	# Create the queue to which the controlling thread will
	# write commands.
	self.__command_queue = Queue.Queue(0)


    def run(self):
	try:
            # Process commands from the channel, until the
            # "quit" command is received.
            self._ProcessCommands()
        except KeyboardInterrupt:
            pass
        except:
            exc_info = sys.exc_info()
            sys.stderr.write(qm.common.format_exception(exc_info))


    def GetCommandQueue(self):
	"""Return the 'Queue' associated with the thread.

	returns -- The 'Queue' on which the controlling thread writes 
	commands."""
	
	return self.__command_queue


    def GetResponseQueue(self):
        """Return the 'Queue' on which results will be written.

        returns -- The 'Queue' on which the results will be written."""

        return self.__response_queue


    def GetTarget(self):
        """Return the 'Target' associated with this thread.

        returns -- The 'Target' with which this thread is associated."""

        return self.__target

    
    def _ProcessCommands(self):
	"""Process test commands.

	Read commands from the queue, process them (synchronously), and
	write back results.  Continue until we get the "quit" command.

	Commands are specified as Python triplets.  The format of each
	triplet is '(type, id, context)'.  'type' specifies the command:

	  * "run test" runs a test.  'id' is the test ID.  Responds with a
	    "test result" reply.

	  * "set up resource" sets up a resource.  'id' is the resource ID.
	    Responds with a "resource result" reply.

	  * "clean up resource" cleans up a resource.  'id' is the resource
	    ID.  Responds with a "resource result" reply.

	  * "quit" causes this function to stop processing commands and
	    return.  'id' and 'context' are ignored.

	Responses to commands are written to the response queue.  Each
	response is a pair, '(target, result)'.

	raises -- 'ProtocolError' if a malformed command is received."""

        raise qm.common.MethodShouldBeOverriddenError, \
              "CommandThread._ProcessCommands"
    


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
    'OnReply' method is invoked."""

    def __init__(self, target_spec, database):
        """Instantiate a target.

        'target_spec' -- A 'TargetSpec' object describing the target.

        'database' -- The 'Database' containing the tests that will be
        run."""

        self.__spec = target_spec
        self.__database = database
        

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


    def GetDatabase(self):
        """Return the 'Database' containing the tests this target will run.

        returns -- The 'Database' containing the tests this target will
        run."""

        return self.__database

    
    def Stop(self):
        """Stop the target.

        preconditions -- The target must be idle.

        postconditions -- The target may no longer be used."""
        
        raise qm.common.MethodShouldBeOverriddenError, "Target.Stop"


    def EnqueueRunTest(self, test_id, context):
        """Place a test in the work queue."""

        self.EnqueueCommand("run test", test_id, context)


    def EnqueueSetUpResource(self, resource_id, context):
        """Place a resource setup function in the work queue."""

        self.EnqueueCommand("set up resource", resource_id, context)


    def EnqueueCleanUpResource(self, resource_id, context):
        """Place a resource cleanup function in the work queue."""

        self.EnqueueCommand("clean up resource", resource_id, context)


    def GetQueueLength(self):
        """Return the number of items in the work queue."""
        
        raise qm.common.MethodShouldBeOverriddenError, "Target.GetQueueLength"


    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the work queue is empty and no tests or
        resource functions are currently being executed."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.IsIdle"


    def OnReply(self, result, test_run):
        """Process an incoming reply.
	
	'result' -- The result of running a test or resource.

        'test_run' -- The 'TestRun' object in which to accumulate test
        and resource results, or 'None' if no accumulation is
        necessary."""
	
        if test_run:
            test_run.AddResult(result, self)


    def ProcessQueue(self):
        """Process work in the work queue."""

        raise qm.common.MethodShouldBeOverriddenError, "Target.ProcessQueue"



class LocalThread(CommandThread):
    """A 'LocalThread' executes commands locally."""

    def __init__(self, target, response_queue):
	"""Construct a new 'LocalThread'.

	'target' -- The 'Target' that owns this thread.

	'response_queue' -- The queue on which to write responses."""

	CommandThread.__init__(self, target, response_queue)


    def _ProcessCommands(self):
	"""Process test commands.

	Read commands from the queue, process them (synchronously), and
	write back results.  Continue until we get the "quit" command.

	Commands are specified as Python triplets.  The format of each
	triplet is '(type, id, context)'.  'type' specifies the command:

	  * "run test" runs a test.  'id' is the test ID.  Responds with a
	    "test result" reply.

	  * "set up resource" sets up a resource.  'id' is the resource ID.
	    Responds with a "resource result" reply.

	  * "clean up resource" cleans up a resource.  'id' is the resource
	    ID.  Responds with a "resource result" reply.

	  * "quit" causes this function to stop processing commands and
	    return.  'id' and 'context' are ignored.

	Responses to commands are written to the response queue.  Each
	response is a pair, '(target, result)'.

	raises -- 'ProtocolError' if a malformed command is received."""

	while 1:
	    try:
		# Read the next command.
		command_object = self.GetCommandQueue().get()
	    except:
		# Something went wrong.  Exit so that the thread exits.
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
                test = self.GetTarget().GetDatabase().GetTest(id)
		result = base.run_test(test, context)
	    elif command_type == "set up resource":
		# Set up a resource.
                resource = self.GetTarget().GetDatabase().GetResource(id)
		result = base.set_up_resource(resource, context)
	    elif command_type == "clean up resource":
		# Clean up a resource.
                resource = self.GetTarget().GetDatabase().GetResource(id)
		result = base.clean_up_resource(resource, context)
	    else:
		raise ProtocolError, "unknown command type %s" % command_type

	    # Send back the result.
	    self.GetResponseQueue().put((self.GetTarget(), (result, self)))

            

class SubprocessTarget(Target):
    """A target implementation that runs tests in local threads.

    This target starts one thread for each degree of concurrency.  Each
    child executes one test or resource function at a time."""

    def __init__(self, target_spec, database, response_queue):
	"""Construct a new 'SubprocessTarget'.

        'database' -- The 'Database' containing the tests that will be
	run.
        
	'response_queue' -- The queue on which to write responses."""

        # Initialize the base class.
        Target.__init__(self, target_spec, database)

        # Build the children.
        self._children = []
        for i in xrange(0, self.GetConcurrency()):
	    # Create the new thread.
	    thread = LocalThread(self, response_queue)
	    # Start the thread.
	    thread.start()
	    # Remember the thread.
            self._children.append(thread)

        # Initially, all children are ready
        self._ready_children = self._children[:]
        self.__command_queue = []


    def Stop(self):
        # Make sure we're not doing anything.
        assert self.IsIdle()
        # Send each child a "quit" command.
        for child in self._children:
	    child.GetCommandQueue().put(("quit", None, None))
        # Now wait for each child process to finish.
        for child in self._children:
	    child.join()

        # Erase attributes.  This instance is now no longer usable.
        del self._ready_children 
        del self._children


    def GetQueueLength(self):
        return len(self.__command_queue) - len(self._ready_children)


    def IsIdle(self):
        return len(self.__command_queue) == 0 \
               and len(self._ready_children) == len(self._children)


    def OnReply(self, response, test_run):
        # Run the base class version.  This reads and processes the
        # reply object itself, and accumulates results appropriately.
        Target.OnReply(self, response[0], test_run)
        # Find the child process that sent the response.
	child = response[1]
        assert child not in self._ready_children
        # The child process is now ready to receive additional work.
        self._ready_children.append(child)
        

    def ProcessQueue(self):
        # Feed commands to ready children until either is exhausted.
        while len(self._ready_children) > 0 \
              and len(self.__command_queue) > 0:
            child = self._ready_children.pop(0)
            command = self.__command_queue.pop(0)
	    child.GetCommandQueue().put(command)


    # Helper functions.

    def EnqueueCommand(self, command_type, id, context):
        # The command object is simply a Python triple.
        self.__command_queue.append((command_type, id, context))



class RemoteThread(CommandThread):
    """A 'RemoteThread' executes commands remotely."""

    def __init__(self, target, response_queue, write_file, read_file):
	"""Construct a new 'RemoteThread'.

	'target' -- The 'Target' that owns this thread.

	'response_queue' -- The queue on which to write responses.

        'write_file' -- The file object to which commands should be
        written.  This file will be closed when the thread exits.

        'read_file' -- The file object from which results should be
        read.  This file will be closed when the thread exits."""

	CommandThread.__init__(self, target, response_queue)

        self.__write_file = write_file
        self.__read_file = read_file
        

    def _ProcessCommands(self):
	"""Process test commands.

	Read commands from the queue, process them (synchronously), and
	write back results.  Continue until we get the "quit" command.

	Commands are specified as Python triplets.  The format of each
	triplet is '(type, id, context)'.  'type' specifies the command:

	  * "run test" runs a test.  'id' is the test ID.  Responds with a
	    "test result" reply.

	  * "set up resource" sets up a resource.  'id' is the resource ID.
	    Responds with a "resource result" reply.

	  * "clean up resource" cleans up a resource.  'id' is the resource
	    ID.  Responds with a "resource result" reply.

	  * "quit" causes this function to stop processing commands and
	    return.  'id' and 'context' are ignored.

	Responses to commands are written to the response queue.  Each
	response is a pair, '(target, result)'.

	raises -- 'ProtocolError' if a malformed command is received."""

	while 1:
	    try:
		# Read the next command.
		command_object = self.GetCommandQueue().get()
	    except:
		# Something went wrong.  Exit so that the thread exits.
		return

            # Send the command through the pipe.
            cPickle.dump(command_object, self.__write_file)

            # If we get the "quit" command, stop.
            if command_object[0] == "quit":
                self.__read_file.close()
                self.__write_file.close()
                return
            
            # Otherwise, read the result.
            print "About to read..."
            result = cPickle.load(self.__read_file)
            print "Done reading..."
	    # Send back the result.
	    self.GetResponseQueue().put((self.GetTarget(), result))



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


    def __init__(self, target_spec, database, response_queue):
        """Construct a new 'RemoteShellTarget'.

        'target_spec' -- The specification for the target.

        'database' -- The 'Database' containing the tests that will be
        run."""

        # Initialize the base class.
        Target.__init__(self, target_spec, database)
        # Determine the host name.
        self.__host_name = self.GetProperty("host", None)
        if self.__host_name is None:
            # None specified; use the target name.
            self.__host_name = self.GetName()

        # Create two pipes: one to write commands to the remote
        # QMTest, and one to read responses.
        command_pipe = os.pipe()
        response_pipe = os.pipe()
        
        # Create the child process.
        child_pid = os.fork()
        
        if child_pid == 0:
            # This is the child process.

            # Close the write end of the command pipe.
            os.close(command_pipe[1])
            # And the read end of the response pipe.
            os.close(response_pipe[0])
            # Connect the pipes to the standard input and standard
            # output for thie child.
            os.dup2(command_pipe[0], sys.stdin.fileno())
            os.dup2(response_pipe[1], sys.stdout.fileno())
            
            # Determine the test database path to use.
            database_path = self.GetProperty(
                "database_path", default=database.GetPath())
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
            assert 0

        else:
            # This is the parent process.  Remember the child.
            self.__command_queue = []
            self.__child_pid = child_pid
            self.__ready_threads = self.GetConcurrency()

            # Start the thread that will process responses from
            # the child.
            self.__thread = \
               RemoteThread(self, response_queue,
                            os.fdopen(command_pipe[1], "w", 0),
                            os.fdopen(response_pipe[0], "r"))
            self.__thread.start()
            
            
    def Stop(self):
        assert self.IsIdle()
        # Send a single "quit" command to the remote program.
        self.__thread.GetCommandQueue().put(("quit", None, None))
        # Wait for the remote shell process to terminate.
        os.waitpid(self.__child_pid, 0)
        # Clean up.
        del self.__child_pid


    def GetQueueLength(self):
        return len(self.__command_queue) - self.__ready_threads


    def IsIdle(self):
        return len(self.__command_queue) == 0 \
               and self.__ready_threads == self.GetConcurrency()


    def OnReply(self, response, test_run):
        self.__ready_threads = self.__ready_threads + 1
        # Run the base class version.  This reads and processes the
        # reply object itself, and accumulates results appropriately.
        Target.OnReply(self, response, test_run)
        
                
    def ProcessQueue(self):
        # Keep sending commands to the remote process, until we're out
        # of queued commands, or the remote process is oversaturated by
        # '__ready_threads'. 
        while len(self.__command_queue) > 0 \
              and self.__ready_threads > -self.__push_ahead:
            command = self.__command_queue.pop(0)
            self.__ready_threads = self.__ready_threads - 1
            self.__thread.GetCommandQueue().put(command)


    # Helper functions.

    def EnqueueCommand(self, command_type, id, context):
        self.__command_queue.append((command_type, id, context))



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
        ready_targets = filter(self.__TargetIsReady, self.__targets)

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
                    target.EnqueueCleanUpResource(resource_id,
                                                  context_wrapper)
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
                group_pattern = test.GetProperty("group")
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
                target.EnqueueRunTest(test_id, context_wrapper)
		count = count + 1
                self.__remaining_test_ids.remove(test_id)
            else:
                # Yes, there's at least one resource missing for the
                # target.  Instead of running the test, set up all the
                # missing resources.  Defer the test; it'll probably be
                # scheduled for this target later.
                for resource_id in missing_resource_ids:
                    context_wrapper = base.ContextWrapper(self.__context)
                    target.EnqueueSetUpResource(resource_id, context_wrapper)
		    count = count + 1

            # If we just gave the target enough work to keep it busy for
            # now, remove it from the list of available targets.
            if not self.__TargetIsReady(target):
                ready_targets.remove(target)

        # We've scheduled as much as we can for now.
        return count


    def AddResult(self, result, target=None):
        """Report the result of running a test or resource.

        'result' -- A 'Result' object representing the result of running
        a test or resource.

        'target' -- The target on which the test was run, if any."""

        # If a target was specified, record its name in the result.
        if target is not None:
            result[Result.TARGET] = target.GetName()
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
                target.EnqueueCleanUpResource(resource_id, context_wrapper)

            elif action == "cleanup" and outcome == Result.PASS:
                # A resource has successfully been cleaned up.  Remove it
                # from the list of active resources for the target.
                del self.__resources[target][resource_id]
        else:
            assert 0
            
        # Report the result.
        self.__ReportResult(result)


    def GetTestResults(self):
        """Return the test results from the run.

        returns -- A map from test ID to corresponding results."""

        return self.__test_results


    def GetResourceResults(self):
        """Return the resource function results from the run.

        returns -- A sequence of resource function results."""

        return self.__resource_results


    # Helper functions.

    def __ReportResult(self, result):
        """Report the 'result'.

        'result' -- A 'Result' indicating the outcome of a test or
        resource run.

        The result is provided to all of the 'ResultStream' objects."""

        for rs in self.__result_streams:
            rs.WriteResult(result)


    def __TargetIsReady(self, target):
        """Return true if 'target' is ready to accept more work."""

        # Keep at least one element in the work queue for each target.
        return target.GetQueueLength() < 0


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

def test_run(database,
             test_ids,
             context,
             target_specs,
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

    'target_specs' -- A sequence of 'TargetSpec' objects representing
    the targets on which to run the tests.

    'result_streams' -- A sequence of 'ResultStream' objects.  Each
    stream will be provided with results as they are available.

    returns -- A pair '(test_results, resource_results)'.
    'test_results' is a map from test IDs to corresponding 'Result'
    objects.  'resource_results' is a sequence of 'Result' objects for
    resource functions that were run."""
    
    response_queue = Queue.Queue(0)

    targets = []
    # Set up the targets.
    for target_spec in target_specs:
        # Find the target class.
        target_class = qm.common.load_class(target_spec.class_name, sys.path)
        # Build the target.
        target = target_class(target_spec, database, response_queue)
        # Accumulate targets.
        targets.append(target)

    # Construct the test run.
    run = TestRun(database, test_ids, context, targets, result_streams)

    # Schedule all the tests and resource functions in the test run.

    # Schedule the first batch of work.
    count = run.Schedule()
    # Loop until done scheduling everything in the test run.
    while count:
        targets_busy = 0
        for target in targets:
            # Give each target a chance to feed its threads some work
            # that was queued up by the scheduler.
            target.ProcessQueue()
            # Remember whether there's at least one target that's not
            # idle, i.e. that's working on a test or resource function.
            if not target.IsIdle():
                targets_busy = 1

	# Loop until we've received responses for all of the tests
	# and resources that have been scheduled.
	while count > 0:
	    # Read a reply from the response_queue.
	    target, response = response_queue.get()
	    # Process the response.
	    target.OnReply(response, run)
	    # We're waiting for one less test.
	    count = count - 1

        # Schedule some more work.
        count = run.Schedule()

    # All targets are now idle.  Stop them.
    for target in targets:
        target.Stop()

    # Let all of the result streams know that the test run is complete.
    for rs in result_streams:
        rs.Summarize()
        
    # Return the results we've accumulated.
    return run.GetTestResults(), run.GetResourceResults()


def is_group_match(group_pattern, group):
    """Return true if 'group' matches 'group_pattern'.

    'group_pattern' -- A target group pattern.

    'group' -- A target group."""

    return re.match(group_pattern, group)


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

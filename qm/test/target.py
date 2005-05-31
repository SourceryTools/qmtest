########################################################################
#
# File:   target.py
# Author: Mark Mitchell
# Date:   10/29/2001
#
# Contents:
#   QMTest Target class.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import qm
import qm.common
import qm.extension
import qm.platform
import qm.test.base
from   qm.test.context import *
from   qm.test.result import *
from   qm.test.database import NoSuchResourceError
import re
import signal
import sys

########################################################################
# classes
########################################################################

class Target(qm.extension.Extension):
    """Base class for target implementations.

    A 'Target' is an entity that can run tests.  QMTest can spread the
    workload from multiple tests across multiple targets.  In
    addition, a single target can run more than one test at once.

    'Target' is an abstract class.

    You can extend QMTest by providing your own target class
    implementation.

    To create your own target class, you must create a Python class
    derived (directly or indirectly) from 'Target'.  The documentation
    for each method of 'Target' indicates whether you must override it
    in your target class implementation.  Some methods may be
    overridden, but do not need to be.  You might want to override
    such a method to provide a more efficient implementation, but
    QMTest will work fine if you just use the default version."""

    arguments = [
        qm.fields.TextField(
            name="name",
            title="Name",
            description="""The name of this target.

            The name of the target.  The target name will be recorded
            in any tests executed on that target so that you can see
            where the test was run.""",
            default_value=""),
        qm.fields.TextField(
            name="group",
            title="Group",
            description="""The group associated with this target.

            Some tests may only be able to run on some targets.  A
            test can specify a pattern indicating the set of targets
            on which it will run.""",
            default_value="")
        ]

    kind = "target"

    class __ResourceSetUpException(Exception):
        """An exception indicating that a resource could not be set up."""

        def __init__(self, resource):
            """Construct a new 'ResourceSetUpException'.

            'resource' -- The name of the resoure that could not be
            set up."""

            self.resource = resource
            

            
    def __init__(self, database, properties):
        """Construct a 'Target'.

        'database' -- The 'Database' containing the tests that will be
        run.

        'properties'  -- A dictionary mapping strings (property names)
        to values."""

        qm.extension.Extension.__init__(self, properties)
        
        self.__database = database


    def GetName(self):
        """Return the name of the target.

        Derived classes must not override this method."""
        
        return self.name


    def GetGroup(self):
        """Return the group of which the target is a member.

        Derived classes must not override this method."""

        return self.group


    def GetDatabase(self):
        """Return the 'Database' containing the tests this target will run.

        returns -- The 'Database' containing the tests this target will
        run.

        Derived classes must not override this method."""

        return self.__database


    def IsIdle(self):
        """Return true if the target is idle.

        returns -- True if the target is idle.  If the target is idle,
        additional tasks may be assigned to it.

        Derived classes must override this method."""

        raise NotImplementedError


    def IsInGroup(self, group_pattern):
        """Returns true if this 'Target' is in a particular group.

        'group_pattern' -- A string giving a regular expression.

        returns -- Returns true if the 'group_pattern' denotes a
        regular expression that matches the group for this 'Target',
        false otherwise."""

        return re.match(group_pattern, self.GetGroup())
        
        
    def Start(self, response_queue, engine=None):
        """Start the target.

        'response_queue' -- The 'Queue' in which the results of test
        executions are placed.
        
        'engine' -- The 'ExecutionEngine' that is starting the target,
        or 'None' if this target is being started without an
        'ExecutionEngine'.
        
        Derived classes may override this method, but the overriding
        method must call this method at some point during its
        execution."""

        self.__response_queue = response_queue
        self.__engine = engine
        # There are no resources available on this target yet.
        self.__resources = {}
        self.__order_of_resources = []

        
    def Stop(self):
        """Stop the target.

        Clean up all resources that have been set up on this target
        and take whatever other actions are required to stop the
        target.
        
        Derived classes may override this method."""
        
        # Clean up any available resources.
        self.__order_of_resources.reverse()
        for name in self.__order_of_resources:
            rop = self.__resources[name]
            if rop and rop[1] == Result.PASS:
                self._CleanUpResource(name, rop[0])
        del self.__response_queue
        del self.__engine
        del self.__resources
        del self.__order_of_resources


    def RunTest(self, descriptor, context):
        """Run the test given by 'test_id'.

        'descriptor' -- The 'TestDescriptor' for the test.

        'context' -- The 'Context' in which to run the test.

        Derived classes may override this method."""

        # Create the result.
        result = Result(Result.TEST, descriptor.GetId())
        try:
            # Augment the context appropriately.
            context = Context(context)
            context[context.TARGET_CONTEXT_PROPERTY] = self.GetName()
            context[context.TMPDIR_CONTEXT_PROPERTY] \
                = self._GetTemporaryDirectory()
            context[context.DB_PATH_CONTEXT_PROPERTY] \
                = descriptor.GetDatabase().GetPath()
            # Set up any required resources.
            self.__SetUpResources(descriptor, context)
            # Make the ID of the test available.
            context[context.ID_CONTEXT_PROPERTY] = descriptor.GetId()
            # Note the start time.
            result[Result.START_TIME] = qm.common.format_time_iso()
            # Run the test.
            try:
                descriptor.Run(context, result)
            finally:
                # Note the end time.
                result[Result.END_TIME] = qm.common.format_time_iso()
        except KeyboardInterrupt:
            result.NoteException(cause = "Interrupted by user.")
            # We received a KeyboardInterrupt, indicating that the
            # user would like to exit QMTest.  Ask the execution
            # engine to stop.
            if self.__engine:
                self.__engine.RequestTermination()
        except qm.platform.SignalException, e:
            # Note the exception.
            result.NoteException(cause = str(e))
            # If we get a SIGTERM, propagate it so that QMTest
            # terminates.
            if e.GetSignalNumber() == signal.SIGTERM:
                # Record the result so that the traceback is
                # available.
                self._RecordResult(result)
                # Ask the execution engine to stop running tests.
                if self.__engine:
                    self.__engine.RequestTermination()
                # Re-raise the exception.
                raise
        except self.__ResourceSetUpException, e:
            result.SetOutcome(Result.UNTESTED)
            result[Result.CAUSE] = qm.message("failed resource")
            result[Result.RESOURCE] = e.resource
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

        returns -- If at attempt to set up the resource has already
        been made, returns a tuple '(resource, outcome, properties)'.
        The 'resource' is the 'Resource' object itself, but may be
        'None' if the resource could not be set up.  The 'outcome'
        indicates the outcome that resulted when the resource was set
        up.  The 'properties' are a map from strings to strings
        indicating properties added by this resource.

        If the resource has not been set up, but _BeginResourceSetUp
        has already been called for the resource, then the contents of
        the tuple will all be 'None'.

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


    def _FinishResourceSetUp(self, resource, result, properties):
        """Finish setting up a resource.

        'resource' -- The 'Resource' itself.
        
        'result' -- The 'Result' associated with setting up the
        resource.

        'properties' -- A dictionary of additional context properties
        that should be provided to tests that depend on this resource.

        returns -- A tuple of the same form as is returned by
        '_BeginResourceSetUp' when the resource has already been set
        up."""

        # The temporary directory is not be preserved; there is no
        # guarantee that it will be the same in a test that depends on
        # this resource as it was in the resource itself.
        del properties[Context.TMPDIR_CONTEXT_PROPERTY]
        # Similarly, the ID property should be the name of the dependent
        # entity, not the name of the reosurce.
        del properties[Context.ID_CONTEXT_PROPERTY]
        rop = (resource, result.GetOutcome(), properties)
        self.__resources[result.GetId()] = rop
        self.__order_of_resources.append(result.GetId())
        return rop


    def __SetUpResources(self, descriptor, context):
        """Set up all the resources associated with 'descriptor'.

        'descriptor' -- The 'TestDescriptor' or 'ResourceDescriptor'
        indicating the test or resource that is about to be run.

        'context' -- The 'Context' in which the resources will be
        executed.

        returns -- A tuple of the same form as is returned by
        '_BeginResourceSetUp' when the resource has already been set
        up."""
        
        # See if there are resources that need to be set up.
        for resource in descriptor.GetResources():
            (r, outcome, resource_properties) \
                = self._SetUpResource(resource, context)
            
            # If the resource was not set up successfully,
            # indicate that the test itself could not be run.
            if outcome != Result.PASS:
                raise self.__ResourceSetUpException, resource
            # Update the list of additional context properties.
            context.update(resource_properties)

        return context
    
        
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
        # Set up the context.
        wrapper = Context(context)
        result = Result(Result.RESOURCE_SETUP, resource_name, Result.PASS)
        resource = None
        # Get the resource descriptor.
        try:
            resource_desc = self.GetDatabase().GetResource(resource_name)
            # Set up the resources on which this resource depends.
            self.__SetUpResources(resource_desc, wrapper)
            # Make the ID of the resource available.
            wrapper[Context.ID_CONTEXT_PROPERTY] = resource_name
            # Set up the resource itself.
            resource_desc.SetUp(wrapper, result)
            # Obtain the resource within the try-block so that if it
            # cannot be obtained the exception is handled below.
            resource = resource_desc.GetItem()
        except self.__ResourceSetUpException, e:
            result.Fail(qm.message("failed resource"),
                        { result.RESOURCE : e.resource })
        except NoSuchResourceError:
            result.NoteException(cause="Resource is missing from the database.")
            self._RecordResult(result)
            return (None, result, None)
        except qm.test.base.CouldNotLoadExtensionError, e:
            result.NoteException(e.exc_info,
                                 cause = "Could not load extension class")
        except KeyboardInterrupt:
            result.NoteException()
            # We received a KeyboardInterrupt, indicating that the
            # user would like to exit QMTest.  Ask the execution
            # engine to stop.
            if self.__engine:
                self.__engine.RequestTermination()
        except:
            result.NoteException()
        # Record the result.
        self._RecordResult(result)
        # And update the table of available resources.
        return self._FinishResourceSetUp(resource, result,
                                         wrapper.GetAddedProperties())


    def _CleanUpResource(self, name, resource):
        """Clean up the 'resource'.

        'resource' -- The 'Resource' that should be cleaned up.

        'name' -- The name of the resource itself."""

        result = Result(Result.RESOURCE_CLEANUP, name)
        # Clean up the resource.
        try:
            val = resource.CleanUp(result)
        except:
            result.NoteException()
        self._RecordResult(result)


    def _GetTemporaryDirectory(self):
        """Return the path to a temporary directory.

        returns -- The path to a temporary directory to pass along to
        tests and resources via the 'TMPDIR_CONTEXT_PROPERTY'."""
        
        raise NotImplementedError

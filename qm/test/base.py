########################################################################
#
# File:   base.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   Base interfaces and classes.
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

import os
import qm
import qm.attachment
import qm.graph
import qm.label
import qm.xmlutil
import string
import sys
import types

########################################################################
# constants
########################################################################

standard_test_class_names = [
    "command.ExecTest",
    "command.CommandTest",
    "command.ScriptTest",
    "python.ExecTest",
    "python.ExceptionTest",
    "python.StringExceptionTest",
    ]
"""A list of names of standard test classes."""

standard_action_class_names = [
    "temporary.TempDirectoryAction",
    ]
"""A list of names of standard action classes."""

dtds = {
    "action": "-//Software Carpentry//QMTest Action V0.1//EN",
    "result": "-//Software Carpentry//QMTest Result V0.1//EN",
    "suite": "-//Software Carpentry//QMTest Suite V0.1//EN",
    "test": "-//Software Carpentry//QMTest Test V0.1//EN",
    }
"""A mapping for DTDs used by QMTest.

Keys are DTD types ("action", "result", etc).  Values are the
corresponding DTD public identifiers."""

########################################################################
# exceptions
########################################################################

class NoSuchTestError(Exception):
    """The specified test does not exist."""

    pass



class NoSuchSuiteError(Exception):
    """The specified suite does not exist."""

    pass



class NoSuchActionError(Exception):
    """The specified action does not exist."""

    pass



########################################################################
# classes
########################################################################

class Attachment(qm.attachment.Attachment):
    """A file attachment.

    A file attachment to a test description may include data in-line, as
    part of the test description, or may reference external data.  For
    instance, in the XML test database impelementation, a test
    description may include attachment data for its arguments directly
    in the XML file, or may reference data in another file stored in the
    test database.

    To store in-line data with the attachment, use the 'data'
    attribute.  To reference external data, set the 'location' to the
    data's location as presented in the test specification.  In the
    latter case, some other agent must set the 'path' attribute of the
    attribute object to the full path to the attachment file, since the
    attachment doesn't have the necessary context."""

    def __init__(self,
                 mime_type=None,
                 description="",
                 file_name="",
                 data=None,
                 location=None):
        """Creata a new attachment.

        'data' -- The attachment data, or 'None' if it's stored in an
        external file.

        'location' -- The name (not generally a full path) of the
        external file containing the attachment data, or 'None'.  If
        this option is specified, the caller is responsible for setting
        the 'path' attribute of the new attachment object to the full
        path to the data file."""

        # Check semantics.
        assert data is not None or location is not None
        assert data is None or location is None

        # Perform base class initialization.
        qm.attachment.Attachment.__init__(self, mime_type,
                                          description, file_name)
        if data is not None:
            self.data = data
        else:
            self.location = location
        

    def GetData(self):
        if hasattr(self, "data"):
            return self.data
        else:
            # Read the data from the external file.
            return open(self.path, "r").read()


    def GetDataSize(self):
        if hasattr(self, "data"):
            return len(data)
        else:
            # Examine the external file.
            return os.stat(self.path)[6]


    def MakeDomNode(self, document):
        if hasattr(self, "data"):
            # Include in-line attachment data.
            return qm.attachment.make_dom_node(self, document,
                                               data=self.data)
        else:
            # Simply specify the location in the DOM tree.  The full
            # path is context-dependent and shouldn't be stored.
            return qm.attachment.make_dom_node(self, document,
                                               location=self.location)



class InstanceBase:
    """Common base class for test and action objects."""

    def __init__(self,
                 instance_id,
                 class_name,
                 arguments):
        validate_id(instance_id)
        self.__id = instance_id
        self.__class_name = class_name
        self.__arguments = arguments
        self.__working_directory = None


    def GetClassName(self):
        """Return the name of the class of which this is an instance."""

        return self.__class_name


    def GetClass(self):
        """Return the test class of this test."""

        return get_class(self.GetClassName())
    

    def GetArguments(self):
        """Returns a map from argument names to values."""

        return self.__arguments


    def GetId(self):
        """Return the ID for this instance."""
        
        return self.__id


    def SetWorkingDirectory(self, directory_path):
        """Set the working directory of the test to 'directory_path'."""

        self.__working_directory = directory_path
        # Set the full path for each attachment in a test argument that
        # references attachment data by location.
        self.__SetAttachmentPaths(self.__arguments.values())


    def GetWorkingDirectory(self):
        """Return the working directory to use when the test is run.

        returns -- The working directory, or 'None' if none was
        specified."""

        return self.__working_directory


    # Helper functions.

    def __MakeItem(self):
        """Construct the underlying user test or action object."""

        arguments = self.GetArguments().copy()

        # Use a default value for each field for which an argument was
        # not specified.
        klass = self.GetClass()
        for field in klass.fields:
            field_name = field.GetName()
            if not arguments.has_key(field_name):
                arguments[field_name] = field.GetDefaultValue()

        return apply(klass, [], arguments)


    def __SetAttachmentPaths(self, value):
        """Set full attachment paths.

        If 'value' is an 'Attachment' instance, the 'path' attribute is
        set.  If 'value' is a sequence type, the 'path' attribute is set
        for any 'Attachment' elements in it."""

        if type(value) == types.InstanceType \
           and isinstance(value, Attachment) \
           and hasattr(value, "location"):
            # It's an attachment type, and has the 'location' attribute
            # set, so set the path.
            value.path = os.path.join(self.__working_directory,
                                      value.location)
        elif type(value) == types.ListType \
             or type(value) == types.TupleType:
            # It's a sequence.  Call ourselves recursively on its
            # elements. 
            for element in value:
                self.__SetAttachmentPaths(element)



class Test(InstanceBase):
    """A test instance."""

    def __init__(self,
                 test_id,
                 test_class_name,
                 arguments,
                 prerequisites={},
                 categories=[],
                 actions=[]):
        """Create a new test instance.

        'test_id' -- The test ID.

        'test_class_name' -- The name of the test class of which this is
        an instance.

        'arguments' -- This test's arguments to the test class.

        'prerequisites' -- A mapping from prerequisite test ID to
        required outcomes.

        'categories' -- A sequence of names of categories to which this
        test belongs.

        'actions' -- A sequence of IDs of actions to run before and
        after the test is run."""

        # Initialize the base class.
        InstanceBase.__init__(self, test_id, test_class_name, arguments)
        self.__prerequisites = prerequisites
        self.__categories = categories
        self.__actions = actions

        # Don't instantiate the test yet.
        self.__test = None


    def GetTest(self):
        """Return the underlying user test object."""

        # Perform just-in-time instantiation.
        if self.__test is None:
            self.__test = self._InstanceBase__MakeItem()

        return self.__test


    def GetCategories(self):
        """Return the names of categories to which the test belongs."""

        return self.__categories
    

    def IsInCategory(self, category):
        """Return true if this test is in 'category'."""

        return category in self.__categories


    def GetPrerequisites(self, absolute=0):
        """Return a map from prerequisite test IDs to required outcomes.

        'absolute' -- If true, present the prerequisite test IDs as
        absolute IDs.  Otherwise, the are presented as IDs relative to
        this test."""

        if absolute:
            rel = qm.label.MakeRelativeTo(qm.label.dirname(self.GetId()))
            prerequisites = {}
            for test_id, outcome in self.__prerequisites.items():
                prerequisites[rel(test_id)] = outcome
            return prerequisites
        else:
            return self.__prerequisites


    def GetActions(self, absolute=0):
        """Return a sequence of IDs of actions.

        'absolute' -- If true, present the prerequisite test IDs as
        absolute IDs.  Otherwise, the are presented as IDs relative to
        this test."""

        if absolute:
            rel = qm.label.MakeRelativeTo(qm.label.dirname(self.GetId()))
            return map(rel, self.__actions)
        else:
            return self.__actions


    def Run(self, context):
        """Execute this test.

        'context' -- Information about the environment in which the test
        is being executed.
        
        returns -- A 'Result' describing the outcome of the test."""

        working_directory = self.GetWorkingDirectory()
        if working_directory is not None:
            # Remember the previous working directory so we can restore
            # it.
            old_working_directory = os.getcwd()
            try:
                # Change to the working directory appropriate for this
                # test.
                os.chdir(working_directory)
                # Run the test.
                return self.GetTest().Run(context)
            finally:
                # Restore the working directory.
                os.chdir(old_working_directory)
        else:
            # Just run the test without mucking with directories.
            return self.GetTest().Run(context)



class Action(InstanceBase):
    """An action instance."""

    def __init__(self,
                 action_id,
                 action_class_name,
                 arguments):
        """Create a new action instance.

        'action_id' -- The action ID.

        'action_class_name' -- The name of the action class of which
        this is an instance.

        'arguments' -- This test's arguments to the test class."""

        # Initialize the base class.
        InstanceBase.__init__(self, action_id, action_class_name, arguments)
        # Don't instantiate the action yet.
        self.__action = None


    def GetAction(self):
        """Return the underlying user action object."""

        # Perform just-in-time instantiation.
        if self.__action is None:
            self.__action = self._InstanceBase__MakeItem()

        return self.__action


    def DoSetup(self, context):
        self.__Do(context, mode="setup")


    def DoCleanup(self, context):
        self.__Do(context, mode="cleanup")


    def __Do(self, context, mode):
        """Execute a setup action.

        'context' -- Information about the environment in which the test
        is being executed.
        
        'mode' -- Either "setup" or "cleanup".

        returns -- A 'Result' describing the outcome of the test."""

        assert mode is "setup" or mode is "cleanup"

        working_directory = self.GetWorkingDirectory()
        old_working_directory = None
        action = self.GetAction()

        try:
            if working_directory is not None:
                # Remember the previous working directory so we can
                # restore it.
                old_working_directory = os.getcwd()
                # Change to the working directory appropriate for this
                # test.
                os.chdir(working_directory)
            # Run the action function.
            if mode is "setup":
                return action.DoSetup(context)
            else:
                return action.DoCleanup(context)
        finally:
            if old_working_directory is not None:
                # Restore the working directory.
                os.chdir(old_working_directory)



class Suite:
   """A group of tests."""

   def __init__(self, suite_id, test_ids=[], suite_ids=[], implicit=0): 
       """Create a new test suite instance.

       'suite_id' -- The ID of the new suite.

       'test_ids' -- A sequence of IDs of tests contained in the suite.

       'suite_ids' -- A sequence of IDs of suites contained in the
       suite.

       'implicit' -- If true, this is an implicit suite.  It contains
       all tests whose IDs have this suite's ID as a prefix."""

       self.__id = suite_id
       self.__test_ids = list(test_ids)
       self.__suite_ids = list(suite_ids)
       self.__implicit = implicit
       

   def GetId(self):
       """Return the ID for this test suite."""

       return self.__id


   def IsImplicit(self):
       """Return true if this is an implicit test suite.

       Implicit test suites should not be explicitly editable."""

       return self.__implicit


   def GetTestIds(self):
       """Return a sequence of the test IDs of the tests in this suite.

       returns -- A sequence of IDs of all tests in this suite.  If this
       suite contains other suites, these are expanded recursively to
       produce the full list of tests.  No test will appear more than
       once.  Test IDs are relative to the top of the test database."""

       database = get_database()
       # 'rel' converts IDs relative to this suite to IDs relative to
       # the top of the test database.
       dir_id = qm.label.split(self.GetId())[0]
       rel = qm.label.MakeRelativeTo(dir_id)
       # Instead of keeping a list of test IDs, we'll build a map, to
       # assist with skipping duplicates.  The keys are test IDs (we
       # don't care about the values).
       ids = {}
       # Start by entering the tests explicitly part of this suite.
       for test_id in map(rel, self.__test_ids):
           ids[test_id] = None
       # Now loop over suites contained in this suite.
       for suite_id in map(rel, self.__suite_ids):
           suite = database.GetSuite(suite_id)
           # Get the test IDs in the contained suite.
           test_ids_in_suite = suite.GetTestIds()
           # Make note of them.
           for test_id in test_ids_in_suite:
               ids[test_id] = None
       # All done.
       return ids.keys()


   def GetRawTestIds(self):
       """Return the IDs of tests explicitly part of this suite.

       returns -- A list of tests explicitly in this suite.  Does not
       include IDs of tests that are included in this suite via other
       suites.  Test IDs are relative to the path containing this
       suite."""

       return self.__test_ids


   def GetRawSuiteIds(self):
       """Return the IDs of suites explicitly part of this suite.

       returns -- A list of suites explicitly in this suite.  Does not
       include IDs of suites that are included via other suites.  Suite
       IDs are relative to the path contianing this suite."""

       return self.__suite_ids



class Database:
    """A database containing tests."""

    def GetClassPaths(self):
        """Return paths to search for class files.

        returns -- A sequence of paths to add to the classpath when
        loading test and action classes."""

        return []


    def HasTest(self, test_id):
        """Return true if the database has a test with ID 'test_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.HasTest"


    def GetTest(self, test_id):
        """Return a 'Test' instance for test ID 'test_id'.

        raises -- 'NoSuchTestError' if there is no test in the database
        with ID 'test_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetTest"


    def WriteTest(self, test):
        """Store a test in the database.

        'test' -- A test to write.  It may be a new version of an
        existing test, or a new test."""

        raise qm.MethodShouldBeOverriddenError, "Database.WriteTest"


    def RemoveTest(self, test_id):
        """Remove the test with ID 'test_id' from the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveTest"


    def GetTestIds(self, path="."):
        """Return test IDs of all tests relative to 'path'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetTestIds"


    def HasSuite(self, suite_id):
        """Return true if the database has a suite with ID 'suite_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.HasSuite"


    def GetSuite(self, suite_id):
        """Return a 'Suite' instance for suite ID 'suite_id'.

        raises -- 'NoSuchSuiteError' if there is no suite in the
        database with ID 'suite_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuite"


    def WriteSuite(self, suite):
        """Store a test suite in the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.WriteSuite"


    def RemoveSuite(self, suite_id):
        """Remove the test suite with ID 'suite_id' from the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveSuite"


    def GetSuiteIds(self, path=".", implicit=0):
        """Return suite IDs of all test suites relative to 'path'.

        'implicit' -- If true, include implicit test suites
        corresponding to directories in the space of test and suite
        IDs."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuiteIds"


    def HasAction(self, action_id):
        """Return true if the database has a action with ID 'action_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.HasAction"


    def GetAction(self, action_id):
        """Return a 'Action' instance for action ID 'action_id'.

        raises -- 'NoSuchActionError' if there is no action in the
        database with ID 'action_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetAction"


    def WriteAction(self, action):
        """Store a action in the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.WriteAction"


    def RemoveAction(self, action_id):
        """Remove the action with ID 'action_id' from the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveAction"


    def GetActionIds(self, path="."):
        """Return action IDs of all actions relative to 'path'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetActionIds"


    def SetAttachmentData(self, attachment, data, item_id):
        """Store attachment data to the database.

        'attachment' -- An 'Attachment' instance.

        'data' -- The attachment data as a string.

        'item_id' -- A test or action ID associated with this attachment."""

        raise qm.MethodShouldBeOverriddenError, "Database.SetAttachmentData"


class Result:
    """The result of running a test.

    A result object stores an outcome"""

    # Outcome constants.
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    UNTESTED = "UNTESTED"

    outcomes = [ PASS, FAIL, ERROR, UNTESTED ]


    def __init__(self, outcome, **properties):
        """Initialize a new result object."""

        self.__outcome = outcome
        self.__properties = properties


    def __str__(self):
        parts = map(lambda kv: "%s=%s" % (kv[0], repr(kv[1])),
                    self.__properties.items())
        parts = [ self.__outcome ] + parts
        return "Result(%s)" % string.join(parts, ", ")


    def GetOutcome(self):
        """Return the outcome of this test result."""

        return self.__outcome


    # Methods to emulate a (write-only) map.

    def __setitem__(self, key, value):
        self.__properties[key] = value


    def __delitem__(self, key):
        del self.__properties[key]



class ResultWrapper:
    """A wrapper around a 'Result' object.

    This class allows us to record additional information along with the
    raw result generated by the test class."""

    def __init__(self, test_id, context, result):
        """Create a new test result wrapper.

        'test_id' -- The ID of the test being run.

        'context' -- The context in use when the test was run.

        'result' -- The 'Result' object returned by the test class's
        'Run' method."""

        self.__test_id = test_id
        self.__context = context
        self.__result = result


    def __str__(self):
        return "ResultWrapper(%s, %s)" \
               % (self.__test_id, str(self.__result))


    def __repr__(self):
        return str(self)


    def GetOutcome(self):
        """Return the outcome of this test result."""

        return self.__result._Result__outcome


    def GetTestId(self):
        """Return the ID of the test for which this is a result."""
        
        return self.__test_id


    def GetContext(self):
        """Return the context in use when this result was generated."""

        return self.__context


    def GetContextProperties(self):
        """Return the attributes added to the context by this test."""

        return self.__context.GetAddedProperties()


    def MakeDomNode(self, document):
        """Generate a DOM element node for this result.

        'document' -- The containing DOM document."""

        # The node is a result element.
        element = document.createElement("result")
        element.setAttribute("id", self.GetTestId())
        # Create and add an element for the outcome.
        outcome_element = document.createElement("outcome")
        text = document.createTextNode(str(self.GetOutcome()))
        outcome_element.appendChild(text)
        element.appendChild(outcome_element)
        # Add a property element for each property.
        for key, value in self.items():
            property_element = document.createElement("property")
            # The property name is an attribute.
            property_element.setAttribute("name", str(key))
            # The property value is contained in a text mode.
            text = document.createTextNode(str(value))
            property_element.appendChild(text)
            # Add the property element to the result node.
            element.appendChild(property_element)

        return element


    # Methods to emulate a (read-only) map, to access the properties of
    # the underlying 'Result' object.

    def __getitem__(self, key):
        return self.__result._Result__properties[key]


    def get(self, key, default=None):
        return self.__result._Result__properties.get(key, default)


    def has_key(self, key):
        return self.__result._Result__properties.has_key(key)


    def items(self):
        return self.__result._Result__properties.items()



class Context:
    """Test-time and local configuration for tests.

    A 'Context' object contains all of the information a test needs to
    execute, beyond what is stored as part of the test specification
    itself.  Information in the context can include,

      * Local (per-user, etc.) configuration, such as where to find the
        tested program.

      * Environmental information, such as which machine the test is
        running on.

      * One-time configuration, including test arguments specified on
        the command line.

    A 'Context' object is effectively a mapping object whose keys must
    be labels and values must be strings."""

    def __init__(self, **initial_attributes):
        """Construct a new context.

        'initial_attributes' -- Initial key/value pairs to include in
        the context."""

        self.__attributes = initial_attributes
        for key, value in self.__attributes.items():
            self.ValidateKey(key)

        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            self.ValidateKey(option)
            value = qm.rc.Get(option, None)
            assert value is not None
            self.__attributes[option] = value

        self.__temporaries = {}


    # Methods to simulate a map object.

    def __getitem__(self, key):
        return self.__attributes[key]


    def __setitem__(self, key, value):
        self.ValidateKey(key)
        self.__attributes[key] = value


    def __delitem__(self, key):
        del self.__attributes[key]


    def has_key(self, key):
        return self.__attributes.has_key(key)


    def keys(self):
        return self.__attributes.keys()


    def values(self):
        return self.__attributes.values()


    def items(self):
        return self.__attributes.items()


    def copy(self):
        # No need to re-validate.
        result = Context()
        result.__attributes = self.__attributes.copy()
        return result


    # Helper methods.

    def ValidateKey(self, key):
        """Validate 'key'.

        raises -- 'ValueError' if 'key' is not a string.

        raises -- 'RuntimeError' if 'key' is not a valid label
        (including periods)."""

        if not isinstance(key, types.StringType):
            raise ValueError, "context key must be a string"
        if not qm.label.is_valid(key, allow_separator=1):
            raise ValueError, \
                  qm.error("invalid context key", key=key)



class ContextWrapper:
    """Wrapper for 'Context' objects.

    A 'ContextWrapper' allows additional properties to be added
    temporarily to a context.  It also keeps new properties added to the
    context separate from those that were specified when the context
    wrapper was intialized.

    There are three sets of properties in a context wrapper.

      1. Properties of the wrapped 'Context' object.

      2. Extra properties specified when the wrapper was created.

      3. Properties added (using '__setitem__') after the wrapper was
         created.

    A property in 3 shadows a property with the same name in 1 or 2,
    and a property in 2 similarly shadows a property with the same name
    in 1."""

    def __init__(self, context, extra_properties={}):
        """Create a context wrapper.

        'context' -- The wrapped 'Context' object.

        'extra_properties' -- Additional properties."""

        self.__context = context
        self.__extra = extra_properties.copy()
        self.__added = {}


    def GetAddedProperties(self):
        """Return the properties added after this wrapper was created."""

        return self.__added


    def __getitem__(self, key):
        """Return a property value."""

        # Check added properties first.
        try:
            return self.__added[key]
        except KeyError:
            pass
        # Then check properties added during initialization.
        try:
            return self.__extra[key]
        except KeyError:
            pass
        # Finally check properties of the wrapped context object.
        return self.__context[key]


    def __setitem__(self, key, value):
        """Set a property value."""

        self.__context.ValidateKey(key)
        # All properties set via '__setitem__' are stored here.
        self.__added[key] = value


    def __delitem__(self, key):
        try:
            del self.__added[key]
        except KeyError:
            # A property cannot be deleted unless it was set with
            # '__setitem__'.
            if self.__extra.has_key(key) or self.__context.has_key(key):
                raise RuntimeError, \
                      qm.error("context attribute cannot be deleted",
                               attribute=key)
            else:
                # The property didn't exist at all.
                raise
           

    def has_key(self, key):
        return self.__added.has_key(key) \
               or self.__extra.has_key(key) \
               or self.__context.has_key(key)


    def keys(self):
        return self.__added.keys() \
               + self.__extra.keys() \
               + self.__context.keys()


    def values(self):
        values = []
        for key in self.keys():
            values.append(self.getitem(key))
        return values


    def items(self):
        items = []
        for key in self.keys():
            items.append(( key, self.getitem(key) ))
        return items


    def copy(self):
        result = ContextWrapper(self.__context, self.__extra)
        result.__added = self.__added.copy()
        return result



class PrerequisiteMapAdapter:
    """A map-like object associating prerequisites with test IDs."""

    def __init__(self, database):
        """Construct a new map."""
        
        self.__database = database


    def __getitem__(self, test_id):
        """Return a sequence of IDs of prerequisite tests of 'test_id'."""

        test = self.__database.GetTest(test_id)
        return test.GetPrerequisites(absolute=1).keys()



class Engine:
   """The test execution engine."""

   def __init__(self, database):
       """Create a new testing engine.

       'database' -- The test database containing the tests on which
       this engine operates."""

       self.__database = database


   def RunTest(self, test_id, context):
       """Run a test.

       'test_id' -- The ID of the test to execute.  

       'context' -- Context to pass to the test.

       returns -- A 'Result' object."""

       results = self.RunTests([ test_id ], context)
       return results[test_id]


   def RunTests(self, test_ids, context, progress_callback=None):
       """Execute several tests.

       'test_ids' -- A sequence of IDs of the tests to run.

       'context' -- Context to pass to the tests.

       'progress_callback' -- If not 'None', a callable that is invoked
       to report test execution progress.  The function takes two
       parameters.  The first is a test ID.  The function is invoked
       once before a test is run, with 'None' as the second argument.
       After the test has been run, the function is called again, with a
       'Result' object as the second argument.

       returns -- A map from test IDs to 'Result' objects of tests that
       were run.  The tests that were run is a superset of
       'test_ids'."""

       # For convenience, set 'progress_callback' to a do-nothing
       # function if it is 'None'.
       if progress_callback is None:
           def null_function(message):
               pass
           progress_callback = null_function

       # Construct a map-like object for test prerequisites.
       prerequisite_map = PrerequisiteMapAdapter(self.__database)
       # Perform a topological sort to determine the tests that will be
       # run and the order in which to run them.  The sort may return a
       # superset of the original 'test_ids'.
       test_ids = qm.graph.topological_sort(test_ids,
                                            prerequisite_map)

       # This map associates a test with each test ID.
       tests = {}

       # This map contains information about when cleanup actions should
       # be run.  There is an entry for each action referenced by at
       # least one of the tests that will be run.  The key is the action
       # ID, and the value is the ID of the test after which the cleanup
       # action must be run.
       cleanup_action_map = {}

       # Loop over all the tests, in the order that they will be run.
       for test_id in test_ids:
           # Look up the test.
           test = self.__database.GetTest(test_id)
           # Store it.
           tests[test_id] = test
           # Loop over all the actions it references.
           for action_id in test.GetActions(absolute=1):
               # The cleanup action should be run after this test.
               # Another, earlier test may have been here, but this test
               # will be run later, so reschedule the cleanup.
               cleanup_action_map[action_id] = test_id

       # This map contains the context properties that were added by
       # each setup action that has been run so far.  A key in this map
       # is an action ID, and the corresponding value represents the
       # properties that the setup action added to the context (as a map
       # from property name to value).  If the setup action failed, the
       # corresponding value is 'None'.
       setup_attributes = {}

       # Run tests.  Store the results in an ordered map so that we can
       # retrieve results by test ID efficiently, and also preserve the
       # order in which tests were run.
       results = qm.OrderedMap()
       for test_id in test_ids:
           test = tests[test_id]
           result = None
           action_ids = test.GetActions(absolute=1)

           # Prerequisite tests and setup actions may add additional
           # properties to the context which are visible to this test.
           # Accumulate those properties in this map.
           extra_context_properties = {}
           
           # Check that all the prerequisites of this test have produced
           # the expected outcomes.  If a prerequisite produced a
           # different outcome, generate an UNTESTED result and stop
           # processing prerequisites.
           
           prerequisites = test.GetPrerequisites(absolute=1)
           for prerequisite_id, outcome in prerequisites.items():
               # Because of the topological sort, the prerequisite
               # should already have been run.
               assert results.has_key(prerequisite_id)
               # Did the prerequisite produce the required outcome?
               prerequisite_result = results[prerequisite_id]
               if prerequisite_result.GetOutcome() != outcome:
                   # No.  As a result, we won't run this test.  Create
                   # a result object with the UNTESTED outcome.
                   result = Result(outcome=Result.UNTESTED,
                                   failed_prerequisite=prerequisite_id)
                   break
               else:
                   # Properties added to the context by the prerequisite
                   # test are to be available to this test.
                   extra_context_properties.update(
                       prerequisite_result.GetContextProperties())

           # Do setup actions (unless a prerequisite failed).  This is
           # done only for the first test that references the action.
           # If a setup action fails, generate an UNTESTED result for
           # this test and stop processing setup actions.

           if result is not None:
               # Don't bother with setup actions if we already have a
               # test result indicating a failed prerequisite.
               pass
           else:
               # Loop over actions referenced by this test.
               for action_id in action_ids:
                   # Have we already done the setup for this action?
                   if setup_attributes.has_key(action_id):
                       # The action has already been run.  Look up the
                       # context properties that the setup function
                       # generated.
                       added_attributes = setup_attributes[action_id]
                       if added_attributes is None:
                           # The action failed when it was run, so don't
                           # run this test.
                           result = Result(outcome=Result.UNTESTED,
                                           failed_setup_action=action_id)
                           break
                   else:
                       # This is the first test to reference this action.
                       # Look up the action.
                       try:
                           action = self.__database.GetAction(action_id)
                       except NoSuchActionError:
                           # Oops, it's missing.  Don't run the test.
                           result = Result(outcome=Result.UNTESTED,
                                           missing_action=action_id)
                           break

                       # Make another context wrapper for the setup
                       # function.  The setup function shouldn't see any
                       # properties added by prerequisite tests or other
                       # actions.  Also, we need to isolate the
                       # properties added by this function.
                       wrapper = ContextWrapper(context)

                       # Do the setup action.
                       progress_callback("action %-43s: " % action_id)
                       try:
                           action.DoSetup(wrapper)
                       except:
                           # The action raised an exception.  Don't run
                           # the test.
                           progress_callback("SETUP ERROR\n")
                           result = Result(Result.UNTESTED,
                                           failed_setup_action=action_id)
                           # Add some information about the traceback.
                           exc_info = sys.exc_info()
                           result["setup_exception_" + action_id] = \
                                            "%s: %s" % exc_info[:2]
                           result["setup_traceback_" + action_id] = \
                                            qm.format_traceback(exc_info)
                           # Record 'None' for this action, indicating
                           # that it failed.
                           setup_attributes[action_id] = None
                           break
                       else:
                           # The action completed successfully.
                           progress_callback("SETUP\n")
                           # Extract the context properties added by the
                           # setup function.
                           added_attributes = wrapper.GetAddedProperties()
                           # Store them for other tests that reference
                           # this action.
                           setup_attributes[action_id] = added_attributes

                   # Accumulate the properties generated by this setup
                   # action. 
                   extra_context_properties.update(added_attributes)

           # We're done with prerequisites and setup actions, and it's
           # time to run the test.
           progress_callback("test %-45s: " % test_id)

           # If we don't already have a result (all prerequisites
           # checked out and setup actions succeeded), actually run the
           # test.
           if result is None:
               # Create a context wrapper that we'll use when running
               # the test.  It includes the original context, plus
               # additional properties added by prerequisite tests and
               # setup actions.
               context_wrapper = ContextWrapper(context,
                                                extra_context_properties)
               try:
                   # Run the test.
                   result = test.Run(context_wrapper)
               except:
                   # The test raised an exception.  Create a result
                   # object for it.
                   result = make_result_for_exception(sys.exc_info())
               else:
                   # The test ran to completion.  It should have
                   # returned a 'Result' object.
                   if not isinstance(result, qm.test.base.Result):
                       # Something else.  That's an error.
                       raise RuntimeError, \
                             qm.error("invalid result",
                                      id=test_id,
                                      test_class=test.GetClass().__name__,
                                      result=repr(result))

           # Invoke the callback.
           progress_callback(result.GetOutcome() + "\n")

           # Finally, run cleanup actions for this test.  Run them no
           # matter what the test outcome is, even if prerequisites or
           # setup actions failed.  If a cleanup action fails, try
           # running the other cleanup actions anyway.

           # Loop over actions referenced by this test.
           for action_id in action_ids:
               if cleanup_action_map[action_id] != test_id:
                   # This is not the last test to require this cleanup
                   # action, so don't do it yet.
                   continue
               if not setup_attributes.has_key(action_id):
                   # The setup action was never run, so don't run the
                   # cleanup action.
                   continue
               # Loop up the action.
               action = self.__database.GetAction(action_id)

               # Create a context wrapper for running the cleanup
               # method.  It includes the original context, plus any
               # additional properties added by the setup method of the
               # same action.
               properties = setup_attributes[action_id]
               if properties is None:
                   # The setup method failed, but we're running the
                   # cleanup method anyway.  Don't use any extra
                   # properties.
                   properties = {}
               wrapper = ContextWrapper(context, properties)

               # Now run the cleanup action.
               progress_callback("action %-43s: " % action_id)
               try:
                   action.DoCleanup(wrapper)
               except:
                   # It raised an exception.  No biggie; just record
                   # some information in the result.
                   progress_callback("CLEANUP ERROR\n")
                   exc_info = sys.exc_info()
                   result["cleanup_exception_" + action_id] = \
                                    "%s: %s" % exc_info[:2]
                   result["cleanup_traceback_" + action_id] = \
                                    qm.format_traceback(exc_info)
               else:
                   # The cleanup action succeeded.
                   progress_callback("CLEANUP\n")

           # Record the test ID and context by wrapping the result.
           result = ResultWrapper(test_id, context_wrapper, result)
           # Store the test result.
           results[test_id] = result

       return results


   def RunSuite(self, suite_id, context):
       """Execute a test suite.

       'suite_id' -- The ID of the suite to run.

       'context' -- Context to pass to the tests.

       returns -- A map from test IDs to 'Result' objects of tests that
       were run.  The tests that were run is a superset of the tests in
       'suite_id'."""

       suite = self.__database.GetSuite(suite_id)
       return self.RunTests(suite.GetTestIds(), context)



########################################################################
# functions
########################################################################

def validate_id(item_id):
    """Validate a test or action ID.

    raises -- 'RuntimeError' if 'item_id' is not a valid ID."""

    if not qm.label.is_valid(item_id, allow_separator=1):
        raise RuntimeError, qm.error("invalid id", id=item_id)


def make_result_for_exception(exc_info, cause=None, outcome=Result.ERROR):
    """Return a 'Result' object for a test that raised an exception.

    'exc_info' -- The exception triple as returned from 'sys.exc_info'.

    'cause' -- If not 'None', additional clarification to include in the
    result.

    returns -- A 'Result' object."""

    if cause is None:
        cause = "An exception occurred."
    return Result(outcome=Result.ERROR,
                  cause=cause,
                  exception="%s: %s" % exc_info[:2],
                  traceback=qm.format_traceback(exc_info))


def get_database():
    """Return the test database object."""

    assert _database is not None
    return _database


def get_class(class_name):
    """Return the test or action class named 'class_name'.

    'class_name' -- A fully-qualified Python class name.

    returns -- A class object for the requested class.

    raises -- 'ValueError' if 'class_name' is formatted incorrectly.

    raises -- 'ImportError' if 'class_name' cannot be loaded."""

    global __loaded_classes

    # Have we already loaded this test class?
    try:
        return __loaded_classes[class_name]
    except KeyError:
        # Nope; that's OK.
        pass

    # Extract paths from the 'QMTEST_CLASSPATH' environment variable. 
    try:
        user_class_path = os.environ["QMTEST_CLASSPATH"]
        user_class_path = string.split(user_class_path, ":")
    except KeyError:
        # The environment variable isn't set.
        user_class_path = []
    # The test database may also provide places for class files.
    database = get_database()
    extra_paths = database.GetClassPaths()
    # Construct the full set of paths to search in.
    paths = user_class_path + extra_paths + __builtin_class_path
    # Load it.
    klass = qm.common.load_class(class_name, paths)
    # Cache it.
    __loaded_classes[class_name] = klass
    # All done.
    return klass


def make_new_test(test_class_name, test_id):
    """Create a new test with default arguments.

    'test_class_name' -- The name of the test class of which to create a
    new test.

    'test_id' -- The test ID of the new test.

    returns -- A new 'Test' object."""

    test_class = get_class(test_class_name)
    # Make sure there isn't already such a test.
    database = get_database()
    if database.HasTest(test_id):
        raise RuntimeError, qm.error("test already exists",
                                     test_id=test_id)
    # Construct an argument map containing default values.
    arguments = {}
    for field in test_class.fields:
        name = field.GetName()
        value = field.GetDefaultValue()
        arguments[name] = value
    # Construct a default test instance.
    return Test(test_id, test_class_name, arguments, {}, [])


def make_new_action(action_class_name, action_id):
    """Create a new action with default arguments.

    'action_class_name' -- The name of the action class of which to
    create a new action.

    'action_id' -- The action ID of the new action.

    returns -- A new 'Action' object."""

    action_class = get_class(action_class_name)
    # Make sure there isn't already such a action.
    database = get_database()
    if database.HasAction(action_id):
        raise RuntimeError, qm.error("action already exists",
                                     action_id=action_id)
    # Construct an argument map containing default values.
    arguments = {}
    for field in action_class.fields:
        name = field.GetName()
        value = field.GetDefaultValue()
        arguments[name] = value
    # Construct a default action instance.
    return Action(action_id, action_class_name, arguments)


def load_outcomes(path):
    """Load test outcomes from a file.

    'path' -- Path to an XML results file.

    returns -- A map from test IDs to outcomes."""

    # Load full results.
    outcomes = load_results(path)
    # Replace full results with outcomes only.
    for test_id in outcomes.keys():
        outcomes[test_id] = outcomes[test_id].GetOutcome()
    return outcomes


def load_results(path):
    """Load test results from a file.

    'path' -- Path to an XML results file.

    returns -- A map from test IDs to 'ResultWrapper' objects."""
    
    results_document = qm.xmlutil.load_xml_file(path)
    # Extract the result elements.
    return __results_from_dom(results_document.documentElement)


def __results_from_dom(results_node):
    """Extract results from a results element.

    'results_node' -- A DOM node corresponding to a results element.

    returns -- A map from test IDs to 'ResultWrapper' objects."""

    assert results_node.tagName == "results"
    # Extract one result for each result element.
    results = {}
    for result_node in results_node.getElementsByTagName("result"):
        result = __result_from_dom(result_node)
        results[result.GetTestId()] = result
    return results


def __result_from_dom(result_node):
    """Extract a result from a result element.

    'result_node' -- A DOM node corresponding to a result element.

    returns -- A 'ResultWrapper' object."""

    assert result_node.tagName == "result"
    # Extract the outcome, and build a base 'Result' object.
    outcome = qm.xmlutil.get_dom_child_text(result_node, "outcome")
    result = Result(outcome)
    # Extract properties, one for each property element.
    for property_node in result_node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value
    # Extract the test ID.
    test_id = result_node.getAttribute("id")
    # FIXME: Load context?
    context = None
    # Construct a result wrapper around the result.
    return ResultWrapper(test_id, context, result)


########################################################################
# variables
########################################################################

_database = None
"""The global test database instance.

Use 'get_database' to access the global test database."""

__loaded_classes = {}
"""Cache of loaded test and action classes."""

__builtin_class_path = [
    qm.common.get_lib_directory("qm", "test", "classes"),
    ]
"""Standard paths to search for test and action classes."""

########################################################################
# initialization
########################################################################

qm.attachment.attachment_class = Attachment

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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

import cPickle
import cStringIO
import os
import qm
import qm.attachment
import qm.graph
import qm.label
import qm.platform
import qm.xmlutil
import string
import sys
import tempfile
import types

########################################################################
# constants
########################################################################

standard_test_class_names = [
    "command.ExecTest",
    "command.ShellCommandTest",
    "command.ShellScriptTest",
    "file.FileContentsTest",
    "python.ExecTest",
    "python.ExceptionTest",
    "python.StringExceptionTest",
    ]
"""A list of names of standard test classes."""

standard_resource_class_names = [
    "temporary.TempDirectoryResource",
    ]
"""A list of names of standard resource classes."""

dtds = {
    "resource":     "-//Software Carpentry//QMTest Resource V0.1//EN",
    "result":       "-//Software Carpentry//QMTest Result V0.2//EN",
    "suite":        "-//Software Carpentry//QMTest Suite V0.1//EN",
    "target":       "-//Software Carpentry//QMTest Target V0.1//EN",
    "test":         "-//Software Carpentry//QMTest Test V0.1//EN",
    }
"""A mapping for DTDs used by QMTest.

Keys are DTD types ("resource", "result", etc).  Values are the
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



class NoSuchResourceError(Exception):
    """The specified resource does not exist."""

    pass



class CommandFailedError(RuntimeError):
    """A command invocation of 'qmtest' failed."""

    def __init__(self, arguments, exit_code, stdout, stderr):
        """Create a new exception.

        'arguments' -- The list of arguments used to invoke the command.

        'exit_code' -- The command's exit code.
        
        'stdout' -- The contents of the command's standard output.

        'stderr' -- The contents of the command's standard error."""

        RuntimeError.__init__(self, "Command failed.")
        self.arguments = string.join(arguments, " ")
        self.exit_code = str(exit_code)
        self.stdout = stdout
        self.stderr = stderr



########################################################################
# classes
########################################################################

class InstanceBase:
    """Common base class for test and resource objects."""

    def __init__(self,
                 instance_id,
                 class_name,
                 arguments,
                 properties):
        validate_id(instance_id)
        self.__id = instance_id
        self.__class_name = class_name
        self.__arguments = arguments
        self.__working_directory = None
        self.__properties = properties.copy()


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


    def GetWorkingDirectory(self):
        """Return the working directory to use when the test is run.

        returns -- The working directory, or 'None' if none was
        specified."""

        return self.__working_directory


    def SetProperty(self, name, value):
        """Set a property.

        'name' -- The property name.  Must be a valid label.

        'value' -- The property value.  'value' is converted to a
        string.

        raises -- 'ValueError' if 'name' is not a valid label.

        If there is already a property named 'name', its value is
        replaced with 'value'."""

        name = str(name)
        value = str(value)
        if not qm.label.is_valid(name):
            raise ValueError, "%s is not a valid property name" % name
        self.__properties[name] = value


    def GetProperty(self, name, default=None):
        """Get a property value.

        'name' -- The property name.

        'default' -- The value to return if there is no property named
        'name'.

        returns -- The value of the 'name' property, or 'default' if
        there is no such property."""

        return self.__properties.get(name, default)


    def GetProperties(self):
        """Return a map from property names to values."""

        return self.__properties


    # Helper functions.

    def __MakeItem(self):
        """Construct the underlying user test or resource object."""

        arguments = self.GetArguments().copy()
        attachment_store = get_database().GetAttachmentStore()

        # Do some extra processing for test arguments.
        klass = self.GetClass()
        for field in klass.fields:
            name = field.GetName()

            # Use a default value for each field for which an argument
            # was not specified.
            if not arguments.has_key(name):
                arguments[name] = field.GetDefaultValue()

            # Convert attachments to 'AttachmentWrapper' objects.
            # First, the values of attachment fields (unless 'None').
            if isinstance(field, qm.fields.AttachmentField):
                value = arguments[name]
                if value is not None:
                    arguments[name] = qm.attachment.AttachmentWrapper(
                        value, attachment_store)
            # Also, all items in the values of attachment set fields.
            if isinstance(field, qm.fields.SetField) \
               and isinstance(field.GetContainedField(),
                              qm.fields.AttachmentField):
                value = arguments[name]
                new_value = map(
                    lambda at, as=attachment_store:
                    qm.attachment.AttachmentWrapper(at, as),
                    value)
                arguments[name] = new_value

        return apply(klass, [], arguments)



class Test(InstanceBase):
    """A test instance."""

    def __init__(self,
                 test_id,
                 test_class_name,
                 arguments,
                 prerequisites={},
                 categories=[],
                 resources=[],
                 properties={}):
        """Create a new test instance.

        'test_id' -- The test ID.

        'test_class_name' -- The name of the test class of which this is
        an instance.

        'arguments' -- This test's arguments to the test class.

        'prerequisites' -- A mapping from prerequisite test ID to
        required outcomes.

        'categories' -- A sequence of names of categories to which this
        test belongs.

        'resources' -- A sequence of IDs of resources to run before and
        after the test is run.

        'properties' -- A map of name, value pairs for properties of the
        test.  Names must be valid labels, and values must be strings."""

        # Initialize the base class.
        InstanceBase.__init__(self, test_id, test_class_name, arguments,
                              properties)
        self.__prerequisites = prerequisites
        self.__categories = categories
        self.__resources = resources

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


    def GetPrerequisites(self):
        """Return a map from prerequisite test IDs to required outcomes."""

        return self.__prerequisites


    def GetResources(self):
        """Return a sequence of IDs of resources."""

        return self.__resources


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



class Resource(InstanceBase):
    """A resource instance."""

    def __init__(self,
                 resource_id,
                 resource_class_name,
                 arguments,
                 properties={}):
        """Create a new resource instance.

        'resource_id' -- The resource ID.

        'resource_class_name' -- The name of the resource class of which
        this is an instance.

        'arguments' -- This test's arguments to the test class.

        'properties' -- A map of name, value pairs for properties of the
        test.  Names must be valid labels, and values must be strings."""

        # Initialize the base class.
        InstanceBase.__init__(self, resource_id, resource_class_name,
                              arguments, properties)
        # Don't instantiate the resource yet.
        self.__resource = None


    def GetResource(self):
        """Return the underlying user resource object."""

        # Perform just-in-time instantiation.
        if self.__resource is None:
            self.__resource = self._InstanceBase__MakeItem()

        return self.__resource


    def SetUp(self, context):
        return self.__Do(context, mode="setup")


    def CleanUp(self, context):
        return self.__Do(context, mode="cleanup")


    def __Do(self, context, mode):
        """Execute a setup resource.

        'context' -- Information about the environment in which the test
        is being executed.
        
        'mode' -- Either "setup" or "cleanup".

        returns -- A 'Result' describing the outcome of the test."""

        assert mode is "setup" or mode is "cleanup"

        working_directory = self.GetWorkingDirectory()
        old_working_directory = None
        resource = self.GetResource()

        try:
            if working_directory is not None:
                # Remember the previous working directory so we can
                # restore it.
                old_working_directory = os.getcwd()
                # Change to the working directory appropriate for this
                # test.
                os.chdir(working_directory)
            # Run the resource function.
            if mode is "setup":
                return resource.SetUp(context)
            else:
                return resource.CleanUp(context)
        finally:
            if old_working_directory is not None:
                # Restore the working directory.
                os.chdir(old_working_directory)



class Suite:
   """A group of tests.

   A test suite is a collection of tests.  The suite may contain other
   suites by reference as well; all tests contained in these contained
   suites are considered contained in the containing suite as well.

   There are two kinds of test suites:

     * Ordinary test suites are created by the user as an organizational
       aid.  The user specifies the IDs of tests and other suites
       contained in the suite.

     * QMTest creates *implicit* test suites as well.  These virtual
       test suites automatically contain all tests and suites whose IDs
       start with a common prefix.

       For example, consider a test database that contains tests with
       IDs "X.Y.a" and "X.Y.Z.b".  The latter is contained in an
       implicit suite "X.Y.Z".  This, along with the test "X.Y.a", is
       contained in the implicit suite "X.Y", which is in turn contained
       in the implicit suite "X".

   Ordinary test suites do not contain resources.  However, implicit
   test suites do contain resources whose IDs have the suite ID as a
   prefix.

   Use 'get_suite_contents_recursively' to find the tests, suites, and
   resources transitively contained in a suite."""

   def __init__(self,
                suite_id,
                implicit=0,
                test_ids=[],
                suite_ids=[],
                resource_ids=[]): 
       """Create a new test suite instance.

       'suite_id' -- The ID of the new suite.

       'implicit' -- If true, this is an implicit suite.  It contains
       all tests whose IDs have this suite's ID as a prefix.

       'test_ids' -- A sequence of IDs of tests contained in the suite.

       'suite_ids' -- A sequence of IDs of suites contained in the
       suite.

       'resource_ids' -- A sequence of IDs of resources contained in the
       suite.  Must be empty unless the suite is implicit."""

       self.__id = suite_id
       self.__implicit = implicit
       assert self.__implicit or len(resource_ids) == 0
       self.__test_ids = list(test_ids)
       self.__suite_ids = list(suite_ids)
       self.__resource_ids = list(resource_ids)


   def GetId(self):
       """Return the ID of this test suite."""

       return self.__id


   def IsImplicit(self):
       """Return true if this is an implicit test suite.

       Implicit test suites should not be explicitly editable."""

       return self.__implicit


   def GetTestIds(self):
       """Return a sequence of the test IDs of the tests in this suite.
       Does not include IDs of tests that are included via other
       suites."""

       return self.__test_ids


   def GetSuiteIds(self):
       """Return the IDs of suites explicitly part of this suite.

       returns -- A list of suites explicitly in this suite.  Does not
       include IDs of suites that are included via other suites."""

       return self.__suite_ids


   def GetResourceIds(self):
       """Return the IDs of resources explicitly part of this suite.

       Generally, suites do not contain resources explicitly, so this
       function will usually return an empty sequence.  However,
       implicit test suites, corresponding for instance to file system
       directories, may contain resources."""

       return self.__resource_ids
   


class Database:
    """A database containing tests."""

    def GetPath(self):
        """Return the path to the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetPath"
    

    def GetClassPaths(self):
        """Return paths to search for class files.

        returns -- A sequence of paths to add to the classpath when
        loading test and resource classes."""

        # Specify the '_classes' subdirectory, if it exists.
        class_dir = os.path.join(self.GetPath(), "_classes")
        if os.path.isdir(class_dir):
            return [class_dir]
        else:
            return []


    def HasTest(self, test_id):
        """Return true if the database has a test with ID 'test_id'."""

        # The default implementation of this function uses 'GetTest'.
        try:
            self.GetTest(test_id)
        except NoSuchTestError:
            return 0
        else:
            return 1


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

        # The default implementation of this function uses 'GetSuite'.

        try:
            self.GetSuite(suite_id)
        except NoSuchSuiteError:
            return 0
        else:
            return 1


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


    def GetSuiteIds(self, path="."):
        """Return suite IDs of all test suites relative to 'path'.

        'implicit' -- If true, include implicit test suites
        corresponding to directories in the space of test and suite
        IDs."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuiteIds"


    def HasResource(self, resource_id):
        """Return true if the database has a resource with 'resource_id'."""

        # The default implementation of this funciton uses 'GetResource'.

        try:
            self.GetResource(resource_id)
        except NoSuchResourceError:
            return 0
        else:
            return 1


    def GetResource(self, resource_id):
        """Return a 'Resource' instance for resource ID 'resource_id'.

        raises -- 'NoSuchResourceError' if there is no resource in the
        database with ID 'resource_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetResource"


    def WriteResource(self, resource):
        """Store a resource in the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.WriteResource"


    def RemoveResource(self, resource_id):
        """Remove the resource with ID 'resource_id' from the database."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveResource"


    def GetResourceIds(self, path="."):
        """Return resource IDs of all resources relative to 'path'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetResourceIds"


    def GetAttachmentStore(self):
        """Return the store for attachment data."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetAttachmentStore"


    def GetTestClasses(self):
        """Return a list of test classes that the database can store.

        Each acceptable test class is returned as a string."""

        return standard_test_class_names
    
    
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


    def GetId(self):
        """Return the test's or resource's ID for which this is a result."""
        
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
        element.setAttribute("id", self.GetId())
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
            if type(value) == types.StringType:
                # The property value is contained in a text mode.
                node = document.createTextNode(str(value))
                property_element.appendChild(node)
            else:
                for text in value:
                    node = document.createTextNode(str(text))
                    property_element.appendChild(node)
            # Add the property element to the result node.
            element.appendChild(property_element)

        return element


    # Methods to emulate a map, to access the properties of the
    # underlying 'Result' object.

    def __getitem__(self, key):
        return self.__result._Result__properties[key]


    def get(self, key, default=None):
        return self.__result._Result__properties.get(key, default)


    def has_key(self, key):
        return self.__result._Result__properties.has_key(key)


    def keys(self):
        return self.__result._Result__properties.keys()


    def items(self):
        return self.__result._Result__properties.items()


    def __setitem__(self, key, value):
        self.__result[key] = value


    def __delitem__(self, key):
        del self.__result[key]



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
            items.append((key, self[key], ))
        return items


    def copy(self):
        result = ContextWrapper(self.__context, self.__extra)
        result.__added = self.__added.copy()
        return result



########################################################################
# functions
########################################################################

def validate_id(item_id):
    """Validate a test or resource ID.

    raises -- 'RuntimeError' if 'item_id' is not a valid ID."""

    if not qm.label.is_valid(item_id, allow_separator=1):
        raise RuntimeError, qm.error("invalid id", id=item_id)


def get_suite_contents_recursively(suite, database):
    """Determine tests, suites, and resources contained in a suite.

    This function determines the IDs of tests, suites, and resources
    contained directly or indirecty (i.e. via a contained suite) in
    'suite'.

    An ordinary suite contained in an implicit suite is not expanded.
    Thus, implicit suites contain tests, resources, and suites whose IDs
    have the suite ID as a prefix, and no others.

    'suite' -- A 'Suite' instance.

    'database' -- The database containing 'suite'.

    returns -- A triple 'test_ids, resource_ids, suite_ids'.  Each
    element is a sequence of IDs."""

    test_ids = []
    resource_ids = []
    suite_ids = []

    # Maintain a work list of suites to process.
    work_list = [suite]
    # Process until the work list is empty.
    while len(work_list) > 0:
        suite = work_list.pop(0)
        # Accumulate test and resource IDs in the suite.
        test_ids.extend(suite.GetTestIds())
        resource_ids.extend(suite.GetResourceIds())
        # Find sub suites in the suite.
        sub_suite_ids = suite.GetSuiteIds()
        # Accumulate them.
        suite_ids.extend(sub_suite_ids)
        # Retrieve the 'Suite' objects.
        sub_suites = map(database.GetSuite, sub_suite_ids)
        # Don't expand ordinary suites contained in implicit suites.
        if suite.IsImplicit():
            sub_suites = filter(lambda s: s.IsImplicit(), sub_suites)
        # Add contained suites to the work list.
        work_list.extend(sub_suites)

    return test_ids, resource_ids, suite_ids


def expand_ids(ids):
    """Expand test and suite IDs into test IDs.

    'ids' -- A sequence of IDs of tests and suites, which may be mixed
    together.

    returns -- A pair 'test_ids, suite_ids'.  'test_ids' is a
    sequence of test IDs including all test IDs mentioned in 'ids' plus
    all test IDs obtained from recursively expanding suites included in
    'ids'.  'suite_ids' is the set of IDs of suites included directly
    and indirectly in 'ids'.

    raises -- 'ValueError' if an element in 'id' is neither a test or
    suite ID.  The exception argument is the erroneous element."""

    database = get_database()

    # We'll collect test and suite IDs in maps, to make duplicate checks
    # efficient.
    test_ids = {}
    suite_ids = {}
    # These function add to the maps.
    def add_test_id(test_id, test_ids=test_ids):
        test_ids[test_id] = None
    def add_suite_id(suite_id, suite_ids=suite_ids):
        suite_ids[suite_id] = None

    for id in ids:
        # Skip this ID if we've already seen it.
        if suite_ids.has_key(id) or test_ids.has_key(id):
            continue
        # Is this a suite ID?
        if database.HasSuite(id):
            add_suite_id(id)
            # Yes.  Load the suite.
            suite = database.GetSuite(id)
            # Determine all the tests and suites contained directly and
            # indirectly in this suite.
            suite_test_ids, suite_resource_ids, sub_suite_ids = \
                get_suite_contents_recursively(suite, database)
            # Add them.
            map(add_test_id, suite_test_ids)
            map(add_suite_id, sub_suite_ids)
        # Or is this a test ID?
        elif database.HasTest(id):
            # Yes.  Add it.
            add_test_id(id)
        else:
            # It doesn't look like a test or suite ID.
            raise ValueError, id

    # Convert the maps to sequences.
    return test_ids.keys(), suite_ids.keys()


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


def load_database(path):
    """Load the database from 'path'."""

    # Make sure it is a directory.
    if not os.path.isdir(path):
        raise ValueError, "Database path %s is not a directory." % path

    # Try to load the database implementation from a file named
    # '_classes/database.py' in the test database.
    classes_path = [os.path.join(path, "_classes")]
    database_class = None
    try:
        database_module = qm.common.load_module("database", classes_path)
    except ImportError, e:
        # Couldn't import the module.
        pass
    else:
        # Look for a class named 'Database' in the module.
        try:
            db = database_module.Database
        except AttributeError:
            # No such attribute in the module.
            pass
        else:
            # Make sure it's a class.
            if type(db) is types.ClassType:
                database_class = db

    # Did we find the class?
    if database_class is None:
        # No.  Fall back to the default XML test database implementation.
        import xmldb
        database_class = xmldb.Database

    # Load the database.
    global _database
    _database = database_class(path)



def get_class(class_name):
    """Return the test or resource class named 'class_name'.

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


def make_new_resource(resource_class_name, resource_id):
    """Create a new resource with default arguments.

    'resource_class_name' -- The name of the resource class of which to
    create a new resource.

    'resource_id' -- The resource ID of the new resource.

    returns -- A new 'Resource' object."""

    resource_class = get_class(resource_class_name)
    # Make sure there isn't already such a resource.
    database = get_database()
    if database.HasResource(resource_id):
        raise RuntimeError, qm.error("resource already exists",
                                     resource_id=resource_id)
    # Construct an argument map containing default values.
    arguments = {}
    for field in resource_class.fields:
        name = field.GetName()
        value = field.GetDefaultValue()
        arguments[name] = value
    # Construct a default resource instance.
    return Resource(resource_id, resource_class_name, arguments)


def load_outcomes(path):
    """Load test outcomes from a file.

    'path' -- Path to an XML results file.

    returns -- A map from test IDs to outcomes."""

    # Load full results.
    test_results = load_results(path)[0]
    # Keep test outcomes only.
    outcomes = {}
    for test_id in test_results.keys():
        outcomes[test_id] = test_results[test_id].GetOutcome()
    return outcomes


def write_results(test_results, resource_results, output):
    """Write results in XML format.

    'test_results' -- A sequence of 'ResultWrapper' objects for tests.

    'resource_results' -- A sequence of 'ResultWrapper' objects for
    resource functions.

    'output' -- A file object to which to write the results."""

    document = qm.xmlutil.create_dom_document(
        public_id=dtds["result"],
        dtd_file_name="result.dtd",
        document_element_tag="test-run"
        )
    # Add an element for grouping test results.
    test_results_element = document.createElement("test-results")
    document.documentElement.appendChild(test_results_element)
    # Add a result element for each test that was run.
    for result in test_results:
        result_element = result.MakeDomNode(document)
        test_results_element.appendChild(result_element)
    # Add an element for grouping resource function results.
    resource_results_element = document.createElement("resource-results")
    document.documentElement.appendChild(resource_results_element)
    # Add a result element for each resource function that was run.
    for result in resource_results:
        result_element = result.MakeDomNode(document)
        resource_results_element.appendChild(result_element)
    # Generate output.
    qm.xmlutil.write_dom_document(document, output)
    

def save_results(results, path):
    """Save results to an XML file.

    'results' -- A sequence of 'ResultWrapper' objects.

    'path' -- The path of the file in which to svae them."""
    
    results_file = open(path, "w")
    write_results(results, results_file)
    results_file.close()


def load_results(path):
    """Read test results from a file.

    'path' -- The file from which to read the results.

    returns -- A pair, '(test_results, resource_results)'.
    'test_results' is map from test IDs to 'ResultWrapper' objects.
    'resource_results' is a sequence of resource 'ResultWrapper' objects."""
    
    results_document = qm.xmlutil.load_xml_file(path)
    node = results_document.documentElement
    # Extract the test result elements.
    test_results_element = qm.xmlutil.get_child(node, "test-results")
    test_results = _test_results_from_dom(test_results_element)
    # Extract the resource result elements.
    resource_results_element = qm.xmlutil.get_child(node, "resource-results")
    resource_results = _resource_results_from_dom(resource_results_element)
    # That's it.
    return test_results, resource_results


def _test_results_from_dom(results_node):
    """Extract test results from a DOM node.

    'results_node' -- A DOM node for a "test-results" element.

    returns -- A map from test IDs to 'ResultWrapper' objects."""

    # Extract one result for each result element.
    results = {}
    for node in qm.xmlutil.get_children(results_node, "result"):
        result = _result_from_dom(node)
        results[result.GetId()] = result
    return results


def _resource_results_from_dom(results_node):
    """Extract resource results from a DOM node.

    'results_node' -- A DOM node for a "resource-results" element.

    returns -- A sequence of 'ResultWrapper' objects for resource
    results."""

    # Extract one result for each result element.
    results = []
    for node in qm.xmlutil.get_children(results_node, "result"):
        result = _result_from_dom(node)
        results.append(result)
    return results


def _result_from_dom(node):
    """Extract a result from a DOM node.

    'node' -- A DOM node corresponding to a "result" element.

    returns -- A 'ResultWrapper' object."""

    assert node.tagName == "result"
    # Extract the outcome, and build a base 'Result' object.
    outcome = qm.xmlutil.get_child_text(node, "outcome")
    result = Result(outcome)
    # Extract properties, one for each property element.
    for property_node in node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value
    # Extract the test ID.
    test_id = node.getAttribute("id")
    # FIXME: Load context?
    context = None
    # Construct a result wrapper around the result.
    return ResultWrapper(test_id, context, result)


def _count_outcomes(results):
    """Count results by outcome.

    'results' -- A sequence of 'ResultWrapper' objects.

    returns -- A map from outcomes to counts of results with that
    outcome.""" 

    counts = {}
    for outcome in Result.outcomes:
        counts[outcome] = 0
    for result in results:
        outcome = result.GetOutcome()
        counts[outcome] = counts[outcome] + 1
    return counts


def split_results_by_expected_outcome(results, expected_outcomes):
    """Partition a sequence of results by expected outcomes.

    'results' -- A sequence of 'ResultWrapper' objects.

    'expected_outcomes' -- A map from ID to corresponding expected
    outcome.

    returns -- A pair of lists.  The first contains results that
    produced the expected outcome.  The second contains results that
    didn't."""

    expected = []
    unexpected = []
    for result in results:
        expected_outcome = expected_outcomes.get(result.GetId(), Result.PASS)
        if result.GetOutcome() == expected_outcome:
            expected.append(result)
        else:
            unexpected.append(result)
    return expected, unexpected


def summarize_test_stats(output, results):
    """Generate a summary of test result statistics.

    'output' -- A file object to which to write the summary.

    'results' -- A sequece of 'ResultWrapper' objects."""

    num_tests = len(results)
    output.write("  %6d        tests total\n" % num_tests)

    # No tests?  Bail.
    if num_tests == 0:
        return

    counts_by_outcome = _count_outcomes(results)
    for outcome in Result.outcomes:
        count = counts_by_outcome[outcome]
        if count > 0:
            output.write("  %6d (%3.0f%%) tests %s\n"
                         % (count, (100. * count) / num_tests, outcome))
    output.write("\n")


def summarize_relative_test_stats(output,
                                  results,
                                  expected_outcomes):
    """Generate statistics of test results relative to expected outcomes.

    'output' -- A file object to which to write the summary.

    'results' -- A sequence of 'ResultWrapper' objects.

    'expected_outcomes' -- A map from test ID to corresponding expected
    outcome."""

    num_tests = len(results)
    output.write("  %6d        tests total\n" % num_tests)

    # No tests?  Bail.
    if num_tests == 0:
        return

    # Split the results into those that produced expected outcomes, and
    # those that didn't.
    expected, unexpected = \
        split_results_by_expected_outcome(results, expected_outcomes)
    # Report the number that produced expected outcomes.
    output.write("  %6d (%3.0f%%) tests as expected\n"
                 % (len(expected), (100. * len(expected)) / num_tests))
    # For results that produced unexpected outcomes, break them down by
    # actual outcome.
    counts_by_outcome = _count_outcomes(unexpected)
    for outcome in Result.outcomes:
        count = counts_by_outcome[outcome]
        if count > 0:
            output.write("  %6d (%3.0f%%) tests unexpected %s\n"
                         % (count, (100. * count) / num_tests, outcome))
    output.write("\n")


def summarize_test_suite_stats(output,
                               results,
                               suite_ids,
                               expected_outcomes):
    """Generate a summary of test results statistics by suite.

    'output' -- A file object to which to write the summary.

    'results' -- A sequence of 'ResultWrapper' objects.

    'suite_ids' -- A sequence of IDs ot suites by which to group
    attachments.

    'expected_outcomes' -- A map from ID to expected outcomes, or
    'None'."""

    database = get_database()

    for suite_id in suite_ids:
        # Expand the contents of the suite.
        suite = database.GetSuite(suite_id)
        ids_in_suite = get_suite_contents_recursively(suite, database)[0]
        # Determine the results belonging to tests in the suite.
        results_in_suite = []
        for result in results:
            if result.GetId() in ids_in_suite:
                results_in_suite.append(result)
        # If there aren't any, skip.
        if len(results_in_suite) == 0:
            continue

        output.write("  %s\n" % suite.GetId())
        if expected_outcomes is None:
            summarize_test_stats(output, results_in_suite)
        else:
            summarize_relative_test_stats(
                output, results_in_suite, expected_outcomes)


def summarize_results(output, format, results, expected_outcomes=None):
    """Generate a summary of results.

    'output' -- A file object to which to write the summary.

    'format' -- The summary format.  Must be "full" or "brief".

    'results' -- A sequence of 'ResultWrapper' objects.

    'expected_outcomes' -- A map from ID to expected outcomes, or 'None'."""

    if len(results) == 0:
        output.write("  None.\n\n")
        return

    # Function to format a result property nicely.
    def format_property(name, value):
        if "\n" in value or len(value) > 72 - len(name):
            value = qm.common.wrap_lines(value, columns=70,
                                         break_delimiter="", indent="        ")
            return "    %s:\n%s\n" % (name, value)
        else:
            return "    %s: %s\n" % (name, value)

    # Generate them.
    for result in results:
        id_ = result.GetId()
        outcome = result.GetOutcome()

        # Print the ID and outcome.
        if expected_outcomes:
            # If expected outcomes were specified, print the expected
            # outcome too.
            expected_outcome = expected_outcomes.get(id_, Result.PASS)
            output.write("  %-46s: %-8s, expected %-8s\n"
                         % (id_, outcome, expected_outcome))
        else:
            output.write("  %-63s: %-8s\n" % (id_, outcome))

        if format == "full":
            # In the "full" format, print all result properties.
            for name, value in result.items():
                output.write(format_property(name, value))
            output.write("\n")
        elif format == "brief":
            # In the "brief" format, print only the "cause" property, if
            # specified.
            if result.has_key("cause"):
                output.write(format_property("cause", result["cause"]))

    if format == "brief":
        output.write("\n")


def run_test(test_id, context):
    """Run a test.

    'test_id' -- The ID of the test to run.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'ResultWrapper' object for the test."""

    context["path"] = qm.rc.Get("path", os.environ["PATH"])

    test = get_database().GetTest(test_id)

    try:
        # Run the test.
        result = test.Run(context)
    except KeyboardInterrupt:
        # Let this propagate out, so the user can kill the test run.
        raise
    except:
        # The test raised an exception.  Create a result object for it.
        result = make_result_for_exception(sys.exc_info())
    else:
        # The test ran to completion.  It should have returned a
        # 'Result' object.
        if not isinstance(result, qm.test.base.Result):
            # Something else.  That's an error.
            raise RuntimeError, \
                  qm.error("invalid result",
                           id=test_id,
                           test_class=test.GetClass().__name__,
                           result=repr(result))

    # Wrap the result with additional information.
    return ResultWrapper(test_id, context, result)


def set_up_resource(resource_id, context):
    """Set up a resource.

    'test_id' -- The ID of the resource to set up.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'ResultWrapper' object for the setup function."""

    resource = get_database().GetResource(resource_id)

    # Set up the resoure.
    try:
        result = resource.SetUp(context)
    except:
        # The resource raised an exception.  
        result = Result(Result.ERROR, cause="Uncaught exception.")
        # Add some information about the traceback.
        exc_info = sys.exc_info()
        result["exception"] = "%s: %s" % exc_info[:2]
        result["traceback"] = qm.common.format_traceback(exc_info)
    # Indicate in the result what we did.
    result["action"] = "setup"
    # Wrap it up.
    return ResultWrapper(resource_id, context, result)


def clean_up_resource(resource_id, context):
    """Clean up a resource.

    'test_id' -- The ID of the resource to clean up.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'ResultWrapper' object for the cleanup function."""

    resource = get_database().GetResource(resource_id)

    # Clean up the resource.
    try:
        result = resource.CleanUp(context)
    except:
        # The resource raised an exception.  
        result = Result(Result.ERROR, cause="Uncaught exception.")
        # Add some information about the traceback.
        exc_info = sys.exc_info()
        result["exception"] = "%s: %s" % exc_info[:2]
        result["traceback"] = qm.common.format_traceback(exc_info)
    # Indicate in the result what we did.
    result["action"] = "cleanup"
    # Wrap it up.
    return ResultWrapper(resource_id, context, result)


########################################################################
# variables
########################################################################

_database = None
"""The global test database instance.

Use 'get_database' to access the global test database."""

__loaded_classes = {}
"""Cache of loaded test and resource classes."""

__builtin_class_path = [
    qm.common.get_lib_directory("qm", "test", "classes"),
    ]
"""Standard paths to search for test and resource classes."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

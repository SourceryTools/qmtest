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
    "command.CommandTest",
    "command.ScriptTest",
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
        # Set the full path for each attachment in a test argument that
        # references attachment data by location.
        self.__SetAttachmentPaths(self.GetArguments().values())


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
       self.__test_id_cache = None


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
       once."""

       if self.__test_id_cache is None:
           database = get_database()
           if self.IsImplicit():
               dir_id = self.GetId()
           else:
               dir_id = qm.label.dirname(self.GetId())
           # Instead of keeping a list of test IDs, we'll build a map, to
           # assist with skipping duplicates.  The keys are test IDs (we
           # don't care about the values).
           ids = {}
           # Start by entering the tests explicitly part of this suite.
           for test_id in self.__test_ids:
               ids[test_id] = test_id
           # Now loop over suites contained in this suite.
           for suite_id in self.__suite_ids:
               suite = database.GetSuite(suite_id)
               # Get the test IDs in the contained suite.
               test_ids_in_suite = suite.GetTestIds()
               # Make note of them.
               for test_id in test_ids_in_suite:
                   ids[test_id] = None
           # All done.
           self.__test_id_cache = ids.keys()

       return self.__test_id_cache


   def GetRawTestIds(self):
       """Return the IDs of tests explicitly part of this suite.

       returns -- A list of tests explicitly in this suite.  Does not
       include IDs of tests that are included in this suite via other
       suites."""

       return self.__test_ids


   def GetRawSuiteIds(self):
       """Return the IDs of suites explicitly part of this suite.

       returns -- A list of suites explicitly in this suite.  Does not
       include IDs of suites that are included via other suites.  Suite
       IDs are relative to the path contianing this suite."""

       return self.__suite_ids



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


    def GetSuiteIds(self, path=".", implicit=0):
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


    def SetAttachmentData(self, attachment, data, item_id):
        """Store attachment data to the database.

        'attachment' -- An 'Attachment' instance.

        'data' -- The attachment data as a string.

        'item_id' -- A test or resource ID associated with this
        attachment."""

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


    def GetId(self):
        """Return the ID of the test or resource for which this is a result."""
        
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
        qm.common.print_message(2, 
            "Warning: couldn't import database module:\n%s\n" % str(e))
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
    outcomes = load_results(path)
    # Replace full results with outcomes only.
    for test_id in outcomes.keys():
        outcomes[test_id] = outcomes[test_id].GetOutcome()
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


def read_results(input):
    """Read test results from XML format.

    'input' -- A file object from which to read the results.

    returns -- A map from test IDs to 'ResultWrapper' objects."""
    
    results_document = qm.xmlutil.load_xml(input)
    test_results_elements = \
        results_document.getElementsByTagName("test-results")
    assert len(test_results_elements) == 1
    # Extract the result elements.
    return _results_from_dom(test_results_elements[0])


def load_results(path):
    """Read test results from a file.

    'path' -- The file from which to read the results.

    returns -- A map from test IDs to 'ResultWrapper' objects."""
    
    results_document = qm.xmlutil.load_xml_file(path)
    test_results_elements = \
        results_document.getElementsByTagName("test-results")
    assert len(test_results_elements) == 1
    # Extract the result elements.
    return _results_from_dom(test_results_elements[0])


def _results_from_dom(results_node):
    """Extract results from a results element.

    'results_node' -- A DOM node corresponding to a results element.

    returns -- A map from test IDs to 'ResultWrapper' objects."""

    # Extract one result for each result element.
    results = {}
    for result_node in results_node.getElementsByTagName("result"):
        result = _result_from_dom(result_node)
        results[result.GetId()] = result
    return results


def _result_from_dom(result_node):
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


def run_test(test_id, context):
    """Run a test.

    'test_id' -- The ID of the test to run.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'ResultWrapper' object for the test."""

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
# initialization
########################################################################

qm.attachment.attachment_class = Attachment

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

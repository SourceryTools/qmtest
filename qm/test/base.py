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
import qm.structured_text
from   qm.test.result import *
import qm.xmlutil
import string
import sys
import tempfile
import types

########################################################################
# constants
########################################################################

dtds = {
    "tdb-configuration":
                    "-//Software Carpentry//QMTest TDB Configuration V0.1//EN",
    "resource":     "-//Software Carpentry//QMTest Resource V0.1//EN",
    "result":       "-//Software Carpentry//QMTest Result V0.3//EN",
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

class ItemDescriptor:
    """Common base class for test and resource descriptors."""

    def __init__(self,
                 database,
                 instance_id,
                 class_name,
                 arguments):
        validate_id(instance_id)
        self.__database = database
        self.__id = instance_id
        self.__class_name = class_name
        self.__arguments = arguments
        self.__working_directory = None


    def GetClassName(self):
        """Return the name of the class of which this is an instance."""

        return self.__class_name


    def GetClass(self):
        """Return the class of this test or resource."""

        if isinstance(self, TestDescriptor):
            kind = 'test'
        elif isinstance(self, ResourceDescriptor):
            kind = 'resource'
        else:
            assert 0
            
        return get_extension_class(self.GetClassName(), kind,
                                   self.__database)
    

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

    # Helper functions.

    def _MakeItem(self):
        """Construct the underlying user test or resource object."""

        arguments = self.GetArguments().copy()

        # Do some extra processing for test arguments.
        klass = self.GetClass()
        for field in klass.arguments:
            name = field.GetName()

            # Use a default value for each field for which an argument
            # was not specified.
            if not arguments.has_key(name):
                arguments[name] = field.GetDefaultValue()

        return apply(klass, [], arguments)



class TestDescriptor(ItemDescriptor):
    """A test instance."""

    def __init__(self,
                 database,
                 test_id,
                 test_class_name,
                 arguments,
                 prerequisites={},
                 categories=[],
                 resources=[],
                 target_group=".*"):
        """Create a new test instance.

        'database' -- The 'Database' containing this test.
        
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

        'target_group' -- A regular expression (represented as a string)
        that indicates the targets on which this test can be run.  If
        the pattern matches a particular group name, the test can be run
        on targets in that group."""

        # Initialize the base class.
        ItemDescriptor.__init__(self, database,
                                test_id, test_class_name, arguments)
        self.__prerequisites = prerequisites
        self.__categories = categories
        self.__resources = resources
        self.__target_group = target_group
        
        # Don't instantiate the test yet.
        self.__test = None


    def GetTest(self):
        """Return the underlying user test object."""

        # Perform just-in-time instantiation.
        if self.__test is None:
            self.__test = self._MakeItem()

        return self.__test


    def GetCategories(self):
        """Return the names of categories to which the test belongs."""

        return self.__categories
    

    def GetPrerequisites(self):
        """Return a map from prerequisite test IDs to required outcomes."""

        return self.__prerequisites


    def GetResources(self):
        """Return a sequence of IDs of resources."""

        return self.__resources


    def GetTargetGroup(self):
        """Returns the pattern for the targets that can run this test.

        returns -- A regular expression (represented as a string) that
        indicates the targets on which this test can be run.  If the
        pattern matches a particular group name, the test can be run
        on targets in that group."""

        return self.__target_group
    
        
    def Run(self, context, result):
        """Execute this test.

        'context' -- Information about the environment in which the test
        is being executed.

        'result' -- The 'Result' object for this test.
        
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
                self.GetTest().Run(context, result)
            finally:
                # Restore the working directory.
                os.chdir(old_working_directory)
        else:
            # Just run the test without mucking with directories.
            self.GetTest().Run(context, result)



class ResourceDescriptor(ItemDescriptor):
    """A resource instance."""

    def __init__(self,
                 database,
                 resource_id,
                 resource_class_name,
                 arguments):
        """Create a new resource instance.

        'database' -- The 'Database' containing this resource.
        
        'resource_id' -- The resource ID.

        'resource_class_name' -- The name of the resource class of which
        this is an instance.

        'arguments' -- This resource's arguments to the resource class."""

        # Initialize the base class.
        ItemDescriptor.__init__(self, database, resource_id,
                                resource_class_name, arguments)
        # Don't instantiate the resource yet.
        self.__resource = None


    def GetResource(self):
        """Return the underlying user resource object."""

        # Perform just-in-time instantiation.
        if self.__resource is None:
            self.__resource = self._MakeItem()

        return self.__resource


    def SetUp(self, context, result):
        return self.__Do(context, result, mode="setup")


    def CleanUp(self, context, result):
        return self.__Do(context, result, mode="cleanup")


    def __Do(self, context, result, mode):
        """Execute a setup resource.

        'context' -- Information about the environment in which the test
        is being executed.

        'result' - The 'Result' for the resource.
        
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
                return resource.SetUp(context, result)
            else:
                return resource.CleanUp(context, result)
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
       in the implicit suite "X"."""

   def __init__(self,
                database,
                suite_id,
                implicit=0,
                test_ids=[],
                suite_ids=[],
                resource_ids=[]): 
       """Create a new test suite instance.

       'database' -- The database in which this suite is located.
       
       'suite_id' -- The ID of the new suite.

       'implicit' -- If true, this is an implicit suite.  It contains
       all tests whose IDs have this suite's ID as a prefix.

       'test_ids' -- A sequence of IDs of tests contained in the suite.

       'suite_ids' -- A sequence of IDs of suites contained in the
       suite.

       'resource_ids' -- A sequence of IDs of resources contained in the
       suite.  Must be empty unless the suite is implicit."""

       self.__database = database
       self.__id = suite_id
       self.__implicit = implicit
       assert self.__implicit or len(resource_ids) == 0
       self.__test_ids = list(test_ids)
       self.__suite_ids = list(suite_ids)
       self.__resource_ids = list(resource_ids)


   def GetDatabase(self):
       """Return the 'Database' that contains this suite.

       returns -- The 'Database' that contains this suite."""

       return self.__database

   
   def GetId(self):
       """Return the ID of this test suite."""

       return self.__id


   def IsImplicit(self):
       """Return true if this is an implicit test suite.

       Implicit test suites cannot be edited."""

       return self.__implicit


   def GetTestIds(self):
       """Return the tests contained in this suite.
       
       returns -- A sequence of labels corresponding to the tests
       contained in this suite.  Tests that are contained in this suite
       only because they are contained in a suite which is itself
       contained in this suite are not returned."""

       return self.__test_ids

   
   def GetSuiteIds(self):
       """Return the suites contained in this suite.
       
       returns -- A sequence of labels corresponding to the suites
       contained in this suite.  Suites that are contained in this suite
       only because they are contained in a suite which is itself
       contained in this suite are not returned."""

       return self.__suite_ids


   def GetAllTestAndSuiteIds(self):
       """Return the tests/suites contained in this suite and its subsuites.

       returns -- A pair '(test_ids, suite_ids)'.  The 'test_ids' and
       'suite_ids' elements are both sequences of labels.  The values
       returned include all tests and suites that are contained in this
       suite and its subsuites, recursively."""

       suite = self
       
       test_ids = []
       suite_ids = []

       # Maintain a work list of suites to process.
       work_list = [suite]
       # Process until the work list is empty.
       while len(work_list) > 0:
           suite = work_list.pop(0)
           # Accumulate test and resource IDs in the suite.
           test_ids.extend(suite.GetTestIds())
           # Find sub suites in the suite.
           sub_suite_ids = suite.GetSuiteIds()
           # Accumulate them.
           suite_ids.extend(sub_suite_ids)
           # Retrieve the 'Suite' objects.
           sub_suites = map(self.GetDatabase().GetSuite, sub_suite_ids)
           # Don't expand ordinary suites contained in implicit suites.
           if suite.IsImplicit():
               sub_suites = filter(lambda s: s.IsImplicit(), sub_suites)
           # Add contained suites to the work list.
           work_list.extend(sub_suites)

       return test_ids, suite_ids
       
       
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

    def __init__(self, **initial_properties):
        """Construct a new context.

        'initial_properties' -- Initial key/value pairs to include in
        the context."""

        self.__properties = initial_properties
        for key, value in self.__properties.items():
            self.ValidateKey(key)

        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            self.ValidateKey(option)
            value = qm.rc.Get(option, None)
            assert value is not None
            self.__properties[option] = value

        self.__temporaries = {}


    # Methods to simulate a map object.

    def __getitem__(self, key):
        return self.__properties[key]


    def __setitem__(self, key, value):
        self.ValidateKey(key)
        self.__properties[key] = value


    def __delitem__(self, key):
        del self.__properties[key]


    def has_key(self, key):
        return self.__properties.has_key(key)


    def keys(self):
        return self.__properties.keys()


    def values(self):
        return self.__properties.values()


    def items(self):
        return self.__properties.items()


    def copy(self):
        # No need to re-validate.
        result = Context()
        result.__properties = self.__properties.copy()
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
                      qm.error("context property cannot be deleted",
                               property=key)
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



def get_db_configuration_directory(db_path):
    """Return the path to the test database's configuration directory."""
    
    return os.path.join(db_path, "QMTest")


def _get_db_configuration_path(db_path):
    """Return the path to a test database's configuration file.

    'db_path' -- The path to the test database."""

    return os.path.join(get_db_configuration_directory(db_path),
                        "configuration")


def is_database(db_path):
    """Returns true if 'db_path' looks like a test database."""

    # A test database is a directory.
    if not os.path.isdir(db_path):
        return 0
    # A test database contains a configuration subdirectory.
    if not os.path.isdir(get_db_configuration_directory(db_path)):
        return 0
    # It probably is OK.
    return 1


def load_database(db_path):
    """Load the database from 'db_path'.

    returns -- The new 'Database'."""

    # Make sure it is a directory.
    if not is_database(db_path):
        raise ValueError, \
              qm.error("not test database", path=db_path)

    # Figure out which class implements the database.  Start by looking
    # for a file called 'configuration' in the directory corresponding
    # to the database.
    config_path = _get_db_configuration_path(db_path)
    if os.path.isfile(config_path):
        # Load the configuration file.
        document = qm.xmlutil.load_xml_file(config_path)
        # Get the root node in the document.
        database = document.documentElement
        # Load the database class name.
        database_class_name = qm.xmlutil.get_child_text(database,
                                                        "class-name")
        # Get the database class.
        database_class = get_extension_class(database_class_name,
                                             "database", None)
    else:
        # If 'configuration' did not exist, fall back to the 'xmldb'
        # database.
        import xmldb
        database_class = xmldb.Database
    
    # Create the database.
    return database_class(db_path)


def create_database(db_path, class_name):
    """Create a new test database.

    'db_path' -- The path to the test database.

    'class_name' -- The class name of the test database implementation.

    raises -- 'ValueError' if 'db_path' already exists."""
    
    # Make sure the path doesn't already exist.
    if os.path.exists(db_path):
        raise ValueError, qm.error("db path exists", path=db_path)
    # Create an empty directory.
    os.mkdir(db_path)
    # Create the configuration directory.
    os.mkdir(get_db_configuration_directory(db_path))

    # Now create an XML document for the configuration file.
    document = qm.xmlutil.create_dom_document(
        public_id=dtds["tdb-configuration"],
        dtd_file_name="tdb_configuration.dtd",
        document_element_tag="tdb-configuration"
        )
    # Create an element containign the class name.
    class_element = qm.xmlutil.create_dom_text_element(
        document, "class-name", class_name)
    document.documentElement.appendChild(class_element)
    # Write it.
    configuration_path = _get_db_configuration_path(db_path)
    qm.xmlutil.write_dom_document(document, open(configuration_path, "w"))


def get_extension_directories(kind, database):
    """Return the directories to search for QMTest extensions.

    'kind' -- A string giving kind of extension for which we are looking.
    This must be of the elements of 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.
    
    returns -- A sequence of strings.  Each string is the path to a
    directory that should be searched for QMTest extensions.  The
    directories must be searched in order; the first directory
    containing the desired module is the one from which the module is
    loaded.

    The directories that are returned are, in order:

    1. Those directories present in the 'QMTEST_CLASSPATH' environment
       variable.

    2. Those directories specified by the 'GetClassPaths' method on the
       test database -- unless 'kind' is 'database'.

    3. The directories containing classes that come with QMTest.

    By placing the 'QMTEST_CLASSPATH' directories first, users can
    override test classes with standard names."""

    global extension_kinds

    # The kind should be one of the extension_kinds.
    assert kind in extension_kinds
    if kind != 'database':
        assert database
    else:
        assert database is None
        
    # Start with the directories that the user has specified in the
    # QNTEST_CLASSPATH environment variable.
    if os.environ.has_key('QMTEST_CLASSPATH'):
        dirs = string.split(os.environ['QMTEST_CLASSPATH'], ':')
    else:
        dirs = []

    # Search directories specified by the database -- unless we are
    # searching for a database class, in which case we cannot assume
    # that a database has already been loaded.
    if kind != 'database':
        dirs = dirs + database.GetClassPaths()

    # Search the builtin directory, too.
    dirs.append(qm.common.get_lib_directory("qm", "test", "classes"))

    return dirs


def get_extension_class_names_in_directory(directory):
    """Return the names of QMTest extension classes in 'directory'.

    'directory' -- A string giving the path to a directory in the file
    system.

    returns -- A dictionary mapping the strings in 'extension_kinds' to
    sequences of strings.  Each element in the sequence names an
    extension class, using the form 'module.class'"""

    global extension_kinds
    
    # Assume that there are no extension classes in this directory.
    extensions = {}
    for kind in extension_kinds:
        extensions[kind] = []
        
    # Look for a file named 'classes.qmc' in this directory.
    file = os.path.join(directory, 'classes.qmc')
    # If the file does not exist, there are no extension classes in
    # this directory.
    if not os.path.isfile(file):
        return extensions

    try:
        # Load the file.
        document = qm.xmlutil.load_xml_file(file)
        # Get the root node in the document.
        root = document.documentElement
        # Get the sequence of elements corresponding to each of the
        # classes listed in the directory.
        classes = qm.xmlutil.get_children(root, 'class')
        # Go through each of the classes to see what kind it is.
        for c in classes:
            kind = c.getAttribute('kind')
            # Skip extensions we do not understand.  Perhaps they
            # are for some other QM tool.
            if kind not in extension_kinds:
                continue
            extensions[kind].append(qm.xmlutil.get_dom_text(c))
    except:
        print sys.exc_info()[1]
        pass

    return extensions


def get_extension_class_names(kind, database):
    """Return the names of extension classes.

    'kind' -- The kind of extension class.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    returns -- A sequence of strings giving the names of the extension
    classes with the indicated 'kind', in the form 'module.class'."""

    dirs = get_extension_directories(kind, database)
    names = []
    for d in dirs:
        names.extend(get_extension_class_names_in_directory(d)[kind])
    return names


def get_extension_class(class_name, kind, database):
    """Return the extension class named 'class_name'.

    'class_name' -- The name of the class, in the form 'module.class'.

    'kind' -- The kind of class to load.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    returns -- The class object with the indicated 'class_name'."""

    global __class_caches
    
    # If this class is already in the cache, we can just return it.
    cache = __class_caches[kind]
    if cache.has_key(class_name):
        return cache[class_name]

    # Otherwise, load it now.  Get all the extension directories in
    # which this class might be located.
    klass = qm.common.load_class(class_name,
                                 get_extension_directories(kind,
                                                           database))
    # Cache it.
    cache[class_name] = klass

    return klass


def get_test_class(class_name, database):
    """Return the test class named 'class_name'.

    'class_name' -- The name of the test class, in the form
    'module.class'.

    returns -- The test class object with the indicated 'class_name'."""
    
    return get_extension_class(class_name, 'test', database)


def get_resource_class(class_name, database):
    """Return the resource class named 'class_name'.

    'class_name' -- The name of the resource class, in the form
    'module.class'.

    returns -- The resource class object with the indicated
    'class_name'."""
    
    return get_extension_class(class_name, 'resource', database)


def load_outcomes(file):
    """Load test outcomes from a file.

    'file' -- The file object from which to read the results.

    returns -- A map from test IDs to outcomes."""

    # Load full results.
    test_results = filter(lambda r: r.GetKind() == Result.TEST,
                          load_results(file))
    # Keep test outcomes only.
    outcomes = {}
    for r in test_results:
        outcomes[r.GetId()] = r.GetOutcome()
    return outcomes


def load_results(file):
    """Read test results from a file.

    'file' -- The file object from which to read the results.

    returns -- A sequence of 'Result' objects."""

    results = []
    
    results_document = qm.xmlutil.load_xml(file)
    node = results_document.documentElement
    # Extract the results.
    results_elements = qm.xmlutil.get_children(node, "result")
    for re in results_elements:
        results.append(_result_from_dom(re))

    return results


def _result_from_dom(node):
    """Extract a result from a DOM node.

    'node' -- A DOM node corresponding to a "result" element.

    returns -- A 'Result' object.  The context for the result is 'None',
    since context is not represented in a result DOM node."""

    assert node.tagName == "result"
    # Extract the outcome.
    outcome = qm.xmlutil.get_child_text(node, "outcome")
    # Extract the test ID.
    test_id = node.getAttribute("id")
    kind = node.getAttribute("kind")
    # The context is not represented in the DOM node.
    context = None
    # Build a Result.
    result = Result(kind, test_id, context, outcome)
    # Extract properties, one for each property element.
    for property_node in node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value

    return result


def count_outcomes(results):
    """Count results by outcome.

    'results' -- A sequence of 'Result' objects.

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

    'results' -- A sequence of 'Result' objects.

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


def run_test(test, context):
    """Run a test.

    'test' -- The 'Test' to run.

    'context' -- The 'Context' object with which to run it.

    returns -- A 'Result' object for the test."""

    result = Result(Result.TEST, test.GetId(), context)

    try:
        # Run the test.
        test.Run(context, result)
    except KeyboardInterrupt:
        # Let this propagate out, so the user can kill the test run.
        raise
    except:
        # The test raised an exception.
        result.NoteException()

    return result


def set_up_resource(resource, context):
    """Set up a resource.

    'resource' -- The 'Resource' to set up.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'Result' object for the setup function."""

    result = Result(Result.RESOURCE, resource.GetId(), context,
                    Result.PASS, { "action" : "setup" } )

    # Set up the resoure.
    try:
        resource.SetUp(context, result)
    except:
        # The resource raised an exception.
        result.NoteException(cause="Uncaught exception.")

    return result


def clean_up_resource(resource, context):
    """Clean up a resource.

    'resource' -- The 'Resource' to clean up.

    'context' -- The 'Context' object with which to run it.

    returns -- A complete 'Result' object for the cleanup function."""

    result = Result(Result.RESOURCE, resource.GetId(), context,
                    Result.PASS, { "action" : "cleanup" } )
    
    # Clean up the resource.
    try:
        val = resource.CleanUp(context, result)
    except:
        # The resource raised an exception.
        result.NoteException(cause="Uncaught exception.")

    return result

########################################################################
# variables
########################################################################

extension_kinds = [ 'database',
                    'resource',
                    'target',
                    'test', ]
"""Names of different kinds of QMTest extension classes."""

__class_caches = {}
"""A dictionary of loaded class caches.

The keys are the kinds in 'extension_kinds'.  The associated value
is itself a dictionary mapping class names to class objects."""

# Initialize the caches.
for kind in extension_kinds:
    __class_caches[kind] = {}

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   database.py
# Author: Mark Mitchell
# Date:   2001-10-05
#
# Contents:
#   QMTest database class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os.path
import qm
from   qm.common import *
import qm.extension
import qm.fields
from   qm.label import *
from   qm.test.base import *

########################################################################
# Classes
########################################################################

class ItemDescriptor:
    """An 'ItemDescriptor' describes a test, resource, or similar entity.

    Some 'Database' operations return an instance of a class derived
    from 'ItemDescriptor', rather than the object described.  For
    example, 'Database.GetTest' returns a 'TestDescriptor', not a
    'Test'.  This additional indirection is an optimization; the
    creation of the actual 'Test' object may be relatively expensive,
    and in many cases all that is needed is information that can be
    gleaned from the descriptor."""

    def __init__(self,
                 database,
                 instance_id,
                 class_name,
                 arguments):
        """Construct an 'ItemDescriptor'.

        'database' -- The 'Database' object in which this entity is
        located.

        'instance_id' -- The label for this entity.

        'class_name' -- The name of the extension class for the entity.
        For example, for a 'TestDescriptor', the 'class_name' is the
        name of the test class.

        'arguments' -- A dictionary mapping argument names to argument
        values.  These arguments will be provided to the extension class
        when the entity is constructed."""

        self.__database = database
        self.__id = instance_id
        self.__class_name = class_name
        self.__arguments = arguments
        self.__working_directory = None
        self.__item = None
        

    def GetDatabase(self):
        """Return the 'Database' containing this entity.

        returns -- The 'Database' object in which this entity is
        located."""

        return self.__database
    
        
    def GetClassName(self):
        """Return the class name of the entity.

        returns -- The name of the extension class for the entity.  For
        example, for a 'TestDescriptor', this method returns the name of
        the test class."""

        return self.__class_name


    def GetClass(self):
        """Return the class of the entity.

        returns -- The Python class object for the entity.  For example,
        for a 'TestDescriptor', this method returns the test class."""

        raise NotImplementedError
    

    def GetClassArguments(self):
        """Return the arguments specified by the test class.

        returns -- A list of 'Field' objects containing all the
        arguments in the class hierarchy.

        Derived classes should not override this method."""

        return qm.extension.get_class_arguments(self.GetClass())
    

    def GetArguments(self):
        """Return the entity arguments.

        returns -- A dictionary mapping argument names to argument
        values.  These arguments will be provided to the extension class
        when the entity is constructed."""

        return self.__arguments


    def GetId(self):
        """Return the label for this entity.

        returns -- The label for this entity."""
        
        return self.__id


    def GetItem(self):
        """Return the entity.

        returns -- An instance of the class returned by 'GetClass'."""

        if not self.__item:
            arguments = self.GetArguments().copy()
            arguments["id"] = self.GetId()
            self.__item = self.GetClass()(arguments)

        return self.__item
    
        
    def SetWorkingDirectory(self, directory_path):
        """Set the directory in which this item will execute.

        'directory_path' -- A path.  When the entity is executed, it
        will execute in this directory."""

        self.__working_directory = directory_path


    def GetWorkingDirectory(self):
        """Return the directory in which this item will execute.

        returns -- The directory in which this entity will execute, or
        'None' if it will it execute in the current directory."""

        return self.__working_directory

    # Helper functions.

    def _Execute(self, context, result, method):
        """Execute the entity.
        
        'context' -- The 'Context' in which the test should be executed,
        or 'None' if the 'method' does not take a 'Context' argument.

        'result' -- The 'Result' object corresponding to this execution.

        'method' -- The method name of the method on the entity that
        should be invoked to perform the execution."""

        working_directory = self.GetWorkingDirectory()
        old_working_directory = None
        
        try:
            if working_directory:
                # Remember the previous working directory so we can
                # restore it.
                old_working_directory = os.getcwd()
                # Change to the working directory appropriate for this
                # test.
                os.chdir(working_directory)
            # Get the item.
            item = self.GetItem()
            # Execute the indicated method.
            if context:
                eval("item.%s(context, result)" % method)
            else:
                eval("item.%s(result)" % method)
        finally:
            # Restore the working directory.
            if old_working_directory:
                os.chdir(old_working_directory)



class TestDescriptor(ItemDescriptor):
    """A test instance."""

    def __init__(self,
                 database,
                 test_id,
                 test_class_name,
                 arguments):
        """Create a new test instance.

        'database' -- The 'Database' containing this test.
        
        'test_id' -- The test ID.

        'test_class_name' -- The name of the test class of which this is
        an instance.

        'arguments' -- This test's arguments to the test class.

        'resources' -- A sequence of IDs of resources to run before and
        after the test is run."""

        # Initialize the base class.
        ItemDescriptor.__init__(self, database,
                                test_id, test_class_name, arguments)

        self.__prerequisites = {}
        for p, o in self.GetArguments().get("prerequisites", []):
            self.__prerequisites[p] = o
            
        # Don't instantiate the test yet.
        self.__test = None


    def GetClass(self):
        """Return the class of the entity.

        returns -- The Python class object for the entity.  For example,
        for a 'TestDescriptor', this method returns the test class."""

        return get_extension_class(self.GetClassName(), 'test',
                                   self.GetDatabase())
    
    
    def GetTest(self):
        """Return the 'Test' object described by this descriptor."""

        return self.GetItem()


    def GetPrerequisites(self):
        """Return a map from prerequisite test IDs to required outcomes."""

        return self.__prerequisites


    def GetResources(self):
        """Return the resources required by this test.

        returns -- A sequence of resource names.  Each name indicates a
        resource that must be available to this test."""

        return self.GetArguments().get("resources", [])


    def GetTargetGroup(self):
        """Returns the pattern for the targets that can run this test.

        returns -- A regular expression (represented as a string) that
        indicates the targets on which this test can be run.  If the
        pattern matches a particular group name, the test can be run
        on targets in that group."""

        return self.GetArguments().get("target_group", ".*")
    
        
    def Run(self, context, result):
        """Execute this test.

        'context' -- The 'Context' in which the test should be executed.

        'result' -- The 'Result' object for this test."""

        self._Execute(context, result, "Run")



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


    def GetClass(self):
        """Return the class of the entity.

        returns -- The Python class object for the entity.  For example,
        for a 'TestDescriptor', this method returns the test class."""

        return get_extension_class(self.GetClassName(), 'resource',
                                   self.GetDatabase())


    def GetResource(self):
        """Return the 'Resource' object described by this descriptor."""

        return self.GetItem()


    def SetUp(self, context, result):
        """Set up the resource.

        'context' -- The 'Context' in which the resource should be executed.

        'result' -- The 'Result' object for this resource."""

        self._Execute(context, result, "SetUp")


    def CleanUp(self, result):
        """Clean up the resource.

        'result' -- The 'Result' object for this resource."""

        self._Execute(None, result, "CleanUp")



class DatabaseError(QMException):
    """An exception relating to a 'Database'.

    All exceptions raised directly by 'Database', or its derived
    classes, will be instances of 'DatabaseError', or a class derived
    from 'DatabaseError'.

    If QMTest catches the exception, it will treat the string
    representation of the exception as an error message to be formatted
    for the user."""
            

class NoSuchTestError(DatabaseError):
    """The specified test does not exist."""

    def __init__(self, test_id):
        """Construct a new 'NoSuchTestError'

        'test_id' -- The name of the test that does not exist."""

        self.test_id = test_id


    def __str__(self):
        """Return a string describing this exception."""

        return qm.error("no such test", test_id=self.test_id)

                        

class NoSuchSuiteError(DatabaseError):
    """The specified suite does not exist."""

    def __init__(self, suite_id):
        """Construct a new 'NoSuchSuiteError'

        'suite_id' -- The name of the suite that does not exist."""

        self.suite_id = suite_id

        
    def __str__(self):
        """Return a string describing this exception."""

        return qm.error("no such suite", suite_id=self.suite_id)



class NoSuchResourceError(DatabaseError):
    """The specified resource does not exist."""

    def __init__(self, resource_id):
        """Construct a new 'NoSuchResourceError'

        'resource_id' -- The name of the resource that does not exist."""

        self.resource_id = resource_id


    def __str__(self):
        """Return a string describing this exception."""

        return qm.error("no such resource", resource_id=self.resource_id)



class Database(qm.extension.Extension):
    """A 'Database' stores tests, testsuites, and resources.

    A 'Database' has two primary functions:

    1. Test storage and retrieval.

       Every test has a unique name, called a "test id". When a new 
       test is created, the 'Database' is responsible for writing that
       test to permanent storage.  Later, QMTest will request the test 
       by providing the database with the test id.  The database must
       retrieve the test from permanent storage.

       QMTest does not put any restrictions on *how* tests are stored.
       The default database implementation uses XML to store tests,
       but any storage format will do.

    2. Test enumeration.

       The 'Database' can tell QMTest what tests are stored in the
       database.  QMTest uses this information in its graphical user
       interface to show the user what tests exist.
       
    A 'Database' stores testsuites and resources in addition to tests.
    The names for tests, testsuites, and resources are all "labels".  A
    label is a special kind of string that is designed to be easily
    convertible to a file name.  For more information, see the
    'qm.label' module.  The namespaces for tests, testsuites, and
    resources are all distinct.  For example, it is OK to have a test
    with the same name as a testsuite.
    
    Every 'Database' is associated with a particular directory on the
    local machine.  In most cases, the 'Database' will store all the
    files it needs within this directory.

    Every 'Database' has an associated 'AttachmentStore'.  An
    'AttachmentStore' is responsible for storing the attachments
    associated with tests.  See the module 'qm.attachment' for more
    information about 'AttachmentStore'.

    'Database' is an abstract class.

    You can extend QMTest by providing your own database implementation.
    One reason to do this is that you may want to store tests in a
    format different from the XML format that QMTest uses by default.
    For example, if you are testing a compiler, you might want to
    represent each test as a source file.  Or, if you are testing a
    SQL database, you might want to represent each test as two files:
    one containing SQL commands to run the test, and one containing
    the output you expect.

    Another reason to provide your own database implementation is that
    you might want to store tests on a remote location.  For example,
    suppose you wanted to allow multiple users to access the same 
    central test database.  You could create a test database that
    created and retrieved tests by communicating with the central
    server.

    To create your own database implementation, you must create a Python
    class derived (directly or indirectly) from 'Database'.  The
    documentation for each method of 'Database' indicates whether you
    must override it in your database implementation.  Some methods may
    be overridden, but do not need to be.  You might want to override
    such a method to provide a more efficient implementation, but QMTest
    will work fine if you just use the default version.

    If QMTest calls a method on a database and that method raises an
    exception that is not caught within the method itself, QMTest will
    catch the exception and continue processing.  Therefore, methods
    here only have to handle exceptions themselves if that is necessary
    to maintain the integrity of the database.

    A single 'Database' may be accessed by multiple threads
    simultaneously.  Therefore, you must take appropriate steps to
    ensure thread-safe access to shared data."""

    arguments = [
        qm.fields.TextField(
            name="label_class",
            title="Label Class",
            description="""The name of the label class used by this database.

            The label class is used to separate names of entities used
            by the database into directories and basenames.""",
            default_value="python_label.PythonLabel"
            )
        ]

    kind = "database"
    
    def __init__(self, path, arguments):
        """Construct a 'Database'.

        'path' -- A string containing the absolute path to the directory
        containing the database.

        'arguments' -- A dictionary mapping attribute names to values.
        
        Derived classes must call this method from their own '__init__'
        methods.  Every derived class must have an '__init__' method that
        takes the path to the directory containing the database as its
        only argument.  The path provided to the derived class '__init__'
        function will always be an absolute path."""

        qm.extension.Extension.__init__(self, arguments)
        
        # The path given must be an absolute path.
        assert os.path.isabs(path)
        self.__path = path

        # Translate the label class name into an actual Python class.
        self.__label_class \
            = get_extension_class(self.label_class, "label", self)
                                          
    # Methods that deal with labels.
    
    def IsValidLabel(self, label, is_component = 1):
        """Return true if 'label' is valid.

        'label' -- A string that is being considered as a label.

        'is_component' -- True if the string being tested is just a
        single component of a label path.
        
        returns -- True if 'label' is a valid name for entities in this
        database."""

        return self.__label_class("").IsValid(label, is_component)


    def JoinLabels(self, *labels):
        """Join the 'labels' together.

        'labels' -- A sequence of strings corresponding to label
        components.

        returns -- A string containing the complete label."""

        if not labels:
            return ""

        return str(apply(self.__label_class(labels[0]).Join,
                         labels[1:]))
    

    def SplitLabel(self, label):
        """Split the label into a pair '(directory, basename)'.

        returns -- A pair of strings '(directory, basename)'."""

        return map(str, self.__label_class(label).Split())


    def SplitLabelLeft(self, label):
        """Split the label into a pair '(parent, subpath)'.
        This is the same operation as SplitLabel, except the split
        occurs at the leftmost separator, not the rightmost, and a
        single-component label comes back in the parent slot.

        returns -- A pair of strings '(parent, subpath)'."""

        return map(str, self.__label_class(label).SplitLeft())


    def LabelBasename(self, label):
        """Return the basename for the 'label'.

        returns -- A string giving the basename for the 'label'."""

        return str(self.__label_class(label).Basename())


    def LabelDirname(self, label):
        """Return the directory name for the 'label'.

        returns -- A string giving the directory name for the 'label'."""

        return str(self.__label_class(label).Dirname())
    

    def LabelSeparator(self):
        """Return the separator character for labels.

        returns -- A string giving the separator character for
        labels."""

        return self.__label_class.sep
    
    
    def _LabelToPath(self, label, extension=""):
        """Return a filesystem path corresponding to this label.

        'label' -- A string giving the label.
        
        'extension' -- A string which is added to each of the components
        but the last.  For example, if 'extension' is '.ext', and
        'Components' returns '('a', 'b', 'c')', the path returned will
        be 'a.ext/b.ext/c' if '/' is the separator character.
        
        returns -- A string giving a relative path in the filesystem
        corresponding to this label."""

        return self.__label_class(label).ToPath(extension)
    
    # Methods that deal with tests.
    
    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def WriteTest(self, test):
        """Store 'test' in the database.

        'test' -- A 'TestDescriptor' indicating the test that should
        be stored.

        'Attachment's associated with 'test' may be located in the
        'AttachmentStore' associated with this database, or in some
        other 'AttachmentStore'.  In the case that they are stored
        elsewhere, they must be copied into the 'AttachmentStore'
        associated with this database by use of the
        'AttachmentStore.Store' method.  The caller, not this method,
        is responsible for removing the original version of the
        attachment, if necessary.
         
        The 'test' may be new, or it may be a new version of an existing
        test.  If it is a new version of an existing test, the database
        may wish to clear out any storage associated with the existing
        test.  However, it is possible that 'Attachment's associated
        with the existing test are still present in 'test', in which
        case it would be a mistake to remove them.

        Derived classes must override this method."""

        raise NotImplementedError


    def RemoveTest(self, test_id):
        """Remove the test named 'test_id' from the database.

        'test_id' -- A label naming the test that should be removed.

        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def HasTest(self, test_id):
        """Check whether or not the database has a test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- True if and only if the database contains a test
        named 'test_id'.  If this function returns true, 'GetTest' will
        usually succeed.  However, they may be circumstances where
        'HasTest' returns true and 'GetTest' does not succeed.  For
        example, someone might remove a critical file from the database
        between the time that 'HasTest' is called and the time that
        'GetTest' is called.

        Derived classes may override this method."""

        try:
            self.GetTest(test_id)
        except NoSuchTestError:
            return 0
        else:
            return 1


    def GetTestIds(self, directory="", scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.
        
        'returns' -- A list of all tests located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise NotImplementedError

    # Methods that deal with suites.

    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'.

        All databases must have an implicit suite called '' that
        contains all tests in the database.  More generally, for each
        directory in the database, there must be a corresponding suite
        that contains all tests in that directory and its
        subdirectories.

        Derived classes must override this method."""

        raise NotImplementedError


    def WriteSuite(self, suite):
        """Store 'suite' in the database.

        'suite' -- An instance of 'Suite' (or a derived class of
        'Suite') that should be stored.  The 'suite' will not be
        implicit.

        The 'suite' may be new, or it may be a new version of an
        existing testsuite.  If 'suite' is a new version of an existing
        suite, it may name fewer tests than the existing version.
        However, this method should not remove any of the tests
        themselves.

        Derived classes must override this method."""

        raise NotImplementedError


    def RemoveSuite(self, suite_id):
        """Remove the suite named 'suite_id' from the database.

        'suite_id' -- A label naming the suite that should be removed.
        The suite will not be implicit.
          
        raises -- 'NoSuchSuiteError' if there is no suite in the
        database named 'test_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def HasSuite(self, suite_id):
        """Check whether or not the database has a suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- True if and only if the database contains a suite
        named 'suite_id'.  If this function returns true, 'GetSuite'
        will usually succeed.  However, they may be circumstances where
        'HasSuite' returns true and 'GetSuite' does not succeed.  For
        example, someone might remove a critical file from the database
        between the time that 'HasSuite' is called and the time that
        'GetSuite' is called.

        All databases must have an implicit suite called "" that
        contains all tests in the database.  More generally, for each
        directory in the database, there must be a corresponding suite
        that contains all tests in that directory and its
        subdirectories.

        Derived classes may override this method."""

        try:
            self.GetSuite(suite_id)
        except NoSuchSuiteError:
            return 0
        else:
            return 1


    def GetSuiteIds(self, directory="", scan_subdirs=1):
        """Return all suite IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all suites located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise NotImplementedError


    # Methods that deal with resources.

    def GetResource(self, resource_id):
        """Return the 'ResourceDescriptor' for the resource 'resouce_id'.

        'resource_id' -- A label naming the resource.

        returns -- A 'ResourceDescriptor' corresponding to 'resource_id'.
        
        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def WriteResource(self, resource):
        """Store 'resource' in the database.

        'resource' -- A 'ResourceDescriptor' indicating the resource that
        should be stored.

        The 'resource' may be new, or it may be a new version of an
        existing resource.

        Derived classes must override this method."""

        raise NotImplementedError


    def RemoveResource(self, resource_id):
        """Remove the resource named 'resource_id' from the database.

        'resource_id' -- A label naming the resource that should be
        removed.

        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def HasResource(self, resource_id):
        """Check whether or not the database has a resource named
        'resource_id'.

        'resource_id' -- A label naming the resource.

        returns -- True if and only if the database contains a resource
        named 'resource_id'.  If this function returns true,
        'GetResource' will usually succeed.  However, they may be
        circumstances where 'HasResource' returns true and 'GetResource'
        does not succeed.  For example, someone might remove a critical
        file from the database between the time that 'HasResource' is
        called and the time that 'GetResource' is called.

        Derived classes may override this method."""

        try:
            self.GetResource(resource_id)
        except NoSuchResourceError:
            return 0
        else:
            return 1


    def GetResourceIds(self, directory="", scan_subdirs=1):
        """Return all resource IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all resources located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise NotImplementedError

    # Miscellaneous methods.

    def GetSubdirectories(self, directory):
        """Return the immediate subdirectories of 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A sequence of (relative) labels indictating the
        immediate subdirectories of 'directory'.  For example, if "a.b"
        and "a.c" are directories in the database, this method will
        return "b" and "c" given "a" as 'directory'.

        Derived classes must override this method."""

        raise NotImplementedError
        
        
    def GetPath(self):
        """Return the directory containing the database.

        returns -- A string containing the absolute path to the
        directory containing the database.

        Derived classes must not override this method."""

        return self.__path
    

    def GetConfigurationDirectory(self):
        """Return the directory containing configuration information.

        returns -- The directory containing configuration information
        for the database.

        Derived classes must not override this method."""

        return get_configuration_directory(self.GetPath())
    

    def GetAttachmentStore(self):
        """Returns the 'AttachmentStore' associated with the database.

        returns -- The 'AttachmentStore' containing the attachments
        associated with tests and resources in this database.

        Derived classes must override this method."""

        raise NotImplementedError


    def GetClassPaths(self):
        """Return directories to search for test and resource classes.

        returns -- A sequence of strings.  Each string is a directory
        that should be searched to locate test and resource classes.
        The directories will be searched in the order they appear.
        QMTest will search other directories (like those in the
        'QMTEST_CLASS_PATH' environment variable) in addition to these
        directories.
        
        For a given database, this method should always return the same
        value; callers are permitted to cache the value returned.

        Derived classes may override this method.  The sequence returned
        by the derived class need not be a superset of the value
        returned by the default implementation (but probably should
        be)."""

        return []


    def GetTestClassNames(self):
        """Return the kinds of tests that the database can store.

        returns -- A sequence of strings.  Each string names a
        class, including the containing module.  Only classes
        of these types can be stored in the database.

        Derived classes may override this method.  The default
        implementation allows all available test classes, but the
        derived class may allow only a subset."""

        return get_extension_class_names('test', self)


    def GetResourceClassNames(self):
        """Return the kinds of resources that the database can store.

        returns -- A sequence of strings.  Each string names a
        class, including the containing module.  Only resources
        of these types can be stored in the database.

        Derived classes may override this method.  The default
        implementation allows all available resource classes, but the
        derived class may allow only a subset."""

        return get_extension_class_names('resource', self)


    def ExpandIds(self, ids):
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

        # We'll collect test and suite IDs in maps, to make duplicate
        # checks efficient.
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
            if self.HasSuite(id):
                add_suite_id(id)
                # Yes.  Load the suite.
                suite = self.GetSuite(id)
                # Determine all the tests and suites contained directly and
                # indirectly in this suite.
                suite_test_ids, sub_suite_ids = suite.GetAllTestAndSuiteIds()
                # Add them.
                map(add_test_id, suite_test_ids)
                map(add_suite_id, sub_suite_ids)
            # Or is this a test ID?
            elif self.HasTest(id):
                # Yes.  Add it.
                add_test_id(id)
            else:
                # It doesn't look like a test or suite ID.
                raise ValueError, id

        # Convert the maps to sequences.
        return test_ids.keys(), suite_ids.keys()

########################################################################
# Functions
########################################################################

def get_configuration_directory(path):
    """Return the configuration directory for the database rooted at 'path'.

    'path' -- The path to the test database.

    returns -- The path to the configuration directory."""

    return os.path.join(path, "QMTest")
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   database.py
# Author: Mark Mitchell
# Date:   2001-10-05
#
# Contents:
#   QMTest database class.
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

import os.path
import qm
import qm.test.base

########################################################################
# classes
########################################################################

class DatabaseError(Exception):
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

        return qm.error("no such test", test_id=test_id)

                        

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



class Database:
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
    to maintain the integrity of the database."""


    def __init__(self, path, store):
        """Construct a 'Database'.

        'path' -- A string containing the absolute path to the directory
        containing the database.

        'store' -- The attachment store that is used to store 
        'Attachment's to tests or resources.

        Derived classes must call this method from there own '__init__'
        methods.  Evey derived class must have an '__init__' method that
        takes the path to the directory containing the database as its
        only argument.  The path provided to the derived class '__init__'
        function will always be an absolute path."""

        # The path given must be an absolute path.
        assert os.path.isabs(path)
        # The path must refer to a directory.
        if not os.path.isdir(path):
            raise DatabaseException, "%s is not a directory" % path

        self.__path = path
        self.__store = store

    # Methods that deal with tests.
    
    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetTest"


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

        raise qm.MethodShouldBeOverriddenError, "Database.WriteTest"


    def RemoveTest(self, test_id):
        """Remove the test named 'test_id' from the database.

        'test_id' -- A label naming the test that should be removed.

        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveTest"


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


    def GetTestIds(self, directory=".", scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.
        
        'returns' -- A list of all tests located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetTestIds"

    # Methods that deal with suites.

    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'.

        All databases must have an implicit suite called '.' that
        contains all tests in the database.  More generally, for each
        directory in the database, there must be a corresponding suite
        that contains all tests in that directory and its
        subdirectories.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuite"


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

        raise qm.MethodShouldBeOverriddenError, "Database.WriteSuite"


    def RemoveSuite(self, suite_id):
        """Remove the suite named 'suite_id' from the database.

        'suite_id' -- A label naming the suite that should be removed.
        The suite will not be implicit.
          
        raises -- 'NoSuchSuiteError' if there is no suite in the
        database named 'test_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveSuite"


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

        All databases must have an implicit suite called '.' that
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


    def GetSuiteIds(self, directory=".", scan_subdirs=1):
        """Return all suite IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all suites located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuiteIds"


    # Methods that deal with resources.

    def GetResource(self, resource_id):
        """Return the 'ResourceDescriptor' for the resource named 'resouce_id'.

        'resource_id' -- A label naming the resource.

        returns -- A 'ResourceDescriptor' corresponding to 'resource_id'.
        
        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetResource"


    def WriteResource(self, resource):
        """Store 'resource' in the database.

        'resource' -- A 'ResourceDescriptor' indicating the resource that
        should be stored.

        The 'resource' may be new, or it may be a new version of an
        existing resource.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.WriteResource"


    def RemoveResource(self, resource_id):
        """Remove the resource named 'resource_id' from the database.

        'resource_id' -- A label naming the resource that should be
        removed.

        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.RemoveResource"


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


    def GetResourceIds(self, directory=".", scan_subdirs=1):
        """Return all resource IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all resources located within 'directory',
        as absolute labels.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetResourceIds"

    # Miscellaneous methods.

    def GetSubdirectories(self, directory):
        """Return the immediate subdirectories of 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A sequence of (relative) labels indictating the
        immediate subdirectories of 'directory'.  For example, if "a.b"
        and "a.c" are directories in the database, this method will
        return "b" and "c" given "a" as 'directory'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSubdirectories"
        
        
    def GetPath(self):
        """Return the directory containing the database.

        returns -- A string containing the absolute path to the
        directory containing the database.

        Derived classes must not override this method."""

        return self.__path
    

    def GetAttachmentStore(self):
        """Returns the 'AttachmentStore' associated with the database.

        returns -- The 'AttachmentStore' containing the attachments
        associated with tests and resources in this database.

        Derived classes must not override this method."""

        return self.__store


    def GetClassPaths(self):
        """Return directories to search for test and resource classes.

        returns -- A sequence of strings.  Each string is a directory
        that should be searched to locate test and resource classes.
        The directories will be searched in the order they appear.
        QMTest will search other directories (like those in the
        'QMTEST_CLASSPATH' environment variable) in addition to these
        directories.
        
        For a given database, this method should always return the same
        value; callers are permitted to cache the value returned.

        Derived classes may override this method.  The sequence
        returned by the derived class need not be a superset of the
        value returned by the default implementation."""

        # Specify the '_classes' subdirectory, if it exists.
        class_dir = os.path.join(self.GetPath(), "_classes")
        if os.path.isdir(class_dir):
            return [class_dir]
        else:
            return []


    def GetTestClasses(self):
        """Return the kinds of tests that the database can store.

        returns -- A sequence of strings.  Each string names a
        class, including the containing module.  Only classes
        of these types can be stored in the database.

        Derived classes may override this method.  The default
        implementation allows all available test classes, but the
        derived class may allow only a subset."""

        return qm.test.base.get_extension_class_names('test')


    def GetResourceClasses(self):
        """Return the kinds of resources that the database can store.

        returns -- A sequence of strings.  Each string names a
        class, including the containing module.  Only resources
        of these types can be stored in the database.

        Derived classes may override this method.  The default
        implementation allows all available resource classes, but the
        derived class may allow only a subset."""

        return qm.test.base.get_extension_class_names('resource')


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

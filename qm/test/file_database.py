########################################################################
#
# File:   file_database.py
# Author: Mark Mitchell
# Date:   2001-10-05
#
# Contents:
#   QMTest FileDatabase class.
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

import dircache
import os
import os.path
from   qm.test.database import *
from   qm.test.directory_suite import *

########################################################################
# classes
########################################################################

class FileDatabase(Database):
    """A 'FileDatabase' stores each test as a single file.

    A 'FileDatabase' is a 'Database' that stores each test, suite,
    or resource as a single file with an extension indicating whether
    it a test, suite, or resource.  In addition, every subdirectory
    that ends with an extension that would normally indicate a suite
    is itself considered an implicit suite.  The contents of the
    implicit suite are all of the tests and suites contained in the
    subdirectory.

    'FileDatabase' is an abstract class."""

    def __init__(self, path, store,
                 test_extension = '.qmt',
                 suite_extension = '.qms',
                 resource_extension = '.qma'):
        """Construct a 'FileDatabase'.

        'path' -- A string containing the absolute path to the directory
        containing the database.

        'store' -- The attachment store that is used to store 
        'Attachment's to tests or resources.
        
        'test_extension' -- The extension (including the leading period)
        that indicates that a file is a test.

        'suite_extension' -- The extension (including the leading
        period) that indicates that a subdirectory, or file, is a test
        suite.

        'resource_extension' -- The extension (including the leading
        period) that indicates that a file is a resource."""
        
	# Initialize base classes.
	qm.test.database.Database.__init__(self, path, store)
        # Save the test extension and suite extension.
        self.__test_extension = test_extension
        self.__suite_extension = suite_extension
        self.__resource_extension = resource_extension
    
    # Methods that deal with tests.

    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes must not override this method."""

        path = self.GetTestPath(test_id)
        if not self._IsTestFile(path):
            raise NoSuchTestError, test_id

        return self._GetTestFromPath(test_id, path)


    def RemoveTest(self, test_id):
        """Remove the test named 'test_id' from the database.

        'test_id' -- A label naming the test that should be removed.

        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        Derived classes may override this method if they need to remove
        additional information from the database."""

        self.__RemoveEntity(test_id, self.__test_extension,
                            NoSuchTestError)


    def GetTestIds(self, directory=".", scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all tests located within 'directory',
        as absolute labels.

        Derived classes must not override this method."""

        # Compute the directory in which to start looking.
        file_dir = self.GetSuitePath(directory)
        # Get all the files that correspond to tests.
        return self._GetLabels(file_dir, scan_subdirs,
                               directory, self._IsTestFile)


    def GetTestPath(self, test_id):
        """Return the file containing 'test_id'.

        'test_id' -- The name of a test.

        returns -- The absolute file name of the file that contains, or
        would contain, 'test_id'.  This method works even if no test
        named 'test_id' exsits."""

        return self._GetPathFromLabel(test_id) + self.__test_extension


    def GetTestExtension(self):
        """Return the extension that indicates a file is a test.

        returns -- The extension (including the leading period) that
        indicates that a file is a test."""

        return self.__test_extension
    
        
    def _IsTestFile(self, path):
        """Returns true if 'path' is a test file.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a test.

        Derived classes may override this method, but only to restrict
        the set of test files.  In particular, a derived class method
        may return false where this method would return true, but
        never vice versa."""

        return (os.path.splitext(path)[1] == self.__test_extension
                and os.path.isfile(path))
                   
    # Methods that deal with suites.

    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'.

        All databases must have an implicit suite called '.' that
        contains all tests in the database.

        Derived classes must not override this method."""

        path = self.GetSuitePath(suite_id)
        if not self._IsSuiteFile(path):
            raise NoSuchSuiteError, suite_id

        # There are two kinds of suites: directories (which are
        # implicit suites), and files (which are explicit suites).
        if os.path.isdir(path):
            return DirectorySuite(self, suite_id)
        else:
            return self._GetSuiteFromPath(suite_id, path)

        
    def RemoveSuite(self, suite_id):
        """Remove the suite named 'suite_id' from the database.

        'suite_id' -- A label naming the suite that should be removed.
        The suite will not be implicit.
        
        raises -- 'NoSuchSuiteError' if there is no suite in the database
        named 'suite_id'.

        Derived classes may override this method if they need to remove
        additional information from the database."""

        self.__RemoveEntity(suite_id, self.__suite_extension,
                            NoSuchSuiteError)


    def GetSuiteIds(self, directory=".", scan_subdirs=1):
        """Return all suite IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all suites located within 'directory',
        as absolute labels.

        Derived classes must not override this method."""

        # Compute the directory in which to start looking.
        file_dir = self.GetSuitePath(directory)
        # Get all the files that correspond to tests.
        return self._GetLabels(file_dir, scan_subdirs, directory,
                               self._IsSuiteFile)


    def GetSuitePath(self, suite_id):
        """Return the file containing 'suite_id'.

        'suite_id' -- The name of a suite.

        returns -- The absolute file name of the file (or directory)
        that contains, or would contain, 'suite_id'.  This method works
        even if no suite named 'suite_id' exsits."""

        # The implicit '.' suite corresponds to the directory in which
        # the database is located.
        if suite_id == '.':
            return self.GetPath()
        else:
            return self._GetPathFromLabel(suite_id) + self.__suite_extension


    def GetSuiteExtension(self):
        """Return the extension that indicates a file is a suite.

        returns -- The extension (including the leading period) that
        indicates that a file is a suite."""

        return self.__suite_extension
    
        
    def _IsSuiteFile(self, path):
        """Returns true if 'path' is a test suite file or directory.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a test.

        Derived classes may override this method, but only to restrict
        the set of suites.  In particular, a derived class method
        may return false where this method would return true, but
        never vice versa."""

        return (path == self.GetPath()
                or (os.path.splitext(path)[1] == self.__suite_extension
                    and (os.path.isfile(path) or os.path.isdir(path))))

    # Methods that deal with resources.

    def GetResource(self, resource_id):
        """Return the 'ResourceDescriptor' for the resource named
        'resource_id'.

        'resource_id' -- A label naming the resource.

        returns -- A 'ResourceDescriptor' corresponding to 'resource_id'.
        
        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'.

        Derived classes must not override this method."""

        path = self.GetResourcePath(resource_id)
        if not self._IsResourceFile(path):
            raise NoSuchResourceError, resource_id

        return self._GetResourceFromPath(resource_id, path)


    def RemoveResource(self, resource_id):
        """Remove the resource named 'resource_id' from the database.

        'resource_id' -- A label naming the resource that should be removed.

        raises -- 'NoSuchResourceError' if there is no resource in the database
        named 'resource_id'.

        Derived classes may override this method if they need to remove
        additional information from the database."""

        self.__RemoveEntity(resource_id, self.__resource_extension,
                            NoSuchResourceError)


    def GetResourceIds(self, directory=".", scan_subdirs=1):
        """Return all resource IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'returns' -- A list of all resources located within 'directory',
        as absolute labels.

        Derived classes must not override this method."""

        # Compute the directory in which to start looking.
        file_dir = self.GetSuitePath(directory)
        # Get all the files that correspond to suites.
        return self._GetLabels(file_dir, scan_subdirs, directory,
                               self._IsResourceFile)


    def GetResourcePath(self, resource_id):
        """Return the file containing 'resource_id'.

        'resource_id' -- The name of a resource.

        returns -- The absolute file name of the file that contains, or
        would contain, 'resource_id'.  This method works even if no
        Resource named 'resource_id' exsits."""

        return self._GetPathFromLabel(resource_id) \
               + self.__resource_extension


    def GetResourceExtension(self):
        """Return the extension that indicates a file is a resource.

        returns -- The extension (including the leading period) that
        indicates that a file is a resource."""

        return self.__resource_extension


    def _IsResourceFile(self, path):
        """Returns true if 'path' is a resource file.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a test.

        Derived classes may override this method, but only to restrict
        the set of resources.  In particular, a derived class method may
        return false where this method would return true, but never vice
        versa."""

        return (os.path.splitext(path)[1] == self.__resource_extension
                and os.path.isfile(path))
    
    # Miscellaneous methods.

    def GetSubdirectories(self, directory):
        """Return the subdirectories of 'directory'.

        'directory' -- A label indicating a directory in the database.

        returns -- A sequence of (relative) labels indictating the
        subdirectories of 'directory'.  For example, if "a.b" and "a.c"
        are directories in the database, this method will return "b" and
        "c" given "a" as 'directory'."""

        subdirs = []
        file_dir = self.GetSuitePath(directory)
        for entry in dircache.listdir(file_dir):
            root = os.path.splitext(entry)[0]
            if not qm.label.is_valid(root, user=1, allow_separator=0):
                continue
            entry_path = os.path.join(file_dir, entry)
            if (self._IsSuiteFile(entry_path)
                and os.path.isdir(entry_path)):
                subdirs.append(root)
        return subdirs
        
    # Derived classes must override these methods.

    def _GetTestFromPath(self, test_id, path):
        """Return a descriptor for the test given by 'path'.

        'test_id' -- The label naming the test.
        
        'path' -- An absolute path to a test file.  The 'path' satisfies
        '_IsTestFile'.

        returns -- A TestDescriptor corresponding to 'test_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, \
              "FileDatabase._GetTestFromPath"
        

    def _GetSuiteFromPath(self, suite_id, path):
        """Return a the 'Suite' given by 'path'.

        'suite_id' -- The label naming the suite.
        
        'path' -- An absolute path to a suite file.  The 'path'
        satisfies '_IsSuiteFile' and is a file, not a directory.

        returns -- A 'Suite' corresponding to 'suite_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, \
              "FileDatabase._GetSuiteFromPath"
        

    def _GetResourceFromPath(self, resource_id, path):
        """Return a descriptor for the resource given by 'path'.

        'resource_id' -- The label naming the resource.
        
        'path' -- An absolute path to a resource file.  The 'path'
        satisfies '_IsResourceFile'.

        returns -- A ResourceDescriptor corresponding to 'resource_id'.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, \
              "FileDatabase._GetResourceFromPath"

    # Derived classes must not override any methods below this point.

    def _GetPathFromLabel(self, label):
        """Returns the file system path corresponding to 'label'.

        'label' -- The id for a test, test suite, or similar entity.

        returns -- The absolute path for the corresponding entry in
        the file system, but without any required extension.

        Derived classes must not override this method."""

        return os.path.join(self.GetPath(),
                            qm.label.to_path(label, self.__suite_extension))


    def _GetLabels(self, directory, scan_subdirs, label, predicate):
        """Returns the labels of entities in 'directory'.

        'directory' -- The absolute path name of the directory in
        which to begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'label' -- The label that corresponds to 'directory'.

        'predicate' -- A function that takes a file name and returns
        a boolean.

        returns -- Labels for all file names in 'directory'.  If
        'scan_subdirs' is true, subdirectories that have
        'self.__suite_extension' as their extension, that satisfy
        'predicate'.

        Derived classes must not override this method."""

        labels = []
        # Create an object that can relativize any labels we find.
        as_absolute = qm.label.AsAbsolute(label)
        # Go through all of the files (and subdirectories) in that
        # directory.
        for entry in dircache.listdir(directory):
            # If the entry name is not a valid label, then pretend it
            # does not exist.  It would not be valid to create an entity
            # with such an id.
            root = os.path.splitext(entry)[0]
            if not qm.label.is_valid(root, user=1, allow_separator=0):
                continue
            # Compute the full path to 'entry'.
            entry_path = os.path.join(directory, entry)
            # If it satisfies the 'predicate', add it to the list.
            if predicate(entry_path):
                labels.append(as_absolute(root))
            # If it is a subdirectory, recurse.
            if (scan_subdirs and os.path.isdir(entry_path)
                and self._IsSuiteFile(entry_path)):
                labels.extend(self._GetLabels(entry_path,
                                              scan_subdirs,
                                              as_absolute(root),
                                              predicate))

        return labels
        
        
    def __RemoveEntity(self, entity_id, extension, exception):
        """Remove an entity.

        'entity_id' -- The name of a test, suite, or resource.

        'extension' -- The extension that will be present on the file
        representing this entity.

        'exception' -- The type of exception to raise if the file
        is not present.

        Derived classes must not override this method."""

        path = self._GetPathFromLabel(entity_id) + extension
        if not os.path.isfile(path):
            raise exception, entity_id

        os.remove(path)
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

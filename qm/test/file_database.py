########################################################################
#
# File:   file_database.py
# Author: Mark Mitchell
# Date:   2001-10-05
#
# Contents:
#   FileDatabase
#   ExtensionFileDatabase
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import dircache
import os
import os.path
from   qm.test.database import *
from   qm.test.directory_suite import *

########################################################################
# Classes
########################################################################

class FileDatabase(Database):
    """A 'FileDatabase' stores each test as a single file.

    A 'FileDatabase' is a 'Database' that stores each test, suite,
    or resource as a single file.  In addition, some subdirectories
    can be considered implicit suites.  The contents of the
    implicit suite are all of the tests and suites contained in the
    subdirectory.

    'FileDatabase' is an abstract class."""

    # Methods that deal with tests.

    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'."""

        path = self.GetTestPath(test_id)
        if not self._IsTestFile(path):
            raise NoSuchTestError, test_id

        return self._GetTestFromPath(test_id, os.path.normpath(path))


    def GetTestPath(self, test_id):
        """Return the file containing 'test_id'.

        'test_id' -- The name of a test.

        returns -- The absolute file name of the file that contains, or
        would contain, 'test_id'.  This method works even if no test
        named 'test_id' exists.

        Derived classes may override this method."""

        return self._GetPathFromLabel(test_id)


    def _IsTestFile(self, path):
        """Returns true if 'path' is a test file.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a test.

        Derived classes must override this method."""

        raise NotImplementedError

    # Methods that deal with suites.

    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'."""

        path = self.GetSuitePath(suite_id)
        if not self._IsSuiteFile(path):
            raise NoSuchSuiteError, suite_id

        # There are two kinds of suites: directories (which are
        # implicit suites), and files (which are explicit suites).
        if os.path.isdir(path):
            return DirectorySuite(self, suite_id)
        else:
            return self._GetSuiteFromPath(suite_id, os.path.normpath(path))

        
    def GetSuitePath(self, suite_id):
        """Return the file containing 'suite_id'.

        'suite_id' -- The name of a suite.

        returns -- The absolute file name of the file (or directory)
        that contains, or would contain, 'suite_id'.  This method works
        even if no suite named 'suite_id' exists.

        Derived classes may override this method."""

        return self._GetPathFromLabel(suite_id)


    def _IsSuiteFile(self, path):
        """Returns true if 'path' is a test suite file or directory.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a test.

        Derived classes may override this method, but only to restrict
        the set of suites.  In particular, a derived class method
        may return false where this method would return true, but
        never vice versa.

        Derived classes must override this method."""

        raise NotImplementedError
    
    # Methods that deal with resources.

    def GetResource(self, resource_id):
        """Return the 'ResourceDescriptor' for the resource named
        'resource_id'.

        'resource_id' -- A label naming the resource.

        returns -- A 'ResourceDescriptor' corresponding to 'resource_id'.
        
        raises -- 'NoSuchResourceError' if there is no resource in the
        database named 'resource_id'."""

        path = self.GetResourcePath(resource_id)
        if not self._IsResourceFile(path):
            raise NoSuchResourceError, resource_id

        return self._GetResourceFromPath(resource_id, os.path.normpath(path))


    def GetResourcePath(self, resource_id):
        """Return the file containing 'resource_id'.

        'resource_id' -- The name of a resource.

        returns -- The absolute file name of the file that contains, or
        would contain, 'resource_id'.  This method works even if no
        Resource named 'resource_id' exists.

        Derived classes may override this method."""

        return self._GetPathFromLabel(resource_id)


    def _IsResourceFile(self, path):
        """Returns true if 'path' is a resource file.

        'path' -- The absolute name of a file.  All relevant
        components in the path name have already been checked to
        ensure that they are valid labels.

        returns -- True iff the file corresponds to a resource.

        Derived classes must override this method."""

        raise NotImplementedError
    
    # Miscellaneous methods.

    def GetRoot(self):
        """Return the root of the test database.

        returns -- The directory that serves as the root of the test
        database.  All paths are relative to this directory.

        Derived classes may override this method."""

        return self.GetPath()
    
        
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
            if not self._AreLabelsPaths():
                root = os.path.splitext(entry)[0]
            else:
                root = entry
            if not self.IsValidLabel(root):
                continue
            entry_path = os.path.join(file_dir, entry)
            if (self._IsSuiteFile(entry_path)
                and os.path.isdir(entry_path)):
                subdirs.append(root)
        return subdirs


    def GetIds(self, kind, directory = "", scan_subdirs = 1):

        # Compute the path name of the directory in which to start.
        file_dir = self.GetSuitePath(directory)
        # Get all the files of the appropriate kind.
        return self._GetLabels(file_dir, scan_subdirs, directory,
                               lambda p: self._IsFile(kind, p))


    def _GetPath(self, kind, id):
        """Returns the file system path corresponding to 'id'.

        'kind' -- An extension kind.

        'id' -- The name of the entity.

        returns -- The path in which the entity is stored."""

        return { Database.RESOURCE : self.GetResourcePath,
                 Database.TEST : self.GetTestPath,
                 Database.SUITE : self.GetSuitePath } [kind] (id)
        
        
    def _IsFile(self, kind, path):
        """Returns true if 'path' is a file of the indicated 'kind'.

        'kind' -- One of 'Database.ITEM_KINDS'.

        'path' -- The path to a file.

        returns -- True iff 'path' is a file of the indicated kind.

        Derived classes must override this method."""

        return { Database.TEST : self._IsTestFile,
                 Database.RESOURCE : self._IsResourceFile,
                 Database.SUITE : self._IsSuiteFile } [kind] (path)
        
    # Derived classes must override these methods.

    def _GetTestFromPath(self, test_id, path):
        """Return a descriptor for the test given by 'path'.

        'test_id' -- The label naming the test.
        
        'path' -- An absolute path to a test file.  The 'path' satisfies
        '_IsTestFile'.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.

        Derived classes must override this method."""

        raise NotImplementedError
        

    def _GetSuiteFromPath(self, suite_id, path):
        """Return a the 'Suite' given by 'path'.

        'suite_id' -- The label naming the suite.
        
        'path' -- An absolute path to a suite file.  The 'path'
        satisfies '_IsSuiteFile' and is a file, not a directory.

        returns -- A 'Suite' corresponding to 'suite_id'.

        Derived classes must override this method."""

        raise NotImplementedError
        

    def _GetResourceFromPath(self, resource_id, path):
        """Return a descriptor for the resource given by 'path'.

        'resource_id' -- The label naming the resource.
        
        'path' -- An absolute path to a resource file.  The 'path'
        satisfies '_IsResourceFile'.

        returns -- A 'ResourceDescriptor' corresponding to
        'resource_id'.

        Derived classes must override this method."""

        raise NotImplementedError


    def _GetPathFromLabel(self, label):
        """Returns the file system path corresponding to 'label'.

        'label' -- The id for a test, test suite, or similar entity.

        returns -- The absolute path for the corresponding entry in
        the file system, but without any required extension."""

        return os.path.join(self.GetRoot(),
                            self._GetRelativeLabelPath(label))


    def _GetLabelFromBasename(self, basename):
        """Returns the label associated with a file named 'basename'.

        'basename' -- The basename of a file, including the extension.

        returns -- The corresponding label.

        Derived classes may override this method."""
 
        return basename


    def _GetLabels(self, directory, scan_subdirs, label, predicate):
        """Returns the labels of entities in 'directory'.

        'directory' -- The absolute path name of the directory in
        which to begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        'label' -- The label that corresponds to 'directory'.

        'predicate' -- A function that takes a file name and returns
        a boolean.

        returns -- Labels for all file names in 'directory'. that
        satisfy 'predicate'  If 'scan_subdirs' is true, subdirectories
        are scanned as well."""

        labels = []

        # Go through all of the files (and subdirectories) in that
        # directory.
        for entry in dircache.listdir(directory):
            entry_label = self._GetLabelFromBasename(entry)
            # If the label is not valid then pretend it
            # does not exist.  It would not be valid to create an entity
            # with such an id.
            if not self.IsValidLabel(entry_label):
                continue
            # Compute the full path to 'entry'.
            entry_path = os.path.join(directory, entry)
            # If it satisfies the 'predicate', add it to the list.
            if predicate(entry_path):
                labels.append(self.JoinLabels(label, entry_label))
            # If it is a subdirectory, recurse.
            if (scan_subdirs and os.path.isdir(entry_path)
                and self._IsSuiteFile(entry_path)):
                labels.extend(self._GetLabels(entry_path,
                                              scan_subdirs,
                                              self.JoinLabels(label, 
                                                              entry_label),
                                              predicate))

        return labels
        

    def RemoveExtension(self, id, kind):

        path = self._GetPath(kind, id)
        if not os.path.isfile(path):
            raise { Database.RESOURCE : NoSuchResourceError,
                    Database.TEST: NoSuchTestError,
                    Database.SUITE: NoSuchSuiteError }[kind], id

        os.remove(path)


    def _AreLabelsPaths(self):
        """Returns true if labels are to be thought of as file names.

        returns -- True if labels are to be thought of as file names.
        If this predicate holds, every label is a path, relative to the
        root of the database.  If false, the labels are translated to
        paths by adding the 'suite_extension' between directories and
        the 'test_extension' or 'resource_extension' at the end of the
        name."""

        return self.label_class == "file_label.FileLabel"


    def _GetRelativeLabelPath(self, label):
        """Returns a representation of 'label' as a relative filename.

        returns -- A relative filename corresponding to 'label'."""

        if self._AreLabelsPaths():
            return label

        return os.path.join(*self.GetLabelComponents(label))



class ExtensionDatabase(FileDatabase):
    """An 'ExtensionFileDatabase' is a 'FileDatabase' where each kind of
    entity (test, suite, resource) has a particular extension.  For
    examples, if tests have the extension '.qmt', then all files ending
    with '.qmt' are considered tests.  If an extension for a particular
    kind of entity is not specified is the empty string, then all files
    will be considered to be that kind of entity.

    'ExtensionDatabase' is an abstract class."""

    arguments = [
        qm.fields.TextField(
            name="test_extension",
            title="Test Extension",
            description="""The extension for test files.
            
            The extension (including the leading period) used for files
            containing tests.""",
            default_value=".qmt"),
        qm.fields.TextField(
            name="suite_extension",
            title="Suite Extension",
            description="""The extension for suite files.
            
            The extension (including the leading period) used for files
            containing suites.""",
            default_value=".qms"),
        qm.fields.TextField(
            name="resource_extension",
            title="Resource Extension",
            description="""The extension for resource files.
            
            The extension (including the leading period) used for files
            containing resources.""",
            default_value=".qma"),
        ]

    def __init__(self, path, arguments):

        FileDatabase.__init__(self, path, arguments)
        self._extensions = { Database.TEST : self.test_extension,
                             Database.RESOURCE : self.resource_extension,
                             Database.SUITE : self.suite_extension }
        
    def GetTestExtension(self):
        """Return the extension that indicates a file is a test.

        returns -- The extension (including the leading period) that
        indicates that a file is a test."""

        return self.test_extension
    
        
    def GetSuiteExtension(self):
        """Return the extension that indicates a file is a suite.

        returns -- The extension (including the leading period) that
        indicates that a file is a suite."""

        return self.suite_extension
    
        
    def GetResourceExtension(self):
        """Return the extension that indicates a file is a resource.

        returns -- The extension (including the leading period) that
        indicates that a file is a resource."""

        return self.resource_extension


    def GetTestPath(self, test_id):

        test_path = self._GetPathFromLabel(test_id)
        if not self._AreLabelsPaths():
            test_path += self.test_extension
        return test_path


    def _IsTestFile(self, path):

        extension = self.GetTestExtension()
        if extension:
            e = os.path.splitext(path)[1]
            if e != extension:
                return 0

        return os.path.isfile(path)

    
    def GetSuitePath(self, suite_id):

        # The top-level suite is just the directory containing the
        # database; no extension is required.
        if suite_id == "":
            return self.GetRoot()
        else:
            suite_path = self._GetPathFromLabel(suite_id)
            if not self._AreLabelsPaths():
                suite_path += self.suite_extension
            return suite_path


    def _IsSuiteFile(self, path):

        if path == self.GetRoot():
            return 1
        
        extension = self.GetSuiteExtension()
        if extension:
            e = os.path.splitext(path)[1]
            if e != extension:
                return 0

        return os.path.isfile(path) or os.path.isdir(path)


    def GetResourcePath(self, resource_id):

        test_path = self._GetPathFromLabel(resource_id)
        if not self._AreLabelsPaths():
            test_path += self.resource_extension
        return test_path
        

    def _IsResourceFile(self, path):

        extension = self.GetResourceExtension()
        if extension:
            e = os.path.splitext(path)[1]
            if e != extension:
                return 0

        return os.path.isfile(path)

        
    def _GetPathFromLabel(self, label):

        if self._AreLabelsPaths():
            path = label
        else:
            path = self._GetRelativeLabelPath(label)

        return os.path.join(self.GetRoot(), path)

        
    def _GetLabelFromBasename(self, basename):

        if self._AreLabelsPaths():
            return basename
        else:
            return os.path.splitext(basename)[0]


    def _GetRelativeLabelPath(self, label):
        """Returns a representation of 'label' as a filename.

        returns -- A filename corresponding to 'label'."""

        if self._AreLabelsPaths():
            return label

        path = ""
        components = self.GetLabelComponents(label)
        if not components:
            return path
        
        for c in components[:-1]:
            path = os.path.join(path, c + self.suite_extension)
        path = os.path.join(path, components[-1])
        return path


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

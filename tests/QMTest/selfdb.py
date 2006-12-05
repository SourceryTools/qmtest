########################################################################
#
# File:   testsuite/QMTest/database.py
# Author: Zack Weinberg
# Date:   2002-08-05
#
# Contents:
#   Test database specific to QMTest self-test suite.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved.
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from   __future__ import nested_scopes
import dircache
import os
import qm
import qm.test.database as database
from   qm.attachment    import FileAttachmentStore
from   qm.test.database import Database, TestDescriptor, ResourceDescriptor
from   qm.test.suite    import Suite
from   xml_database     import XMLDatabase

########################################################################
# classes
########################################################################

class NestedDatabase(Database):
    """Abstract base class for a database nested inside another database.

    The outer database is called the 'parent'.  The nested database
    uses the parent's class path and attachment store.  Also, this
    class provides implementations of all the database Get methods
    suitable for a database that doesn't have any of that object."""

    def __init__(self, path, parent, arguments):
        """Construct a 'NestedDatabase.'

        'path' - A string containing the absolute path to the directory
        containing the database.  This directory must exist.

        'parent' - The database containing this database.

        'arguments' - A dictionary mapping attribute names to values."""
        Database.__init__(self, path, arguments)

        if not os.path.isdir(path):
            raise qm.common.QMException, \
                  qm.error("db path doesn't exist", path=path)


    def GetTest(self, test_id):
        raise NoSuchTestError


    def GetTestIds(self, directory='', scan_subdirs=1):
        return []


    def GetSuite(self, suite_id):
        if suite_id != '':
            raise NoSuchSuiteError
        return Suite(self, suite_id, implicit=1)


    def GetSuiteIds(self, directory='', scan_subdirs=1):
        return ['']


    def GetResource(self, resource_id):
        raise NoSuchResourceError


    def GetResourceIds(self, directory='', scan_subdirs=1):
        return []


    def GetSubdirectories(self, directory):
        return []


    def GetAttachmentStore(self):
        return self.__parent.GetAttachmentStore()


    def GetClassPaths(self):
        return self.__parent.GetClassPaths()



class RegressionDatabase(NestedDatabase):
    """Database storing regression tests for QMTest.

    This database is read-only, i.e. the methods to update it through
    the GUI are not implemented.  It is expected that users will
    update it by creating new test databases manually.

    Currently, there are no subdirectories and no resources in this
    database."""

    def GetTest(self, test_id):
        """Return the 'TestDescriptor' for the test named 'test_id'.

        'test_id' -- A label naming the test.

        returns -- A 'TestDescriptor' corresponding to 'test_id'.
        
        raises -- 'NoSuchTestError' if there is no test in the database
        named 'test_id'.

        The test exists if there is an immediate subdirectory of our path
        which is itself a QMTest test database."""

        (parent, base) = self.SplitLabel(test_id)
        if parent != '':
            raise NoSuchTestError, test_id

        path = os.path.join(self.GetPath(), base)

        if not os.path.isdir(os.path.join(path, "QMTest")):
            raise NoSuchTestError

        return TestDescriptor(self, test_id, 'selftest.RegTest',
                              { 'path' : path })


    def GetTestIds(self, directory='', scan_subdirs=1):
        """Return all test IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.
        
        returns -- A list of all tests located within 'directory',
        as absolute labels.

        There are no subdirectories, so 'scan_subdirs' is ignored.
        Test IDs correspond 1:1 with subdirectories of this directory
        that are QMTest databases."""

        if directory != '':
            raise NoSuchDirectoryError, directory

        p = self.GetPath()
        ids = []

        for entry in dircache.listdir(p):
            if database.is_database(os.path.join(p, entry)):
                ids.append(entry)
        return ids


    def GetSuite(self, suite_id):
        """Return the 'Suite' for the suite named 'suite_id'.

        'suite_id' -- A label naming the suite.

        returns -- An instance of 'Suite' (or a derived class of
        'Suite') corresponding to 'suite_id'.
        
        raises -- 'NoSuchSuiteError' if there is no test in the database
        named 'test_id'.

        As there are no subdirectories, and as we do not allow user creation
        of explicit suites, the only suite in this database is the implicit
        suite, ''."""

        if suite_id != '':
            raise NoSuchSuiteError
        return Suite(self, suite_id, implicit=1,
                     test_ids=self.GetTestIds())


    def GetSuiteIds(self, directory='', scan_subdirs=1):
        """Return all suite IDs that begin with 'directory'.

        'directory' -- A label indicating the directory in which to
        begin the search.

        'scan_subdirs' -- True if (and only if) subdirectories of
        'directory' should be scanned.

        returns -- A list of all suites located within 'directory',
        as absolute labels."""

        assert directory == ''
        return ['']



class UnitDatabase(NestedDatabase):
    """Database storing unit tests for QMTest.  They are stored in the
    'unit' directory; however, the layout and contents of this directory
    is not yet specified.  Therefore, this database is empty."""

    # NestedDatabase does all the work.



class QMSelftestDatabase(Database):
    """Database storing QMTest's own self-test suite.

    This database does not directly contain any tests.  Each subdirectory
    of the database path is mapped to a sub-database, which contains tests;
    all of the methods simply forward to the sub-database.

    Currently there is a hardwired list of subdirectories, and
    modification is not implemented."""


    __subdir_map = {
        'regress' : RegressionDatabase,
        'unit'    : UnitDatabase,
        'xmldb'   : XMLDatabase
    }


    def __init__(self, path, arguments):
        """Construct a 'QMSelftestDatabase.'

        'path' - A string containing the absolute path to the directory
        containing the database.  This directory must exist.

        'parent' - The database containing this database.

        'arguments' - A dictionary mapping attribute names to values.

        Constructing this database implicitly creates sub-databases
        for each subdirectory of 'path' that it knows about."""

        Database.__init__(self, path, arguments)

        if not os.path.isdir(path):
            raise qm.common.QMException, \
                  qm.error("db path doesn't exist", path=path)

        self.__store = FileAttachmentStore(self)

        subdb = {}
        for (subdir, subclass) in self.__subdir_map.items():
            subpath = os.path.join(path, subdir)
            if os.path.isdir(subpath):
                if issubclass(subclass, NestedDatabase):
                    subdb[subdir] = subclass(subpath, self, arguments)
                else:
                    subdb[subdir] = subclass(subpath, arguments)
        self.__subdb = subdb


    def GetAttachmentStore(self):
        return self.__store


    def GetTest(self, test_id):
        return self._GetThing(test_id, 'Test')


    def GetResource(self, resource_id):
        return self._GetThing(resource_id, 'Resource')


    def GetSuite(self, suite_id):
        if suite_id == '':
            return Suite(self, suite_id, implicit=1,
                         suite_ids=self.__subdb.keys())
        else:
            return self._GetThing(suite_id, 'Suite')


    def GetTestIds(self, directory='', scan_subdirs=1):
        return self._GetThingIds(directory, scan_subdirs, 'Test')


    def GetResourceIds(self, directory='', scan_subdirs=1):
        return self._GetThingIds(directory, scan_subdirs, 'Resource')


    def GetSuiteIds(self, directory='', scan_subdirs=1):
        return self._GetThingIds(directory, scan_subdirs, 'Suite', [''])


    def GetSubdirectories(self, directory=''):
        """Return a list of all the immediate subdirectories of 'directory'."""
        if directory == '':
            return self.__subdb.keys()
        else:
            (parent, child) = self.SplitLabelLeft(directory)
            return self.__subdb[parent].GetSubdirectories(child)


    def _GetThing(self, id, what):
        """Look up an object in a sub-database and return a qualified version.

        'id'   -- The ID of the thing to look up.
        'what' -- What kind of thing it is."""

        (parent, child) = self.SplitLabelLeft(id)
        sub = self.__subdb.get(parent)
        if sub is None:
            error = getattr(database, 'NoSuch' + what + 'Error')
            raise error, id

        qualifier = getattr(self, '_Qualify' + what)
        getter = getattr(sub, 'Get' + what)

        return qualifier(parent, getter(child))


    def _GetThingIds(self, directory, scan_subdirs, what, extra_top=[]):
        """Return a list of qualified IDs of objects in the database.

        'directory'     -- The directory containing all the IDs caller
                           is interested in.
        'scan_subdirs'  -- Whether or not to recurse into subdirectories.
        'what'          -- What kind of thing to enumerate.
        'extra_top'     -- Any extra entries to include in the list, if
                           we are looking at the root directory of the
                           database."""

        if directory == '':
            ids = extra_top[:]
            if scan_subdirs:
                for subdir in self.__subdb.keys():
                    ids.extend(self._QualifyThingIds(subdir, '', 1, what))
            return ids

        else:
            (parent, child) = self.SplitLabelLeft(directory)
            return self._QualifyThingIds(parent, child, scan_subdirs, what)


    def _QualifyThingIds(self, parent, child, scan_subdirs, what):
        """Subroutine of _GetThingIds, called once for each top-level
        subdirectory to process.

        'parent'       -- The top-level directory being processed.
        'child'        -- The path being processed within that directory.
        'scan_subdirs' -- Whether or not to recurse into subdirectories.
        'what'         -- What kind of thing to enumerate."""
        
        assert self.__subdb.has_key(parent)

        getter = getattr(self.__subdb[parent], 'Get' + what + 'Ids')
        qids = []
        for id in getter(child, scan_subdirs):
            qids.append(self.JoinLabels(parent, id))
        return qids


    def _QualifyTest(self, parent, test):
        """Convert a TestDescriptor in a sub-database to a TestDescriptor
        in this database.

        'parent' -- The directory name to prepend to the test ID and the
                    IDs of all its resources and prerequisites.
        'test'   -- The test to be converted."""

        prereqs = test.GetPrerequisites()
        qprereqs = map(lambda x: (self.JoinLabels(parent, x[0]), x[1]),
                       prereqs.items())
        resources = test.GetResources()
        qresources = map(lambda r: self.JoinLabels(parent, r),
                         resources)

        arguments = test.GetArguments()
        arguments["prerequisites"] = qprereqs
        arguments["resources"] = qresources

        return TestDescriptor(self,
                              self.JoinLabels(parent, test.GetId()),
                              test.GetClassName(),
                              arguments)


    def _QualifyResource(self, parent, resource):
        """Convert a ResourceDescriptor in a sub-database to a
        ResourceDescriptor in this database.

        'parent'   -- The directory name to prepend to the resource ID.
        'resource' -- The resource to be converted."""

        return ResourceDescriptor(self,
                                  self.JoinLabels(parent, resource.GetId()),
                                  resource.GetClassName(),
                                  resource.GetArguments())


    def _QualifySuite(self, parent, suite):
        """Convert a suite in a sub-database to a suite in this database.

        'parent' -- The directory name to prepend to all test and suite
                    IDs in the suite.
        'suite'  -- The suite to be converted."""

        qtests = []
        qsuites = []

        for t in suite.GetTestIds():
            qtests.append(self.JoinLabels(parent, t))
        
        for s in suite.GetSuiteIds():
            qsuites.append(self.JoinLabels(parent, s))

        id = suite.GetId()
        if id == '':
            qid = parent
        else:
            qid = self.JoinLabels(parent, suite.GetId())

        return Suite(suite.GetDatabase(),
                     qid,
                     suite.IsImplicit(),
                     qtests,
                     qsuites)

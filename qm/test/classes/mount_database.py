########################################################################
#
# File:   mount_database.py
# Author: Mark Mitchell
# Date:   03/19/2003
#
# Contents:
#   MountDatabase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import dircache
import os.path
from   qm.test.database import *
from   qm.test.suite import Suite
from   qm.fields import *
import qm.test.database

########################################################################
# Classes
########################################################################

class MountDatabase(Database):
    """A 'MountDatabase' contains other databases.

    Every contained database has a "mount point", which is a label
    giving the root of the database.  A test with the ID "x" in a
    database with a mount point of "y" has the ID "x.y" in the
    containing database.

    The contained databases are found by looking for subdirectories of
    the 'MountDatabase' directory.  Every immediate subdirectory which
    is itself a QMTest database is mounted; its mount point is the
    name of the subdirectory."""

    class MountedSuite(Suite):
        """A 'MountedSuite' is a suite from a mounted database."""

        def __init__(self, database, suite_id, joiner, suite):

            super(MountDatabase.MountedSuite, self).\
                __init__({},
                         qmtest_id = suite_id,
                         qmtest_database = database)
            self.__suite = suite
            self.__joiner = joiner


        def IsImplicit(self):

            return self.__suite.IsImplicit()

        
        def GetTestIds(self):

            return map(self.__joiner, self.__suite.GetTestIds())
                                                         

        def GetSuiteIds(self):

            return map(self.__joiner, self.__suite.GetSuiteIds())


    mounts = DictionaryField(key_field = TextField(),
                             value_field = TextField(),
                             description=\
                """Dictionary mapping mount points to (sub-)database paths.
                If empty, the database directory is scanned for subdirectories.""")


    def __init__(self, path, arguments):

        # The label class used by the MountDatabase is the label class
        # used by the databases it contains.  They must all use the
        # same label class.
        label_class = None
        implicit = False
        # Find the contained databases.
        self.mounts = arguments.pop('mounts', {})
        self._mounts = {}
        if not self.mounts:
            # Scan local directory.
            implicit = True
            self.mounts = dict([(d, os.path.join(path, d))
                                for d in dircache.listdir(path)])
        else:
            # Translate relative paths into absolute paths.
            tmp = {}
            for k,v in self.mounts.iteritems():
                tmp[k] = os.path.join(path, v)
            self.mounts = tmp
        # Now translate the value from path to database
        for k,v in self.mounts.iteritems():
            if is_database(v):
                db = load_database(v)
                self._mounts[k] = db
                if not label_class:
                    label_class = db.label_class
                elif label_class != db.label_class:
                    raise QMException, \
                          "mounted databases use differing label classes"
            elif not implicit:
                raise QMException, "%s does not contain a test database"%v
                                   
        # Initialize the base class.
        arguments["modifiable"] = "false"
        if label_class:
            arguments["label_class"] = label_class
            
        Database.__init__(self, path, arguments)


        
    def GetIds(self, kind, directory="", scan_subdirs=1):

        ids = []
        if directory == "" and kind == Database.SUITE:
                ids.extend(self._mounts.keys())
        if scan_subdirs:
            dirs = directory and [directory] or self._mounts.keys()
            for d in dirs:
                database, joiner, subdir = self._SelectDatabase(d)
                ids += [joiner(i) for i in database.GetIds(kind, subdir, 1)]
        return ids

    def GetTest(self, test_id):

        joiner, contained_test \
             = self._GetContainedItem(Database.TEST, test_id)

        # Remap the prerequisites.
        arguments = contained_test.GetArguments()
        prerequisites = contained_test.GetPrerequisites()
        if prerequisites:
            new_prerequisites = map(lambda p: (joiner(p[0]), p[1]),
                                    prerequisites.items())
            arguments[Test.PREREQUISITES_FIELD_ID] = new_prerequisites

        # Remap the resources.
        self._AdjustResources(joiner, arguments)

        return TestDescriptor(self,
                              test_id,
                              contained_test.GetClassName(),
                              arguments)
    

    def GetResource(self, resource_id):

        joiner, contained_resource \
             = self._GetContainedItem(Database.RESOURCE, resource_id)

        # Remap the resources.
        arguments = contained_resource.GetArguments()
        self._AdjustResources(joiner, arguments)

        return ResourceDescriptor(self, resource_id,
                                  contained_resource.GetClassName(),
                                  arguments)
    

    def GetSuite(self, suite_id):

        if suite_id == "":
            return Database.GetSuite(self, suite_id)

        joiner, contained_suite \
            = self._GetContainedItem(Database.SUITE, suite_id)
        test_ids = map(joiner, contained_suite.GetTestIds())
        suite_ids = map(joiner, contained_suite.GetSuiteIds())
        return MountDatabase.MountedSuite(self, suite_id,
                                          joiner,
                                          contained_suite)
    

    def GetSubdirectories(self, directory):

        if directory == "":
            return self._mounts.keys()
        database, joiner, dir = self._SelectDatabase(directory)
        return database.GetSubdirectories(dir)
        

    def GetClassPaths(self):

        paths = []
        for db in self._mounts.values():
            paths.extend(db.GetClassPaths())
            paths.append(get_configuration_directory(db.GetPath()))
        return paths


    def _AdjustResources(self, joiner, arguments):
        """Adjust the resource IDs stored in the 'arguments'.

        'joiner' -- A function of one argument which prepends the
        label for a mount point to the label it is given.

        'arguments' -- The arguments to a test or resource class.

        Modifies the arguments to contain resource names that are
        relative to the containing database."""
        
        resources = arguments.get(Runnable.RESOURCE_FIELD_ID)
        if resources:
            new_resources = map(joiner, resources)
            arguments[Runnable.RESOURCE_FIELD_ID] = new_resources
    

    def _GetContainedItem(self, kind, item_id):
        """Return 'item_id' from a mounted database.

        'kind' -- The kind of item to return.

        'item_id' -- The name of the item, in the containing
        database.

        returns -- A tuple '(joiner, item).  The 'item' will be from
        one of the mounted databases.  'joiner' is a function of one
        argument which prepends the mount point to its argument."""

        try:
            database, joiner, item_id = self._SelectDatabase(item_id)

            # Look for the item in the contained database.
            try:
                item = database.GetItem(kind, item_id)
            except NoSuchItemError, e:
                # Reset the id.
                e.item_id = joiner(item_id)
                raise

            return joiner, item
        except:
            raise Database._item_exceptions[kind](item_id)


    def _SelectDatabase(self, item_id):
        """Return the contained database in which 'item_id' can be found.

        'item_id' -- The name of an item in this database.

        returns -- A tuple '(database, joiner, id)' where 'database'
        is a 'Database', 'joiner' is a function of one argument which
        prepends the mount point to a label, and 'id' is the portion
        of 'item_id' that remains after stripping off the mount point
        of 'database'.  If 'item_id' does not correspond to any mount
        point, an exception is raised."""

        mount_point, item_id = self.SplitLabelLeft(item_id)
        db = self._mounts[mount_point]
        return (db, lambda p: self.JoinLabels(mount_point, p), item_id)

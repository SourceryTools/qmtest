########################################################################
#
# File:   regression_database.py
# Author: Mark Mitchell
# Date:   03/20/2003
#
# Contents:
#   QMTest regression database class.
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

########################################################################
# Classes
########################################################################

class RegressionDatabase(Database):
    """Database storing regression tests for QMTest.

    This database is read-only, i.e. the methods to update it through
    the GUI are not implemented.  It is expected that users will
    update it by creating new test databases manually.

    Currently, there are no subdirectories and no resources in this
    database."""

    def __init__(self, path, arguments):

        arguments["modifiable"] = "false"
        Database.__init__(self, path, arguments)

        
    def GetTest(self, test_id):

        path = os.path.join(self.GetPath(), test_id)
        if not is_database(path):
            raise NoSuchTestError

        return TestDescriptor(self, test_id, 'selftest.RegTest',
                              { 'path' : path })

        
    def GetIds(self, kind, directory = "", scan_subdirs = 1):

        assert directory == ""

        ids = []
        # There are no suites or resources in this database.
        if kind == Database.TEST:
            p = self.GetPath()
            for entry in dircache.listdir(p):
                if is_database(os.path.join(p, entry)):
                    ids.append(entry)

        return ids
    

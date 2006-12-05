########################################################################
#
# File:   results_file_database.py
# Author: Nathaniel Smith
# Date:   2003-08-08
#
# Contents:
#   ResultsFileDatabase.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports 
########################################################################

import glob
import os.path
from   qm.test.database import *

########################################################################
# Classes
########################################################################

class ResultsFileDatabase(Database):
    """Database storing result file tests for QMTest.

    Each file in the test directory matching the glob "*.qmr" is
    considered to be a test, and should be a results file resulting from
    running the database "tdb" in the test directory.  So to generate a
    new test, one generally should run "qmtest -D tdb run -o my_test".
    Each test is considered to pass if the latest version of qmtest is
    able to load it in as an expectations file and run with no
    unexpected results.

    This database is read-only, i.e. the methods to update it through
    the GUI are not implemented.  It is expected that users will
    update it by creating new result files automatically.

    Currently, there are no subdirectories and no resources in this
    database."""

    def __init__(self, path, arguments):

        arguments["modifiable"] = "false"
        Database.__init__(self, path, arguments)

        
    def GetTest(self, test_id):

        results_file = os.path.join(self.GetPath(), test_id + ".qmr")
        if not os.path.exists(results_file):
            raise NoSuchTestError
        tdb = os.path.join(self.GetPath(), "tdb")

        return TestDescriptor(self,
                              test_id,
                              "results_file_test.ResultsFileTest",
                              {"results_file": results_file,
                               "tdb": tdb})

        
    def GetIds(self, kind, directory = "", scan_subdirs = 1):

        assert directory == ""

        if kind == Database.TEST:
            p = self.GetPath()
            files = glob.glob(os.path.join(p, "*.qmr"))
            basenames = [os.path.basename(file) for file in files]
            names = [os.path.splitext(file)[0] for file in basenames]
            return names
        else:
            # There are no suites or resources in this database.
            return []

        return ids

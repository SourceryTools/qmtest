########################################################################
#
# File:   dir_run_database.py
# Author: Mark Mitchell
# Date:   2005-08-08
#
# Contents:
#   QMTest DirRunDatabase class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from glob import glob
import os.path
from qm.test import base
from qm.test.reader_test_run import ReaderTestRun
from qm.test.run_database import RunDatabase

########################################################################
# Classes
########################################################################

class DirRunDatabase(RunDatabase):
    """A 'DirRunDatabase' reads test runs from a directory.

    A 'DirRunDatabase' is associated with a given directory.  The
    database consists of all '.qmr' files in the directory.  Each
    '.qmr' file is treated as a result file."""

    def __init__(self, directory, database):
        """Create a new 'DirRunDatabase'.

        'directory' -- The path to the directory containing the
        results files.

        'database' -- The test 'Database' to which the results files
        correspond."""

        self.__runs = []
        # Read through all the .qmr files.
        for f in glob(os.path.join(directory, "*.qmr")):
            try:
                # Create the ResultReader corresponding to f.
                reader = base.load_results(open(f, 'rb'), database)
                run = ReaderTestRun(reader)
            except:
                # If anything goes wrong reading the file, just skip
                # it.
                continue
            # Add this run to the list.
            self.__runs.append(run)


    def GetAllRuns(self):

        return self.__runs
    
    

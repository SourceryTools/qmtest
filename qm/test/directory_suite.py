########################################################################
#
# File:   directory_suite.py
# Author: Mark Mitchell
# Date:   2001-10-06
#
# Contents:
#   QMTest DirectorySuite class.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from qm.test.suite import *

########################################################################
# classes
########################################################################

class DirectorySuite(Suite):
    """A 'DirectorySuite' is a suite corresponding to a directory.

    A 'DirectorySuite' is an implicit suite that contains all tests
    within a given directory.  The directory is given by a label, not
    a file system directory, so a 'DirectorySuite' can work with any
    database."""

    def __init__(self, database, directory):
        """Construct a new 'DirectorySuite'.

        'database' -- The 'Database' instance containing this suite.

        'directory' -- A label giving the directory corresponding to
        this suite."""

        # Construct the base class.
        Suite.__init__(self, database, directory, implicit=1)
        # Remember the database.
        self.__database = database


    def GetTestIds(self):
        """Return the tests contained in this suite.
        
        returns -- A sequence of labels corresponding to the tests
        contained in this suite.  Tests that are contained in this suite
        only because they are contained in a suite which is itself
        contained in this suite are not returned."""

        return self.__database.GetTestIds(self.GetId(), scan_subdirs=0)
    

    def GetSuiteIds(self):
        """Return the suites contained in this suite.
        
        returns -- A sequence of labels corresponding to the suites
        contained in this suite.  Suites that are contained in this
        suite only because they are contained in a suite which is itself
        contained in this suite are not returned."""

        return self.__database.GetSuiteIds(self.GetId(), scan_subdirs=0)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:


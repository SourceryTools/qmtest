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

from qm.test.base import Suite

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


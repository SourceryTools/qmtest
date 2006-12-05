########################################################################
#
# File:   suite.py
# Author: Mark Mitchell
# Date:   11/05/2001
#
# Contents:
#   QMTest Suite class
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.extension

########################################################################
# Classes
########################################################################

class Suite(qm.extension.Extension):
    """A collection of tests.

     A test suite is a collection of tests.  The suite may contain other
    suites by reference as well; all tests contained in these contained
    suites are considered contained in the containing suite as well."""

    arguments = [
       ]

    kind = "suite"

    EXTRA_ID = "qmtest_id"
    """The name of the extra keyword argument to '__init__' that
    specifies the name of the test or resource."""

    EXTRA_DATABASE = "qmtest_database"
    """The name of the extra keyword argument to '__init__' that
    specifies the database containing the test or resource."""


    def __init__(self, arguments, **extras):
        """Construct a new 'Runnable'.
        
        'arguments' -- As for 'Extension.__init__'.
        
        'extras' -- Extra keyword arguments provided by QMTest.
        Derived classes must pass along any unrecognized keyword
        arguments to this method.  All extra keyword arguments
        provided by QMTest will begin with 'qmtest_'.  These arguments
        are provided as keyword arguments so that additional arguments
        can be added in the future without necessitating changes to
        test or resource classes.  Derived classes should not rely in
        any way on the contents of 'extras'."""
        
        qm.extension.Extension.__init__(self, arguments)
        
        self.__id = extras[self.EXTRA_ID]
        self.__database = extras[self.EXTRA_DATABASE]
        
        
    def GetDatabase(self):
        """Return the 'Database' that contains this suite.
        
        returns -- The 'Database' that contains this suite."""
        
        return self.__database
    

    def GetId(self):
        """Return the ID of this test suite."""
        
        return self.__id


    def GetTestIds(self):
        """Return the tests contained in this suite.
        
        returns -- A sequence of labels corresponding to the tests
        contained in this suite.  Tests that are contained in this suite
        only because they are contained in a suite which is itself
        contained in this suite are not returned."""
        
        return []


    def GetSuiteIds(self):
        """Return the suites contained in this suite.
        
        returns -- A sequence of labels corresponding to the suites
        contained in this suite.  Suites that are contained in this suite
        only because they are contained in a suite which is itself
        contained in this suite are not returned."""
        
        return []


    def IsImplicit(self):
        """Return true if this is an implicit test suite.
        
        Implicit test suites cannot be edited."""
        
        raise NotImplementedError
    

    def GetAllTestAndSuiteIds(self):
        """Return the tests/suites contained in this suite and its subsuites.
        
        returns -- A pair '(test_ids, suite_ids)'.  The 'test_ids' and
        'suite_ids' elements are both sequences of labels.  The values
        returned include all tests and suites that are contained in this
        suite and its subsuites, recursively."""
        
        suite = self
        
        test_ids = []
        suite_ids = []
        
        # Maintain a work list of suites to process.
        work_list = [suite]
        # Process until the work list is empty.
        while len(work_list) > 0:
            suite = work_list.pop(0)
            # Accumulate test and resource IDs in the suite.
            test_ids.extend(suite.GetTestIds())
            # Find sub suites in the suite.
            sub_suite_ids = suite.GetSuiteIds()
            # Accumulate them.
            suite_ids.extend(sub_suite_ids)
            # Retrieve the 'Suite' objects.
            sub_suites = map(self.GetDatabase().GetSuite, sub_suite_ids)
            # Don't expand ordinary suites contained in implicit suites.
            if suite.IsImplicit():
                sub_suites = filter(lambda s: s.IsImplicit(), sub_suites)
            # Add contained suites to the work list.
            work_list.extend(sub_suites)

        return test_ids, suite_ids
       
       


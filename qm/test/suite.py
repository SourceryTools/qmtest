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
# classes
########################################################################

class Suite:
   """A collection of tests.

   A test suite is a collection of tests.  The suite may contain other
   suites by reference as well; all tests contained in these contained
   suites are considered contained in the containing suite as well."""

   def __init__(self,
                database,
                suite_id,
                implicit=0,
                test_ids=[],
                suite_ids=[]):
       """Create a new test suite instance.

       'database' -- The database in which this suite is located.
       
       'suite_id' -- The ID of the new suite.

       'implicit' -- If true, this is an implicit suite, generated
       automatically by QMTest.

       'test_ids' -- A sequence of IDs of tests contained in the suite.

       'suite_ids' -- A sequence of IDs of suites contained in the
       suite."""

       self.__database = database
       self.__id = suite_id
       self.__implicit = implicit
       assert self.__implicit or len(resource_ids) == 0
       self.__test_ids = list(test_ids)
       self.__suite_ids = list(suite_ids)


   def GetDatabase(self):
       """Return the 'Database' that contains this suite.

       returns -- The 'Database' that contains this suite."""

       return self.__database

   
   def GetId(self):
       """Return the ID of this test suite."""

       return self.__id


   def IsImplicit(self):
       """Return true if this is an implicit test suite.

       Implicit test suites cannot be edited."""

       return self.__implicit


   def GetTestIds(self):
       """Return the tests contained in this suite.
       
       returns -- A sequence of labels corresponding to the tests
       contained in this suite.  Tests that are contained in this suite
       only because they are contained in a suite which is itself
       contained in this suite are not returned."""

       return self.__test_ids

   
   def GetSuiteIds(self):
       """Return the suites contained in this suite.
       
       returns -- A sequence of labels corresponding to the suites
       contained in this suite.  Suites that are contained in this suite
       only because they are contained in a suite which is itself
       contained in this suite are not returned."""

       return self.__suite_ids


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
       
       

########################################################################
#
# File:   throughput.py
# Author: Mark Mitchell
# Date:   07/31/2003
#
# Contents:
#   Test datbase for testing execution engine throughput.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.fields import *
from qm.test.database import *
from qm.test.result import *
from qm.test.test import *
import random

########################################################################
# Classes
########################################################################

class ThroughputTest(Test):

    def Run(self, context, result):

        return
        

    
class ThroughputDatabase(Database):

    arguments = [
        IntegerField("num_tests",
                     default_value = 100)
        ]

        
    def GetIds(self, kind, directory = "", scan_subdirs = 1):

        if kind != Database.TEST:
            return super(ThroughputDatabase, self).GetIds(kind,
                                                          directory,
                                                          scan_subdirs)

        tests = []
        for x in xrange(self.num_tests):
            tests.append("test%d" % x)

        return tests

        
    def GetTest(self, test_id):

        prereqs = []
        for x in xrange(random.randrange(5)):
            test = "test%d" % random.randrange(self.num_tests)
            outcome = random.choice(Result.outcomes)
            prereqs.append((test, outcome))
            
        return TestDescriptor(self, test_id,
                              "throughput.ThroughputTest",
                              { Test.PREREQUISITES_FIELD_ID : prereqs })

########################################################################
#
# File:   tuple_test.py
# Author: Mark Mitchell
# Date:   2003-07-21
#
# Contents:
#   Test classes for tests written in Python.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.fields
from   qm.test.test import Test

########################################################################
# Classes
########################################################################

class TupleTest(Test):
    """A 'TupleTest' has a single tuple field.

    This test class is used to validate QMTest's tuple processing."""
    
    arguments = [
        qm.fields.TupleField(
            "tuple",
            (qm.fields.IntegerField(name = "integer"),))
        ]


    def Run(self, context, result):

        if self.tuple != [3,]:
            result.Fail("Incorrect tuple contents.",
                        { "TupleTest.value" : str(self.tuple) })

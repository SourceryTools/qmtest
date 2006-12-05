########################################################################
#
# File:   test_interface.py
# Author: Mark Mitchell
# Date:   10/15/2002
#
# Contents:
#   TestInterface test class.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.test.database import Database
from qm.test.test import Test
import types

########################################################################
# Classes
########################################################################

class TestInterface(Test):
    """A 'TestInterface' test tests the interface of the 'Test' class.

    The 'TestInterface' test class is desiged to ensure that the
    interface to test classes does not change."""

    def __init__(self, arguments, **extras):
        """Construct a new 'TestInterface'."""

        # Even though this constructor just passes along its
        # arguments, it makes sure that no changes in the interface to
        # the constructor take place.
        Test.__init__(self, arguments, **extras)


    def Run(self, context, result):

        try:
            if not isinstance(self.GetId(), types.StringType):
                result.Fail("GetId() did not return a string.")
            if not isinstance(self.GetDatabase(), Database):
                result.Fail("GetDatabase() did not return a Database.")
        except:
            result.NoteException(outcome = Result.FAIL)

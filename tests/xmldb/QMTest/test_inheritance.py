########################################################################
#
# File:   test_inheritance.py
# Author: Mark Mitchell
# Date:   12/20/2002
#
# Contents:
#   TestInheritance test class.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.extension
import qm.fields
from   qm.test.test import Test

########################################################################
# Classes
########################################################################

class Base(Test):
    """A 'Base' has one test argument."""

    arguments = [
        qm.fields.IntegerField(name = "a")
        ]



class Derived(Base):
    """A 'Derived' overrides the argument from 'Base'."""

    arguments = [
        qm.fields.IntegerField(name = "a",
                               computed = "true")
        ]

    b = qm.fields.IntegerField(name = "b", default_value = 42)

    def Run(self, context, result):

        args = qm.extension.get_class_arguments_as_dictionary(Derived)
        if args['a'] != Derived.arguments[0]:
            result.Fail("Incorrect argument.")
        elif not args['a'].IsComputed():
            result.Fail("Argument is not computed.")
        elif self.b != args['b'].GetDefaultValue():
            result.Fail("Argument 'b' has wrong value.")

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


    def Run(self, context, result):

        args = qm.extension.get_class_arguments(Derived)
        if args[0] != Derived.arguments[0]:
            result.Fail("Incorrect argument.")
        elif not args[0].IsComputed():
            result.Fail("Argument is not computed.")
        else:
            for a in args[1:]:
                if a.GetName() == "a":
                    result.Fail('Two arguments named \"a\".')
                        

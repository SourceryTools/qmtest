########################################################################
#
# File:   runnable.py
# Author: Mark Mitchell
# Date:   10/11/2002
#
# Contents:
#   QMTest Runnable class.
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
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

class Runnable(qm.extension.Extension):
    """A 'Runnable' can run on a 'Target'.

    'Runnable' is an abstract base class for 'Test' and 'Resource'."""

    class ResourceField(qm.fields.ChoiceField):
        """A 'ResourceField' contains the name of a resource.

        The exact format of the name depends on the test database in use."""

        def GetItems(self):

            database = qm.test.cmdline.get_qmtest().GetDatabase()
            return database.GetResourceIds()



    EXTRA_ID = "qmtest_id"
    """The name of the extra keyword argument to '__init__' that
    specifies the name of the test or resource."""
    
    EXTRA_DATABASE = "qmtest_database"
    """The name of the extra keyword argument to '__init__' that
    specifies the database containing the test or resource."""

    arguments = [
        qm.fields.SetField(
            ResourceField(
                name = "resources",
                title = "Resources",
                description = \
                """Resources on which this test or resource depends.
                
                Before this test or resource is executed, the
                resources on which it depends will be set up.""",
                not_empty_text = "true",
                )),
        ]

    
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
        
        
    def GetId(self):
        """Return the name of this test or resource.

        'context' -- The 'Context' in which this entity is running.
        
        returns -- The name of this test or resource."""

        return self.__id


    def GetDatabase(self):
        """Return the 'Database' in which this test or resource is stored.

        returns -- The 'Database' in which this test or resource is
        stored."""

        return self.__database

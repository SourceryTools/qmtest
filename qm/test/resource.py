########################################################################
#
# File:   resource.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Resource class.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.test.runnable
from   qm.test.test import Test

########################################################################
# Classes
########################################################################

class Resource(qm.test.runnable.Runnable):
    """A 'Resource' sets up before a test and cleans up afterwards.

    Some tests take a lot of work to set up.  For example, a database
    test that checks the result of SQL queries may require that the
    database first be populated with a substantial number of records.
    If there are many tests that all use the same set of records, it
    would be wasteful to set up the database for each test.  It would
    be more efficient to set up the database once, run all of the
    tests, and then remove the databases upon completion.

    You can use a 'Resource' to gain this efficiency.  If a test
    depends on a resource, QMTest will ensure that the resource is
    available before the test runs.  Once all tests that depend on the
    resource have been run QMTest will destroy the resource.

    Each resource class (i.e., class derived from 'Resource')
    describes a set of "arguments".  Each argument has a name and a
    type.  The values of these arguments determine the design-time
    parameters for the resource.  See the documentation for the 'Test'
    class for more complete information.

    Each resource class also defines a 'SetUp' method that indicates how
    to set up the resource, and a 'CleanUp' method that indicates how
    to clean up afterwards.

    'Resource' is an abstract class.

    You can extend QMTest by providing your own resource class
    implementation.  If the resource classes that come with QMTest
    cannot be used conveniently with your application domain, you may
    wish to create a new resource class.

    To create your own resource class, you must create a Python class
    derived (directly or indirectly) from 'Resource'.  The
    documentation for each method of 'Resource' indicates whether you
    must override it in your resource class implementation.  Some
    methods may be overridden, but do not need to be.  You might want
    to override such a method to provide a more efficient
    implementation, but QMTest will work fine if you just use the
    default version.

    If QMTest calls a method on a resource and that method raises an
    exception that is not caught within the method itself, QMTest will
    catch the exception and continue processing."""
    
    kind = "resource"
    
    def SetUp(self, context, result):
        """Set up the resource.

        'context' -- A 'Context' giving run-time parameters to the
        resource.  The resource may place additional variables into
        the 'context'; these variables will be visible to tests that
        depend on the resource.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        This method should not return a value.

        Derived classes must override this method."""

        raise NotImplementedError


    def CleanUp(self, result):
        """Clean up the resource.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        This method should not return a value.

        Derived classes may override this method."""

        pass



########################################################################
# Functions
########################################################################

def resource_adapter(test_class):
    """Return a resource class based on 'test_class'.

    'test_class' -- A 'Test' class.  This argument is not the name of
    a 'Test' class; it is the actuall class object itself.

    returns -- A 'Resource' class.  The 'Resource' class 'SetUp'
    method is equivalent to the 'Test' class 'Run' method.  The
    'CleanUp' action is empty.

    If this function is called more than once with the same
    'test_class', it will return a new class each time."""

    assert test_class.kind == Test.kind

    # Construct a new class.  By listing 'Resource' first, we ensure
    # that the 'kind' field for the new class is 'Resource.kind'.
    class ResourceAdapter(Resource, test_class):
        """A 'ResourceAdapter' is a resource based on a 'Test' class.

        The 'SetUp' method for this class behaves just like the 'Run'
        method for the test class on which this resource is based.""" 

        def SetUp(self, context, result):

            # To set up the resource, just run the underlying test class.
            self.Run(context, result)



    # Return the new class.        
    return ResourceAdapter

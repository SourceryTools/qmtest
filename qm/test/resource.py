########################################################################
#
# File:   resource.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Resource class.
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

import qm

########################################################################
# classes
########################################################################

class Resource:
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
    
    arguments = []
    """A list of the arguments to the resource class.

    Each element of this list should be an instance of 'Field'.  When
    QMTest prompts the user for arguments to create a new resource, it
    will prompt in the order that the fields are provided here.

    Derived classes may redefine this class variable.  However,
    derived classes should not explicitly include the arguments from
    base classes; QMTest will automatically combine all the arguments
    found throughout the class hierarchy."""

    
    def __init__(self, **arguments):
        """Construct a new 'Resource'

        'arguments' -- A dictionary mapping argument names (as
        specified in the 'arguments' class variable) to values.

        This method will place all of the arguments into this objects
        instance dictionary.
        
        Derived classes may override this method.  The Derived class
        method should begin by calling this method."""
        
        self.__dict__.update(arguments)


    def SetUp(self, context, result):
        """Set up the resource.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        This method should not return a value.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Resource.SetUp"


    def CleanUp(self, result):
        """Clean up the resource.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        This method should not return a value.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Resource.CleanUp"

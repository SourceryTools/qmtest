########################################################################
#
# File:   result.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Test class.
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

class Test:
    """A 'Test' is run to check for correct behavior.

    A 'Test' performs some check on the system being tested, and
    indicates whether the check was successful, or whether the
    check failed.

    Each test class (i.e., class derived from 'Test') describes a set
    of "arguments".  Each argument has a name and a type.  The values
    of these arguments determine the design-time parameters for the
    test.  For example, for a test class that executes program and
    checks their exit codes, the arguments might consist of the
    name of the program to execute, and the command-line arguments
    that should be given to that program.  QMTest uses the arguments
    to prompt the user when creating a new test.

    Each test class also defines a 'Run' method that indicates how
    to run tests in that class.  The 'Run' method is responsible for
    actually performing the test and for reporting the results.
    
    'Test' is an abstract class.

    You can extend QMTest by providing your own test class
    implementation.  If the test classes that come with QMTest cannot
    be used conveniently with your application domain, or if you would
    like to report more detailed information about passing and failing
    tests, you may wish to create a new test class.

    To create your own database implementation, you must create a
    Python class derived (directly or indirectly) from 'Test'.  The
    documentation for each method of 'Test' indicates whether you must
    override it in your database implementation.  Some methods may be
    overridden, but do not need to be.  You might want to override
    such a method to provide a more efficient implementation, but
    QMTest will work fine if you just use the default version.

    If QMTest calls a method on a database and that method raises an
    exception that is not caught within the method itself, QMTest will
    catch the exception and continue processing."""

    arguments = []
    """A list of the arguments to the test class.

    Each element of this list should be an instance of 'Field'.  When
    QMTest prompts the user for arguments to create a new test, it
    will prompt in the order that the fields are provided here.

    Derived classes must redefine this class variable."""


    def __init__(self):
        """Construct a new 'Test'.

        Derived classes must override this method.  The derived
        class method should have one argument for each element
        of 'arguments'.  The names of the arguments to the derived
        class version of '__init__' should match the names given
        in 'arguments'.  QMTest will call the derived class
        '__init__' with each parameter bound to the value the user
        specified when creating the test.

        The Derived class method should begin by calling this
        method."""
        
        pass


    def Run(self, context, result):
        """Run the test.

        'context' -- A 'Context' giving run-time parameters to the
        test.

        'result' -- A 'Result' object.  The outcome will be
        'Result.PASS' when this method is called.  The 'result' may be
        modified by this method to indicate outcomes other than
        'Result.PASS' or to add annotations.

        This method should not return a value.

        Derived classes must override this method."""

        raise qm.MethodShouldBeOverriddenError, "Test.Run"

########################################################################
#
# File:   test.py
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
from   qm.fields import *
from   qm.test.cmdline import *

########################################################################
# classes
########################################################################

class TargetGroupField(TextField):
    """A 'TargetGroupField' contains a target group pattern.

    A 'TargetGroupField' is a 'TextField' that has been specialized to
    store target group specifications."""

    def GetDescription(self):
        """Return a description of this field.

        This description is used when displaying detailed help
        information about the field."""

        # Get the basic description.
        desc = TextField.GetDescription(self)
        # Add a list of the available targets.
        desc = desc + "\n\n**Available Target Groups**\n\n"
        groups = map(lambda t: t.GetGroup(), get_qmtest().GetTargets())
        for g in groups:
            desc = desc + "  * " + g + "\n"

        return desc
    
        
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

    To create your own test class, you must create a Python class
    derived (directly or indirectly) from 'Test'.  The documentation
    for each method of 'Test' indicates whether you must override it
    in your test class implementation.  Some methods may be
    overridden, but do not need to be.  You might want to override
    such a method to provide a more efficient implementation, but
    QMTest will work fine if you just use the default version.

    If QMTest calls a method on a test and that method raises an
    exception that is not caught within the method itself, QMTest will
    catch the exception and continue processing."""

    arguments = [
        TargetGroupField(
            name="target_group",
            title="Target Group Pattern",
            description="""The targets on which this test can run.

            A regular expression that indicates the targets on which
            this test can be run.  If the pattern matches a particular
            group name, the test can be run on targets in that
            group.""",
            default_value=".*"
            )
    ]
    """A list of the arguments to the test class.

    Each element of this list should be an instance of 'Field'.  When
    QMTest prompts the user for arguments to create a new test, it
    will prompt in the order that the fields are provided here.

    Derived classes may redefine this class variable.  However,
    derived classes should not explicitly include the arguments from
    base classes; QMTest will automatically combine all the arguments
    found throughout the class hierarchy."""


    def __init__(self, **arguments):
        """Construct a new 'Test'.

        'arguments' -- A dictionary mapping argument names (as
        specified in the 'arguments' class variable) to values.

        This method will place all of the arguments into this objects
        instance dictionary.
        
        Derived classes may override this method.  The Derived class
        method should begin by calling this method."""

        self.__dict__.update(arguments)


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


    def GetTargetGroup(self):
        """Returns the pattern for the targets that can run this test.

        returns -- A regular expression (represented as a string) that
        indicates the targets on which this test can be run.  If the
        pattern matches a particular group name, the test can be run
        on targets in that group."""

        return self.target_group

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

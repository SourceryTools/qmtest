########################################################################
#
# File:   test.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Test class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   __future__ import nested_scopes
import qm
import qm.fields
import qm.test.cmdline
import qm.test.result
import qm.test.runnable

########################################################################
# Classes
########################################################################

class TargetGroupField(qm.fields.TextField):
    """A 'TargetGroupField' contains a target group pattern.

    A target group pattern is a regular expression.  A test will only be
    run on a particular target if the target's group is matched by the
    test's target group pattern."""

    def GetDescription(self):
        """Return a description of this field.

        This description is used when displaying detailed help
        information about the field."""

        # Get the basic description.
        desc = qm.fields.TextField.GetDescription(self)
        # Add a list of the available targets.
        desc = desc + "\n\n**Available Target Groups**\n\n"
        groups = map(lambda t: t.GetGroup(),
                     qm.test.cmdline.get_qmtest().GetTargets())
        for g in groups:
            desc = desc + "  * " + g + "\n"

        return desc



class Test(qm.test.runnable.Runnable):
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

    class OutcomeField(qm.fields.EnumerationField):
        """An 'OutcomeField' contains an outcome."""

        def __init__(self, name, **properties):

            qm.fields.EnumerationField.__init__(
                self, name,
                qm.test.result.Result.PASS,
                [ qm.test.result.Result.PASS,
                  qm.test.result.Result.FAIL,
                  qm.test.result.Result.UNTESTED,
                  qm.test.result.Result.ERROR ],
                **properties)



    class TestField(qm.fields.ChoiceField):
        """A 'TestField' contains the name of a test.

        The exact format of the name depends on the test database in use."""

        def GetItems(self):

            database = qm.test.cmdline.get_qmtest().GetDatabase()
            return database.GetTestIds()


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
            ),
        qm.fields.SetField(
            qm.fields.TupleField(
                "prerequisites",
                (TestField(
                    name = "test_id",
                    title = "Test",
                    description = """The name of the prerequisite test.""",
                    not_empty_text = "true",
                    ),
                 OutcomeField(
                    name = "outcome",
                    title = "Outcome",
                    description \
                    = """The required outcome for the prerequisite test.
                        
                          If the outcome is different from that given here,
                          the dependent test will not be run.""",
                    )),
                title="Prerequisite Tests",
                description="""The tests on which this test depends.
                
                Every test can depend on other tests.  Those tests will be
                run before this test.  If the prerequisite test does not
                have the outcome indicated, this test will not be run.""",
                ))
    ]

    kind = "test"
    
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

        raise NotImplementedError


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

########################################################################
#
# File:   python.py
# Author: Alex Samuel
# Date:   2001-04-03
#
# Contents:
#   Test classes for tests written in Python.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""Test classes for tests written in Python."""

########################################################################
# imports
########################################################################

import qm
import qm.fields
import qm.test.base
from   qm.test.result import *
from   qm.test.test import *
import string
import sys
import types

########################################################################
# classes
########################################################################

class ExecTest(Test):
    """Check that a Python expression evaluates to true.

    An 'ExecTest' test consists of Python source code together with
    an (optional) Python expression.  First the Python code is
    executed.  If it throws an (uncaught) exception the test fails.
    If the optional expression is present, it is then evaluated.  If it
    evaluates to false, the test fails.  Otherwise, the test passes."""

    arguments = [
        qm.fields.TextField(
            name="source",
            title="Python Source Code",
            description="""The source code.

            This code may contain class definitions, function
            definitions, statements, and so forth.  If this code
            throws an uncaught exception, the test will fail.""",
            verbatim="true",
            multiline="true",
            default_value="pass"
            ),

        qm.fields.TextField(
            name="expression",
            title="Python Expression",
            description="""The expression to evaluate.

            If the expression evaluates to true, the test will pass,
            unless the source code above throws an uncaught exception.

            If this field is left blank, it is treated as an expression
            that is always true.""",
            verbatim="true",
            multiline="true",
            default_value="1"
            )
        ]


    def Run(self, context, result):

        # Adjust the source code.
        if self.source is None:
            self.source = ""
        else:
            # Make sure the source ends with a newline.  A user is
            # likely to be confused by the error message if it's
            # missing. 
            if self.source[-1] != "\n":
                self.source = self.source + "\n" 
        global_namespace, local_namespace = make_namespaces(context)
        # Execute the source code.
        try:
            exec self.source in global_namespace, local_namespace
        except:
            # The source raised an unhandled exception, so the test
            # fails
            result.NoteException(cause="Exception executing source.")
        else:
            # The source code executed OK.  Was an additional expression
            # provided? 
            if self.expression is not None:
                # Yes; evaluate it.
                try:
                    value = eval(self.expression,
                                 global_namespace, local_namespace)
                except:
                    # Oops, an exception while evaluating the
                    # expression.  The test fails.
                    result.NoteException(cause=
                                         "Exception evaluating expression.")
                else:
                    # We evaluated the expression.  The test passes iff
                    # the expression's value is boolean true.
                    if not value:
                        result.Fail("Expression evaluates to false.",
                                    { "ExecTest.expr" : self.expression,
                                      "ExecTest.value" : repr(value) })
            else:
                # No expression provided; if we got this far, the test
                # passes. 
                pass


class BaseExceptionTest(Test):
    """Base class for tests of exceptions."""

    arguments = [
        qm.fields.TextField(
            name="source",
            title="Python Source Code",
            description="""The source code.

            This code may contain class definitions, function
            definitions, statements, and so forth.""",
            verbatim="true",
            multiline="true",
            default_value="pass"
            ),

        qm.fields.TextField(
            name="exception_argument",
            title="Exception Argument",
            description="""The expected value of the exception.

            This value is a Python expression which should evaluate
            to the same value as the exception raised.

            If this field is left blank, the value of the exception is
            ignored.""",
            default_value=""
            )
        ]


    def Run(self, context, result):

        # Adjust the exception argument.
        if string.strip(self.exception_argument) != "":
            self.exception_argument = eval(self.exception_argument, {}, {})
            self.has_exception_argument = 1
        else:
            self.has_exception_argument = 0
            
        global_namespace, local_namespace = make_namespaces(context)
        try:
            # Execute the test code.
            exec self.source in global_namespace, local_namespace
        except:
            exc_info = sys.exc_info()
            # Check the exception argument.
            self.CheckArgument(exc_info, result)
            if result.GetOutcome() != Result.PASS:
                return
            # Check that the exception itself is OK.
            self.MakeResult(exc_info, result)
        else:
            # The test code didn't raise an exception.
            result.Fail(qm.message("test did not raise"))


    def CheckArgument(self, exc_info, result):
        """Check that the exception argument matches expectations.

        'result' -- The result object for this test."""

        # Was an expected exception argument specified?
        if self.has_exception_argument:
            # Yes.  Extract the exception argument.
            argument = exc_info[1]
            if cmp(argument, self.exception_argument):
                cause = qm.message("test raised wrong argument")
                result.Fail(cause,
                            { "BaseExceptionTest.type" :
                              str(exc_info[0]),
                              "BaseExceptionTest.argument" :
                               repr(argument) })


    def MakeResult(self, exc_info, result):
        """Check the exception in 'exc_info' and construct the result.

        'result' -- The result object for this test."""

        pass



class ExceptionTest(BaseExceptionTest):
    """Check that the specified Python code raises an exception.

    An 'ExceptionTest' checks that the specified Python code raises a
    particular exception.  The test passes if the exception is an
    instance of the expected class and (optionally) if its value matches
    the expected value.  If the code fails to raise an exception, the
    test fails."""

    arguments = [
        qm.fields.TextField(
            name="exception_class",
            title="Exception Class",
            description="""The expected type of the exception.

            This value is the name of a Python class.  If the
            exception raised is not an instance of this class, the
            test fails.""",
            default_value="Exception"
            )
        ]


    def MakeResult(self, exc_info, result):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.ClassType:
            result.Fail(qm.message("test raised non-object",
                                   exc_type=str(type(exc_info[0]))))
        # Make sure it's an instance of the right class.
        exception_class_name = exc_info[0].__name__
        if exception_class_name != self.exception_class:
            cause = qm.message("test raised wrong class",
                               class_name=exception_class_name)
            result.Fail(cause=cause)


    def CheckArgument(self, exc_info, result):
        """Check that the exception argument matches expectations.

        'result' -- The result object for this test."""

        # Was an expected argument specified?
        if self.has_exception_argument:
            # Extract the actual argument from the exception object.
            try:
                argument = exc_info[1].args
            except:
                # If the "args" were not available, then the exception
                # object does not use the documented interface given
                # for Exception.
                result.Fail("Exception object does not provide access "
                            "to arguments provided to 'raise'",
                            { "ExceptionTest.type" : str(exc_info[0]) })
                return
                
            # Now the expected argument.
            expected_argument = self.exception_argument
            # Python wraps the arguments to class exceptions in strange
            # ways, so wrap the expected argument similarly.  A 'None'
            # argument is represented by an empty tuple.
            if expected_argument is None:
                expected_argument = ()
            # Tuple arguments are unmodified.
            elif type(expected_argument) is types.TupleType:
                pass
            # A non-tuple argument is wrapped in a tuple.
            else:
                expected_argument = (expected_argument, )

            # Compare the actual argument to the expectation.
            if cmp(expected_argument, argument) != 0:
                # We got a different argument.  The test fails.
                cause = qm.message("test raised wrong argument")
                result.Fail(cause,
                            { "ExceptionTest.type" : str(exc_info[0]),
                              "ExceptionTest.argument" : repr(argument) })



class StringExceptionTest(BaseExceptionTest):
    """Check that the specified Python code raises a string exception.

    A 'StringExceptionTest' checks that the specified code throws
    an exception.  The exception must be a string and must have
    the expected value."""

    arguments = [
        qm.fields.TextField(
            name="exception_text",
            title="Exception Text",
            description="The expected exception string.",
            default_value="exception"
            )
        ]


    def MakeResult(self, exc_info, result):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.StringType:
            result.Fail(qm.message("test raised non-string",
                                   exc_type=str(type(exc_info[0]))))
        # Make sure it's the right string.
        if exc_info[0] != self.exception_text:
            result.Fail(qm.message("test raised wrong string",
                                   text=exc_info[0]))
        


########################################################################
# functions
########################################################################

def make_namespaces(context):
    """Construct namespaces for eval/exec of Python test code.

    'context' -- The test context.

    returns -- A pair '(global_namespace, local_namespace)' of maps."""

    # The global namespace contains only the context object.
    global_namespace = {
        "context": context,
        }
    # The local namespace is empty.
    local_namespace = {
        }
    return global_namespace, local_namespace


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

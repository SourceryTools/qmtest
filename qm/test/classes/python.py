########################################################################
#
# File:   python.py
# Author: Alex Samuel
# Date:   2001-04-03
#
# Contents:
#   Test classes for tests written in Python.
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
    """Check the result of a Python expression.

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
            ),
        
        ]


    def __init__(self, source, expression):
        # Store stuff for later.
        if source is None:
            self.__source = ""
        else:
            self.__source = source
            # Make sure the source ends with a newline.  A user is
            # likely to be confused by the error message if it's
            # missing. 
            if self.__source[-1] != "\n":
                self.__source = self.__source + "\n" 
        self.__expression = expression


    def Run(self, context, result):
        global_namespace, local_namespace = make_namespaces(context)
        # Execute the source code.
        try:
            exec self.__source in global_namespace, local_namespace
        except:
            # The source raised an unhandled exception, so the test
            # fails
            result.NoteException(cause="Exception executing source.")
        else:
            # The source code execute OK.  Was an additional expression
            # provided? 
            if self.__expression is not None:
                # Yes; evaluate it.
                try:
                    value = eval(self.__expression,
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
                                    { "ExecTest.value" : repr(value) })
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
            ),

        ]


    def __init__(self, source, exception_argument):
        # Store stuff for later.
        self.__source = source
        if string.strip(exception_argument) != "":
            self.exception_argument = eval(exception_argument, {}, {})


    def Run(self, context, result):
        global_namespace, local_namespace = make_namespaces(context)
        try:
            # Execute the test code.
            exec self.__source in global_namespace, local_namespace
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
        if hasattr(self, "exception_argument"):
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
        BaseExceptionTest.arguments[0],

        qm.fields.TextField(
            name="exception_argument",
            title="Exception Argument",
            description="""The expected value of the exception.

            This value is a Python expression which should evaluate
            to the same value as the exception raised.

            If this field is left blank, the value of the exception is
            ignored.

            A value of "None" or "()" matches an exception raised
            without an argument, as in 'raise ValueError'; an exception
            raised with the argument 'None', as in 'raise ValueError,
            None'; and an exception raised with an empty tuple as its
            argument, as in 'raise ValueError, ()'.""",
            default_value=""
            ),

        qm.fields.TextField(
            name="exception_class",
            title="Exception Class",
            description="""The expected type of the exception.

            This value is the name of a Python class.  If the
            exception raised is not an instance of this class, the
            test fails.""",
            default="Exception"
            ),

        ]


    def __init__(self, source, exception_class, exception_argument):
        # Initialize the base class.
        BaseExceptionTest.__init__(self, source, exception_argument)
        # Store stuff for later.
        self.__exception_class_name = exception_class
                 

    def MakeResult(self, exc_info, result):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.ClassType:
            result.Fail(qm.message("test raised non-object",
                                   exc_type=str(type(exc_info[0]))))
        # Make sure it's an instance of the right class.
        exception_class_name = exc_info[0].__name__
        if exception_class_name != self.__exception_class_name:
            cause = qm.message("test raised wrong class",
                               class_name=exception_class_name)
            result.Fail(cause=cause)


    def CheckArgument(self, exc_info, result):
        """Check that the exception argument matches expectations.

        'result' -- The result object for this test."""

        # Was an expected argument specified?
        if hasattr(self, "exception_argument"):
            # Extract the actual argument from the exception object.  
            argument = exc_info[1].args

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

    arguments = BaseExceptionTest.arguments + [
        qm.fields.TextField(
            name="exception_text",
            title="Exception Text",
            description="The expected exception string.",
            default_value="exception"
            )

        ]


    def __init__(self, source, exception_text, exception_argument):
        # Initialize the base class.
        BaseExceptionTest.__init__(self, source, exception_argument)
        # Store stuff for later.
        self.__exception_text = exception_text


    def MakeResult(self, exc_info, result):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.StringType:
            result.Fail(qm.message("test raised non-string",
                                   exc_type=str(type(exc_info[0]))))
        # Make sure it's the right string.
        if exc_info[0] != self.__exception_text:
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

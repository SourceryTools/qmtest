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
from   qm.test.base import Result
import string
import sys
import types

########################################################################
# classes
########################################################################

class ExecTest:
    """A test consisting of Python code.

    A 'ExecTest' test consists of a body of Python source code, and an
    optional expression.  The Python code is executed; if it raises an
    uncaught exception, the test fails.  If an expression is specified,
    the test passes iff the expression value evaluates to boolean true.
    If no expression is provided, the test passes automatically (unless
    the Python code raises an uncaught exception)."""

    fields = [
        qm.fields.TextField(
            name="source",
            title="Python Source Code",
            description="Python source code to execute.  This may "
            "contain class and function definitions.",
            verbatim="true",
            multiline="true",
            default_value="pass"
            ),

        qm.fields.TextField(
            name="expression",
            title="Python Expression",
            description="""A Python expression indicating the test
            result.  The expression returns a boolean; true indicates
            PASS.  If omitted, the expression is assumed to return a
            passing value, so the test will always pass unless the code
            specified for the 'source' parameter raises an exception.""",
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
        self.__expression = expression


    def Run(self, context):
        global_namespace, local_namespace = make_namespaces(context)
        # Execute the source code.
        try:
            exec self.__source in global_namespace, local_namespace
        except:
            # The source raised an unhandled exception, so the test
            # fails. 
            result = qm.test.base.make_result_for_exception(
                sys.exc_info(),
                outcome=Result.FAIL,
                cause="Exception executing source.")
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
                    result = qm.test.base.make_result_for_exception(
                        sys.exc_info(),
                        outcome=Result.FAIL,
                        cause="Exception evaluating expression.")
                else:
                    # We evaluated the expression.  The test passes iff
                    # the expression's value is boolean true.
                    if value:
                        result = Result(Result.PASS)
                    else:
                        result = Result(
                            Result.FAIL,
                            cause="Expression evaluates to false.",
                            value=repr(value))
            else:
                # No expression provided; if we got this far, the text
                # passes. 
                result = Result(Result.PASS)

        return result



class BaseExceptionTest:
    """Base class for tests of exceptions."""

    fields = [
        qm.fields.TextField(
            name="source",
            title="Python Source Code",
            description="Python source code to execute.",
            verbatim="true",
            multiline="true",
            default_value="pass"
            ),

        qm.fields.TextField(
            name="exception_argument",
            title="Exception Argument",
            description="""If this parameter is specified, a Python
            expression which evaluates to the expected argument of the
            raised expression.  If this parameter is empty, no check
            is performed of the exception argument.""",
            default_value=""
            ),

        ]


    def __init__(self, source, exception_argument):
        # Store stuff for later.
        self.__source = source
        if string.strip(exception_argument) != "":
            self.exception_argument = eval(exception_argument, {}, {})


    def Run(self, context):
        global_namespace, local_namespace = make_namespaces(context)
        try:
            # Execute the test code.
            exec self.__source in global_namespace, local_namespace
        except:
            exc_info = sys.exc_info()
            # Check the exception argument.
            result = self.CheckArgument(exc_info)
            if result is not None:
                return result
            # Check that the exception itself is OK.
            return self.MakeResult(exc_info)
        else:
            # The test code didn't raise an exception.
            return Result(Result.FAIL,
                          cause=qm.message("test did not raise"))


    def CheckArgument(self, exc_info):
        """Check that the exception argument matches expectations.

        returns -- 'None' if the exception argument matches
        expectations.  Otherwise, a 'Result' object indicating
        failure."""

        # Was an expected exception argument specified?
        if hasattr(self, "exception_argument"):
            # Yes.  Extract the exception argument.
            argument = exc_info[1]
            if cmp(argument, self.exception_argument):
                cause = qm.message("test raised wrong argument")
                return Result(Result.FAIL,
                              cause=cause,
                              type=str(exc_info[0]),
                              argument=repr(argument))
        return None


    def MakeResult(self, exc_info):
        """Check the exception in 'exc_info' and construct the result.

        returns -- A 'Result' instance for the test."""

        return Result(Result.PASS)



class ExceptionTest(BaseExceptionTest):
    """Test that Python code raises an exception.

    A test of this class consists of a body of Python code.  The test
    execs the code and checks that it raises an exception.  For the test
    to pass, the code must raise an exception that is an instance of the
    specified Python class.  Optionally, an expected exception argument
    may be specified as well.  If the code does not raise an exception,
    the test fails."""

    fields = [
        BaseExceptionTest.fields[0],

        qm.fields.TextField(
            name="exception_argument",
            title="Exception Argument",
            description="""If this parameter is specified, a Python
            expression which evaluates to the expected argument of the
            raised expression.

            If this parameter is empty, no check is performed of the
            exception argument.

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
            description="""If this parameter is specified, the exception
            is expected to be a class instance.  The value of the
            parameter is the name of Python class of which the exception
            object is expected to be an instance.""",
            default="Exception"
            ),

        ]


    def __init__(self, source, exception_class, exception_argument):
        # Initialize the base class.
        BaseExceptionTest.__init__(self, source, exception_argument)
        # Store stuff for later.
        self.__exception_class_name = exception_class
                 

    def MakeResult(self, exc_info):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.ClassType:
            cause = qm.message("test raised non-object",
                               exc_type=str(type(exc_info[0])))
            return Result(Result.FAIL, cause=cause)
        # Make sure it's an instance of the right class.
        exception_class_name = exc_info[0].__name__
        if exception_class_name != self.__exception_class_name:
            cause = qm.message("test raised wrong class",
                               class_name=exception_class_name)
            return Result(Result.FAIL, cause=cause)

        # OK, it checks out.
        return Result(Result.PASS)


    def CheckArgument(self, exc_info):
        """Check that the exception argument matches expectations.

        returns -- 'None' if the exception argument matches
        expectations.  Otherwise, a 'Result' object indicating
        failure."""

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
                return Result(Result.FAIL,
                              cause=cause,
                              type=str(exc_info[0]),
                              argument=repr(argument))

        return None



class StringExceptionTest(BaseExceptionTest):
    """Test that Python code raises a string exception.

    A test of this class consists of a body of Python code.  The test
    execs the code and checks that it raises an exception.  For the test
    to pass, the code must raise an exception that is a string that
    matches the specified expected exception text.  Optionally, an
    expected exception argument may be specified as well.  If the code
    does not raise an exception, the test fails."""


    fields = BaseExceptionTest.fields + [
        qm.fields.TextField(
            name="exception_text",
            title="Exception Text",
            description="The expected text of the exception string.",
            default_value="exception"
            )

        ]


    def __init__(self, source, exception_text, exception_argument):
        # Initialize the base class.
        BaseExceptionTest.__init__(self, source, exception_argument)
        # Store stuff for later.
        self.__exception_text = exception_text


    def MakeResult(self, exc_info):
        # Make sure the exception is an object.
        if not type(exc_info[0]) is types.StringType:
            cause = qm.message("test raised non-string",
                               exc_type=str(type(exc_info[0])))
            return Result(Result.FAIL, cause=cause)
        # Make sure it's the right string.
        if exc_info[0] != self.__exception_text:
            cause = qm.message("test raised wrong string",
                               text=exc_info[0])
            return Result(Result.FAIL, cause=cause)

        # OK, it checks out.
        return Result(Result.PASS)
        


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

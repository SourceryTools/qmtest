########################################################################
#
# File:   result.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Result class.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import sys
import types

########################################################################
# Classes
########################################################################

class Result:
    """A 'Result' describes the outcome of a test.

    A 'Result' contains two pieces of data: an outcome and a set
    of annotations.  The outcome indicates whether the test passed
    or failed.  More specifically, the outcome may be one of the
    following constants:

    'Result.PASS' -- The test passed.

    'Result.FAIL' -- The test failed.

    'Result.ERROR' -- Something went wrong in the process of trying to
    execute the test.  For example, if the Python code implementing
    the 'Run' method in the test class raised an exception, the
    outcome would be 'Result.ERROR'.

    'Result.UNTESTED' -- QMTest did not even try to run the test.
    For example, if a prerequiste was not satisfied, then this outcome
    will be used.'

    The annotations are a dictionary, mapping strings to strings.
    The indices should be of the form 'class.name' where 'class' is
    the name of the test class that created the annotation.  Any
    annotations created by QMTest, as opposed to the test class, will
    have indices of the form 'qmtest.name'.  Currently, QMTest
    recognizes the following annotations:

    'Result.CAUSE' -- For results whose outcome is not 'FAIL', this
    annotation gives a brief description of why the test failed.  The
    preferred form of this message is a phrase like "Incorrect
    output." or "Exception thrown."  The message should begin with a
    capital letter and end with a period.  Most results formatters
    will display this information prominently.

    'Result.EXCEPTION' -- If an exeption was thrown during the
    test execution, a brief description of the exception.
    
    'Result.TARGET' -- This annotation indicates on which target the
    test was executed.

    'Result.TRACEBACK' -- If an exeption was thrown during the test
    execution, a representation of the traceback indicating where
    the exception was thrown.

    A 'Result' object has methods that allow it to act as a dictionary
    from annotation names to annotation values.  You can directly add
    an annotation to a 'Result' by writing code of the form
    'result[CAUSE] = "Exception thrown."'.
    
    A 'Result' object is also used to describe the outcome of
    executing either setup or cleanup phase of a 'Resource'."""

    # Constants for result kinds.

    RESOURCE = "resource"
    TEST = "test"
    
    # Constants for outcomes.

    FAIL = "FAIL"
    ERROR = "ERROR"
    UNTESTED = "UNTESTED"
    PASS = "PASS"

    # Constants for predefined annotations.

    ACTION = "qmtest.action"
    CAUSE = "qmtest.cause"
    EXCEPTION = "qmtest.exception"
    RESOURCE = "qmtest.resource"
    TARGET = "qmtest.target"
    TRACEBACK = "qmtest.traceback"
    
    # Other class variables.

    kinds = [ RESOURCE, TEST ]
    """A list of the possible kinds."""
    
    outcomes = [ ERROR, FAIL, UNTESTED, PASS ]
    """A list of the possible outcomes.

    The order of the 'outcomes' is significant; they are ordered from
    most interesting to least interesting from the point of view of
    someone browsing results."""

    def __init__(self, kind, id, context, outcome=PASS, annotations={}):
        """Construct a new 'Result'.

        'kind' -- The kind of result.  The value must be one of the
        'Result.kinds'.
        
        'id' -- The label for the test or resource to which this
        result corresponds.

        'context' -- The 'ContextWrapper' in use when the test (or
        resource) was executed.

        'outcome' -- The outcome associated with the test.  The value
        must be one of the 'Result.outcomes'.

        'annotations' -- The annotations associated with the test."""

        assert kind in Result.kinds
        assert outcome in Result.outcomes

        self.__kind = kind
        self.__id = id
        self.__context = context
        self.__outcome = outcome
        self.__annotations = annotations.copy()


    def GetKind(self):
        """Return the kind of result this is.

        returns -- The kind of entity ('Result.TEST' or
        'Result.RESOURCE') to which this result corresponds."""

        return self.__kind
    
        
    def GetOutcome(self):
        """Return the outcome associated with the test.

        returns -- The outcome associated with the test.  This value
        will be one of the 'Result.outcomes'."""

        return self.__outcome
    
        
    def SetOutcome(self, outcome):
        """Set the outcome associated with the test.

        'outcome' -- One of the 'Result.outcomes'."""

        assert outcome in Result.outcomes
        self.__outcome = outcome

    def Annotate(self, annotations):
        """Add 'annotations' to the current set of annotations."""
        self.__annotations.update(annotations)

    def Fail(self, cause=None, annotations={}):
        """Mark the test as failing.

        'cause' -- If not 'None', this value becomes the value of the
        'Result.CAUSE' annotation.

        'annotations' -- The annotations are added to the current set
        of annotations."""

        self.SetOutcome(Result.FAIL)
        if cause:
            self[Result.CAUSE] = cause
        self.Annotate(annotations)
        
    def GetId(self):
        """Return the label for the test or resource.

        returns -- A label indicating indicating to which test or
        resource this result corresponds."""

        return self.__id


    def GetContext(self):
        """Return the context in which the test or resource executed.

        returns -- The 'ContextWrapper' in which the test or resource
        executed."""

        return self.__context
    

    def GetCause(self):
        """Return the cause of failure, if the test failed.

        returns -- If the test failed, return the cause of the
        failure, if available."""

        if self.has_key(Result.CAUSE):
            return self[Result.CAUSE]
        else:
            return ""
    
        
    def NoteException(self,
                      exc_info=None,
                      cause="An exception occurred.",
                      outcome=ERROR):
        """Note that an exception occurred during execution.

        'exc_info' -- A triple, in the same form as that returned
        from 'sys.exc_info'.  If 'None', the value of 'sys.exc_info()'
        is used instead.

        'cause' -- The value of the 'Result.CAUSE' annotation.

        'outcome' -- The outcome of the test, now that the exception
        has occurred.
        
        A test class can call this method if an exception occurs while
        the test is being run."""

        if not exc_info:
            exc_info = sys.exc_info()
            
        self.SetOutcome(outcome)
        self[Result.CAUSE] = cause
        self[Result.EXCEPTION] = "%s: %s" % exc_info[:2]
        self[Result.TRACEBACK] = qm.format_traceback(exc_info)

        
    def MakeDomNode(self, document):
        """Generate a DOM element node for this result.

        Note that the context is not represented in the DOM node.

        'document' -- The containing DOM document.

        returns -- The element created."""

        # The node is a result element.
        element = document.createElement("result")
        element.setAttribute("id", self.GetId())
        element.setAttribute("kind", self.GetKind())
        # Create and add an element for the outcome.
        outcome_element = document.createElement("outcome")
        text = document.createTextNode(str(self.GetOutcome()))
        outcome_element.appendChild(text)
        element.appendChild(outcome_element)
        # Add a property element for each property.
        keys = self.keys()
        keys.sort()
        for key in keys:
            value = self[key]
            property_element = document.createElement("property")
            # The property name is an attribute.
            property_element.setAttribute("name", str(key))
            if type(value) in qm.common.string_types:
                # The property value is contained in a text mode.
                node = document.createTextNode(str(value))
                property_element.appendChild(node)
            else:
                for text in value:
                    node = document.createTextNode(str(text))
                    property_element.appendChild(node)
            # Add the property element to the result node.
            element.appendChild(property_element)

        return element


    # These methods allow 'Result' to act like a dictionary of
    # annotations.
    
    def __getitem__(self, key):
        assert type(key) in qm.common.string_types
        return self.__annotations[key]


    def __setitem__(self, key, value):
        assert type(key) in qm.common.string_types
        assert type(value) in qm.common.string_types
        self.__annotations[key] = value


    def __delitem__(self, key):
        assert type(key) in qm.common.string_types
        del self.__annotations[key]


    def get(self, key, default=None):
        assert type(key) in qm.common.string_types
        return self.__annotations.get(key, default)


    def has_key(self, key):
        assert type(key) in qm.common.string_types
        return self.__annotations.has_key(key)


    def keys(self):
        return self.__annotations.keys()


    def items(self):
        return self.__annotations.items()

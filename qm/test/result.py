########################################################################
#
# File:   result.py
# Author: Mark Mitchell
# Date:   2001-10-10
#
# Contents:
#   QMTest Result class.
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
from   qm.test.context import ContextException
import sys
import types
import cgi

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
    have indices of the form 'qmtest.name'.

    The annotation values are HTML.  When displayed in the GUI, the
    HTML is inserted directly into the result page; when the
    command-line interface is used the HTML is converted to plain
    text.
    
    Currently, QMTest recognizes the following built-in annotations:

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

    RESOURCE_SETUP = "resource_setup"
    RESOURCE_CLEANUP = "resource_cleanup"
    TEST = "test"
    
    # Constants for outcomes.

    FAIL = "FAIL"
    ERROR = "ERROR"
    UNTESTED = "UNTESTED"
    PASS = "PASS"

    # Constants for predefined annotations.

    CAUSE = "qmtest.cause"
    EXCEPTION = "qmtest.exception"
    RESOURCE = "qmtest.resource"
    TARGET = "qmtest.target"
    TRACEBACK = "qmtest.traceback"
    START_TIME = "qmtest.start_time"
    END_TIME = "qmtest.end_time"
    
    # Other class variables.

    kinds = [ RESOURCE_SETUP, RESOURCE_CLEANUP, TEST ]
    """A list of the possible kinds."""
    
    outcomes = [ ERROR, FAIL, UNTESTED, PASS ]
    """A list of the possible outcomes.

    The order of the 'outcomes' is significant; they are ordered from
    most interesting to least interesting from the point of view of
    someone browsing results."""

    def __init__(self, kind, id, outcome=PASS, annotations={}):
        """Construct a new 'Result'.

        'kind' -- The kind of result.  The value must be one of the
        'Result.kinds'.
        
        'id' -- The label for the test or resource to which this
        result corresponds.

        'outcome' -- The outcome associated with the test.  The value
        must be one of the 'Result.outcomes'.

        'annotations' -- The annotations associated with the test."""

        assert kind in Result.kinds
        assert outcome in Result.outcomes

        self.__kind = kind
        self.__id = id
        self.__outcome = outcome
        self.__annotations = annotations.copy()


    def __getstate__(self):
        """Return a representation of this result for pickling.

        By using an explicit tuple representation of 'Result's when
        storing them in a pickle file, we decouple our storage format
        from internal implementation details (e.g., the names of private
        variables)."""

        # A tuple containing the data needed to reconstruct a 'Result'.
        # No part of this structure should ever be a user-defined type,
        # because that will introduce interdependencies that we want to
        # avoid.
        return (self.__kind,
                self.__id,
                self.__outcome,
                self.__annotations)


    def __setstate__(self, pickled_state):
        """Construct a 'Result' from its pickled form."""

        if isinstance(pickled_state, dict):
            # Old style pickle, from before we defined '__getstate__'.
            # (Notionally, this is version "0".)  The state is a
            # dictionary containing the variables we used to have.
            self.__kind = pickled_state["_Result__kind"]
            self.__id = pickled_state["_Result__id"]
            self.__outcome = pickled_state["_Result__outcome"]
            self.__annotations = pickled_state["_Result__annotations"]
            # Also has a key "_Result__context" containing a (probably
            # invalid) context object, but we discard it.
        else:
            assert isinstance(pickled_state, tuple) \
                   and len(pickled_state) == 4
            # New style pickle, from after we defined '__getstate__'.
            # (Notionally, this is version "1".)  The state is a tuple
            # containing the values of the variables we care about.
            (self.__kind,
             self.__id,
             self.__outcome,
             self.__annotations) = pickled_state


    def GetKind(self):
        """Return the kind of result this is.

        returns -- The kind of entity (one of the 'kinds') to which
        this result corresponds."""

        return self.__kind
    
        
    def GetOutcome(self):
        """Return the outcome associated with the test.

        returns -- The outcome associated with the test.  This value
        will be one of the 'Result.outcomes'."""

        return self.__outcome
    
        
    def SetOutcome(self, outcome, cause = None, annotations = {}):
        """Set the outcome associated with the test.

        'outcome' -- One of the 'Result.outcomes'.

        'cause' -- If not 'None', this value becomes the value of the
        'Result.CAUSE' annotation.

        'annotations' -- The annotations are added to the current set
        of annotations."""

        assert outcome in Result.outcomes
        self.__outcome = outcome
        if cause:
            self.SetCause(cause)
        self.Annotate(annotations)


    def Annotate(self, annotations):
        """Add 'annotations' to the current set of annotations."""
        self.__annotations.update(annotations)


    def Fail(self, cause = None, annotations = {}):
        """Mark the test as failing.

        'cause' -- If not 'None', this value becomes the value of the
        'Result.CAUSE' annotation.

        'annotations' -- The annotations are added to the current set
        of annotations."""

        self.SetOutcome(Result.FAIL, cause, annotations)

        
    def GetId(self):
        """Return the label for the test or resource.

        returns -- A label indicating indicating to which test or
        resource this result corresponds."""

        return self.__id


    def GetCause(self):
        """Return the cause of failure, if the test failed.

        returns -- If the test failed, return the cause of the
        failure, if available."""

        if self.has_key(Result.CAUSE):
            return self[Result.CAUSE]
        else:
            return ""
    

    def SetCause(self, cause):
        """Set the cause of failure.

        'cause' -- A string indicating the cause of failure.  Like all
        annotations, 'cause' will be interested as HTML."""

        self[Result.CAUSE] = cause


    def Quote(self, string):
        """Return a version of string suitable for an annotation value.

        Performs appropriate quoting for a string that should be taken
        verbatim; this includes HTML entity escaping, and addition of
        <pre> tags.

        'string' -- The verbatim string to be quoted.

        returns -- The quoted string."""

        return "<pre>%s</pre>" % cgi.escape(string)


    def NoteException(self,
                      exc_info = None,
                      cause = None,
                      outcome = ERROR):
        """Note that an exception occurred during execution.

        'exc_info' -- A triple, in the same form as that returned
        from 'sys.exc_info'.  If 'None', the value of 'sys.exc_info()'
        is used instead.

        'cause' -- The value of the 'Result.CAUSE' annotation.  If
        'None', a default message is used.

        'outcome' -- The outcome of the test, now that the exception
        has occurred.
        
        A test class can call this method if an exception occurs while
        the test is being run."""

        if not exc_info:
            exc_info = sys.exc_info()

        exception_type = exc_info[0]
        
        # If no cause was specified, use an appropriate message.
        if not cause:
            if exception_type is ContextException:
                cause = str(exc_info[1])
            else:
                cause = "An exception occurred."

        # For a 'ContextException', indicate which context variable
        # was invalid.
        if exception_type is ContextException:
            self["qmtest.context_variable"] = exc_info[1].key
            
        self.SetOutcome(outcome, cause)
        self[Result.EXCEPTION] \
            = self.Quote("%s: %s" % exc_info[:2])
        self[Result.TRACEBACK] \
            = self.Quote(qm.format_traceback(exc_info))

        
    def MakeDomNode(self, document):
        """Generate a DOM element node for this result.

        Note that the context is not represented in the DOM node.

        'document' -- The containing DOM document.

        returns -- The element created."""

        # The node is a result element.
        element = document.createElement("result")
        element.setAttribute("id", self.GetId())
        element.setAttribute("kind", self.GetKind())
        element.setAttribute("outcome", str(self.GetOutcome()))
        # Add an annotation element for each annotation.
        keys = self.keys()
        keys.sort()
        for key in keys:
            value = self[key]
            annotation_element = document.createElement("annotation")
            # The annotation name is an attribute.
            annotation_element.setAttribute("name", str(key))
            # The annotation value is contained in a text node.  The
            # data is enclosed in quotes for robustness if the
            # document is pretty-printed.
            node = document.createTextNode('"' + str(value) + '"')
            annotation_element.appendChild(node)
            # Add the annotation element to the result node.
            element.appendChild(annotation_element)

        return element

    # These methods allow 'Result' to act like a dictionary of
    # annotations.
    
    def __getitem__(self, key):
        assert type(key) in types.StringTypes
        return self.__annotations[key]


    def __setitem__(self, key, value):
        assert type(key) in types.StringTypes
        assert type(value) in types.StringTypes
        self.__annotations[key] = value


    def __delitem__(self, key):
        assert type(key) in types.StringTypes
        del self.__annotations[key]


    def get(self, key, default=None):
        assert type(key) in types.StringTypes
        return self.__annotations.get(key, default)


    def has_key(self, key):
        assert type(key) in types.StringTypes
        return self.__annotations.has_key(key)


    def keys(self):
        return self.__annotations.keys()


    def items(self):
        return self.__annotations.items()


########################################################################
# Variables
########################################################################

__all__ = ["Result"]

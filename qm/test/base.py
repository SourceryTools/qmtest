########################################################################
#
# File:   base.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   Base interfaces and classes.
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

import os
import qm
import qm.graph
import qm.label
import string
import sys
import types
import qm.xmlutil
import xml.dom.ext.reader.Sax

########################################################################
# exceptions
########################################################################

class NoSuchTestError(Exception):
    """The specified test does not exist."""

    pass



class NoSuchSuiteError(Exception):
    """The specified suite does not exist."""

    pass



########################################################################
# classes
########################################################################

class Test:
    """A test instance."""

    def __init__(self,
                 test_id,
                 test_class,
                 arguments,
                 prerequisites,
                 categories):
        """Create a new test instance.

        'test_id' -- The test ID.

        'test_class' -- The name of the test class of which this is an
        instance.

        'arguments' -- This test's arguments to the test class.

        'categories' -- A sequence of names of categories to which this
        test belongs.

        'prerequisites' -- A mapping from prerequisite test ID to
        required outcomes."""

        self.__id = test_id
        self.__test_class = test_class
        self.__arguments = arguments
        self.__prerequisites = prerequisites
        self.__categories = categories

        # Don't instantiate the test yet.
        self.__test = None


    def GetTest(self):
        """Return the underlying user test object."""

        # Perform just-in-time instantiation.
        if self.__test is None:
            self.__test = apply(self.__test_class, [], self.__arguments)

        return self.__test


    def GetClass(self):
        """Return the test class of this test."""

        return self.__test_class
    

    def GetId(self):
        """Return the ID for this instance."""
        
        return self.__id


    def IsInCategory(self, category):
        """Return true if this test is in 'category'."""

        return category in self.__categories


    def GetPrerequisites(self):
        """Return a map from prerequisite test IDs to required outcomes."""

        return self.__prerequisites


    def Run(self, context):
        """Execute this test.

        'context' -- Information about the environment in which the test
        is being executed.
        
        returns -- A 'Result' describing the outcome of the test."""

        return self.GetTest().Run(context)



class Suite:
   """A group of tests."""

   def __init__(self, id): 
       """Create a new test suite instance.

       'id' -- The suite ID."""

       self.__id = id
       self.__tests = []


   def GetId(self):
       """Return the ID for this test suite."""

       return self.__id


   def GetTestIds(self):
       """Return a sequence of the test IDs of the tests in this suite."""

       raise qm.MethodShouldBeOverriddenError, "Suite.GetTestIds"



class Database:
    """A database containing tests."""

    def HasTest(self, test_id):
        """Return true if the database has a test with ID 'test_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.HasTest"


    def GetTest(self, test_id):
        """Return a 'Test' instance for test ID 'test_id'.

        raises -- 'NoSuchTestError' if there is no test in the database
        with ID 'test_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetTest"


    def HasSuite(self, suite_id):
        """Return true if the database has a suite with ID
        'suite_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.HasSuite"


    def GetSuite(self, suite_id):
        """Return a 'Suite' instance for suite ID 'suite_id'.

        raises -- 'NoSuchSuiteError' if there is no suite in the
        database with ID 'suite_id'."""

        raise qm.MethodShouldBeOverriddenError, "Database.GetSuite"



class Result:
    """The result of running a test.

    A result object stores an outcome"""

    # Outcome constants.
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    UNTESTED = "UNTESTED"

    outcomes = [ PASS, FAIL, ERROR, UNTESTED ]


    def __init__(self, outcome, **properties):
        """Initialize a new result object."""

        self.__outcome = outcome
        self.__properties = properties


    def __str__(self):
        parts = map(lambda kv: "%s=%s" % (kv[0], repr(kv[1])),
                    self.__properties.items())
        parts = [ self.__outcome ] + parts
        return "Result(%s)" % string.join(parts, ", ")


    # Methods to emulate a (write-only) map.

    def __setitem__(self, key, value):
        self.__properties[key] = value


    def __delitem__(self, key):
        del self.__properties[key]



class ResultWrapper:
    """A wrapper around a 'Result' object.

    This class allows us to record additional information along with the
    raw result generated by the test class."""

    def __init__(self, test_id, context, result):
        """Create a new test result wrapper.

        'test_id' -- The ID of the test being run.

        'context' -- The context in use when the test was run.

        'result' -- The 'Result' object returned by the test class's
        'Run' method."""

        self.__test_id = test_id
        self.__context = context
        self.__result = result


    def __str__(self):
        return "ResultWrapper(%s, %s)" \
               % (self.__test_id, str(self.__result))


    def __repr__(self):
        return str(self)


    def GetOutcome(self):
        """Return the outcome of this test result."""

        return self.__result._Result__outcome


    def GetTestId(self):
        """Return the ID of the test for which this is a result."""
        
        return self.__test_id


    def GetContext(self):
        """Return the context in use when this result was generated."""

        return self.__context


    def MakeDomElement(self, document):
        """Generate a DOM element node for this result.

        'document' -- The containing DOM document."""

        # The node is a result element.
        element = document.createElement("result")
        element.setAttribute("id", self.GetTestId())
        # Create and add an element for the outcome.
        outcome_element = document.createElement("outcome")
        text = document.createTextNode(str(self.GetOutcome()))
        outcome_element.appendChild(text)
        element.appendChild(outcome_element)
        # Add a property element for each property.
        for key, value in self.items():
            property_element = document.createElement("property")
            # The property name is an attribute.
            property_element.setAttribute("name", str(key))
            # The property value is contained in a text mode.
            text = document.createTextNode(str(value))
            property_element.appendChild(text)
            # Add the property element to the result node.
            element.appendChild(property_element)

        return element


    # Methods to emulate a (read-only) map, to access the properties of
    # the underlying 'Result' object.

    def __getitem__(self, key):
        return self.__result._Result__properties[key]


    def get(self, key, default=None):
        return self.__result._Result__properties.get(key, default)


    def has_key(self, key):
        return self.__result._Result__properties.has_key(key)


    def items(self):
        return self.__result._Result__properties.items()



class Context:
    """Test-time and local configuration for tests.

    A 'Context' object contains all of the information a test needs to
    execute, beyond what is stored as part of the test specification
    itself.  Information in the context can include,

      * Local (per-user, etc.) configuration, such as where to find the
        tested program.

      * Environmental information, such as which machine the test is
        running on.

      * One-time configuration, including test arguments specified on
        the command line.

    A 'Context' object is effectively a mapping object whose keys must
    be labels and values must be strings.
    """

    def __init__(self, **initial_attributes):
        """Construct a new context.

        'initial_attributes' -- Initial key/value pairs to include in
        the context."""

        self.__attributes = initial_attributes
        for key, value in self.__attributes.items():
            self.__ValidateKey(key)
            self.__ValidateValue(value)

        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            self.__ValidateKey(option)
            value = qm.rc.Get(option, None)
            assert value is not None
            self.__ValidateValue(value)
            self.__attributes[option] = value


    # Methods to simulate a map object.

    def __getitem__(self, key):
        return self.__attributes[key]


    def __setitem__(self, key, value):
        self.__ValidateKey(key)
        self.__ValidateValue(value)
        self.__attributes[key] = value


    def __delitem__(self, key):
        del self.__attributes[key]


    def keys(self):
        return self.__attributes.keys()


    def values(self):
        return self.__attributes.values()


    def items(self):
        return self.__attributes.items()


    def copy(self):
        # No need to re-validate.
        result = Context()
        result.__attributes = self.__attributes.copy()
        return result


    # Helper methods.

    def __ValidateKey(self, key):
        """Validate 'key'.

        raises -- 'ValueError' if 'key' is not a string.

        raises -- 'RuntimeError' if 'key' is not a valid label
        (including periods)."""

        if not isinstance(key, types.StringType):
            raise ValueError, "context key must be a string"
        if not qm.label.is_valid(key, allow_separator=1):
            raise RuntimeError, \
                  qm.error("invalid context key", key=key)


    def __ValidateValue(self, value):
        """Validate 'value'.

        raises -- 'ValueError' if 'value' is not a string."""

        if not isinstance(value, types.StringType):
            raise ValueError, "context value must be a string"



class PrerequisiteMapAdapter:
    """A map-like object associating prerequisites with test IDs."""

    def __init__(self, database):
        """Construct a new map."""
        
        self.__database = database


    def __getitem__(self, test_id):
        """Return a sequence of IDs of prerequisite tests of 'test_id'."""

        test = self.__database.GetTest(test_id)
        return test.GetPrerequisites().keys()



class Engine:
   """The test execution engine."""

   def __init__(self, database):
       """Create a new testing engine.

       'database' -- The test database containing the tests on which
       this engine operates."""

       self.__database = database


   def RunTest(self, test_id, context):
       """Run a test.

       'test_id' -- The ID of the test to execute.  

       'context' -- Context to pass to the test.

       returns -- A 'Result' object."""

       results = self.RunTests([ test_id ], context)
       return results[test_id]


   def RunTests(self, test_ids, context, progress_callback=None):
       """Execute several tests.

       'test_ids' -- A sequence of IDs of the tests to run.

       'context' -- Context to pass to the tests.

       'progress_callback' -- If not 'None', a callable that is invoked
       to report test execution progress.  The function takes two
       parameters.  The first is a test ID.  The function is invoked
       once before a test is run, with 'None' as the second argument.
       After the test has been run, the function is called again, with a
       'Result' object as the second argument.

       returns -- A map from test IDs to 'Result' objects of tests that
       were run.  The tests that were run is a superset of
       'test_ids'."""

       # Construct a map-like object for test prerequisites.
       prerequisite_map = PrerequisiteMapAdapter(self.__database)
       # Perform a topological sort to determine the tests that will be
       # run and the order in which to run them.  The sort may return a
       # superset of the original 'test_ids'.
       test_ids = qm.graph.topological_sort(test_ids,
                                            prerequisite_map)
       # Construct a map from test IDs to test objects.
       tests = {}
       for test_id in test_ids:
           tests[test_id] = self.__database.GetTest(test_id)

       # Run tests.  Store the results in an ordered map so that we can
       # retrieve results by test ID efficiently, and also preserve the
       # order in which tests were run.
       results = qm.OrderedMap()
       for test_id in test_ids:
           test = tests[test_id]
           result = None

           # Invoke the callback.
           if progress_callback is not None:
               progress_callback(test_id, None)

           # Check the test's prerequisites.
           for prerequisite_id, outcome in test.GetPrerequisites().items():
               # Because of the topological sort, the prerequisite
               # should already have been run.
               assert results.has_key(prerequisite_id)
               # Did the prerequisite produce the required outcome?
               if results[prerequisite_id].GetOutcome() != outcome:
                   # No.  As a result, we won't run this test.  Create
                   # a result object with the UNTESTED outcome.
                   result = Result(outcome=Result.UNTESTED,
                                   failed_prerequisite=prerequisite_id)
                   # Don't look at other prerequisites.
                   break

           # If we don't already have a result (all prerequisites
           # checked out), actually run the test.
           if result is None:
               try:
                   result = test.Run(context)
               except:
                   # The test raised an exception.  Create a result
                   # object with the ERROR outcome.
                   exception = qm.format_exception(sys.exc_info())
                   result = Result(outcome=Result.ERROR,
                                   exception=exception)
               else:
                   # What did the test return?
                   if isinstance(result, qm.test.base.Result):
                       # A 'Result' instance.  Good; keep it.
                       pass
                   elif result in Result.outcomes:
                       # Just an outcome.  Construct a 'Result' instance
                       # with it.
                       result = Result(outcome=result)
                   else:
                       # Something else.  That's an error.
                       raise RuntimeError, \
                             qm.error("invalid result",
                                      id=test_id,
                                      test_class=test.GetClass().__name__,
                                      result=repr(result))

           # Record the test ID and context by wrapping the result.
           result = ResultWrapper(test_id, context, result)

           # Invoke the callback, if one was specified.
           if progress_callback is not None:
               progress_callback(test_id, result)

           # Store the test result.
           results[test_id] = result

       return results


   def RunSuite(self, suite_id, context):
       """Execute a test suite.

       'suite_id' -- The ID of the suite to run.

       'context' -- Context to pass to the tests.

       returns -- A map from test IDs to 'Result' objects of tests that
       were run.  The tests that were run is a superset of the tests in
       'suite_id'."""

       suite = self.__database.GetSuite(suite_id)
       return self.RunTests(suite.GetTestIds(), context)



########################################################################
# functions
########################################################################

def get_test_class(test_class_name, extra_paths=[]):
    """Return the test class named 'test_class_name'.

    'test_class_name' -- A fully-qualified Python class name.

    'extra_paths' -- Additional file system paths in which to look for
    test classes, analogous to 'PYTHONPATH'.  These paths are searched
    after those specified in the 'QMTEST_CLASSPATH' environment
    variable, but before the standard testa classes.

    returns -- A class object for the subclass of 'Test' that
    corresponds to the requested test class.

    raises -- 'ImportError' if 'test_class_name' cannot be loaded."""

    global __loaded_test_classes

    # Have we already loaded this test class?
    try:
        return __loaded_test_classes[test_class_name]
    except KeyError:
        # Nope; that's OK.
        pass

    # Extract paths from the 'QMTEST_CLASSPATH' environment variable. 
    try:
        user_class_path = os.environ["QMTEST_CLASSPATH"]
        user_class_path = string.split(user_classpath, ":")
    except KeyError:
        # The environment variable isn't set.
        user_class_path = []
    # Construct the full set of paths to search in.
    paths = user_class_path + extra_paths + __builtin_test_class_path
    # Load it.
    test_class = qm.common.load_class(test_class_name, paths)
    # Cache it.
    __loaded_test_classes[test_class_name] = test_class
    # All done.
    return test_class


def expand_and_validate_ids(database, content_ids, id_list):
    """Expand and validate IDs.

    This function examines the IDs in 'content_ids'.  Each ID must be a
    test ID or a suite ID.

      1. Expand suite IDs to the test IDs they contain.

      2. Check that test IDs in 'content_ids' and expanded from suites
         actually exist.

      3. Append test IDs to 'id_list', skipping duplicates.  Any test
         IDs already in 'id_list' are preserved.  The order of tests is
         as specified in 'content_ids', with suites expanded
         depth-first, and the first instance of each duplicate test IDs
         kept.

    raises -- 'ValueError' if an element of 'content_ids' isn't a valid
    ID.

    May also raise other exceptions while expanding suites."""
    
    # We'll keep a map whose keys are test IDs, to detect duplicates
    # efficiently.  Initialize it to test IDs already in 'id_list'.
    id_set = {}
    for test_id in id_list:
        id_set[test_id] = None
    # Scan over inputs.
    for id_ in content_ids:
        # Do we already have a test with this ID?
        if id_set.has_key(id_):
            # Yes, so skip.
            continue
        # Check if it's a test ID.
        if database.HasTest(id_):
            id_list.append(id_)
            id_set[id_] = None
        # Or check if it's a suite ID.
        elif database.HasSuite(id_):
            suite = database.GetSuite(id_)
            ids_in_suite = suite.GetTestIds()
            for test_id in ids_in_suite:
                if not id_set.has_key(test_id):
                    id_list.append(test_id)
                    id_set[test_id] = None
        else:
            # Can't find a match for the ID.
            raise ValueError, id_


def load_outcomes(path):
    """Load test outcomes from a file.

    'path' -- Path to an XML results file.

    returns -- A map from test IDs to outcomes."""

    # Load full results.
    outcomes = load_results(path)
    # Replace full results with outcomes only.
    for test_id in outcomes.keys():
        outcomes[test_id] = outcomes[test_id].GetOutcome()
    return outcomes


def load_results(path):
    """Load test results from a file.

    'path' -- Path to an XML results file.

    returns -- A map from test IDs to 'ResultWrapper' objects."""
    
    # Open the input file.
    results_file = open(path, "r")
    # Read and parse XML.
    reader = xml.dom.ext.reader.Sax.Reader(validate=1)
    try:
        results_document = reader.fromStream(results_file)
    except:
        # FIXME:  Handle parse and validation errors.
        raise
    results_file.close()
    # Extract the result elements.
    return __results_from_dom(results_document.documentElement)


def __results_from_dom(results_node):
    """Extract results from a results element.

    'results_node' -- A DOM node corresponding to a results element.

    returns -- A map from test IDs to 'ResultWrapper' objects."""

    assert results_node.tagName == "results"
    # Extract one result for each result element.
    results = {}
    for result_node in results_node.getElementsByTagName("result"):
        result = __result_from_dom(result_node)
        results[result.GetTestId()] = result
    return results


def __result_from_dom(result_node):
    """Extract a result from a result element.

    'result_node' -- A DOM node corresponding to a result element.

    returns -- A 'ResultWrapper' object."""

    assert result_node.tagName == "result"
    # Extract the outcome, and build a base 'Result' object.
    outcome = qm.xmlutil.get_dom_child_text(result_node, "outcome")
    result = Result(outcome)
    # Extract properties, one for each property element.
    for property_node in result_node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value
    # Extract the test ID.
    test_id = result_node.getAttribute("id")
    # FIXME: Load context?
    context = None
    # Construct a result wrapper around the result.
    return ResultWrapper(test_id, context, result)


########################################################################
# variables
########################################################################

__loaded_test_classes = {}
"""Cache of loaded test classes."""

__builtin_test_class_path = [
    os.path.join(qm.common.get_base_directory(), "test", "classes"),
    ]
"""Standard paths to search for test classes."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

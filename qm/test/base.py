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
import sys
import types

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

   def __init__(self, id):
       """Create a new test instance.

       'id' -- The test ID."""

       self.__id = id


   def GetId(self):
       """Return the ID for this instance."

       return self.__id


   # The fields in this test class.  A mapping from field names to
   # 'Field' instances."""
   fields = {}


   def Run(self, context):
       """Execute this test.

       'context' -- Information about the environment in which the
       test is being executed.

       returns -- A 'Result' describing the outcome of the test."""

       raise qm.MethodShouldBeOverriddenError, "Test.Run"
  


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
    """The result of running a test."""

    # Outcome constants.
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    UNTESTED = "UNTESTED"
    

    def __init__(self, outcome, context=None, **properties):
        """Initialize a new result object."""

        self.__outcome = outcome
        self.__properties = properties


    def __str__(self):
        result = "  OUTCOME: %s\n" % self.__outcome
        for key, value in self.__properties.items():
            result = result + "  %s: %s" % (key, value)
        return result


    def GetOutcome(self):
        """Return the outcome in this result."""

        return self.__outcome


    def __getitem__(self, key):
        return self.__properties[key]


    def __setitem__(self, key, value):
        self.__properties[key] = value


    def __delitem__(self, key):
        del self.__properties[key]
        


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
        if not qm.common.is_valid_label(key, allow_periods=1):
            raise RuntimeError, \
                  qm.error("invalid context key", key=key)


    def __ValidateValue(self, value):
        """Validate 'value'.

        raises -- 'ValueError' if 'value' is not a string."""

        if not isinstance(value, types.StringType):
            raise ValueError, "context value must be a string"



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


   def RunTests(self, test_ids, context):
       """Execute several tests.

       'test_ids' -- A sequence of IDs of the tests to run.

       'context' -- Context to pass to the tests.

       returns -- A map from test IDs to 'Result' objects.  There
       may be IDs in the map which are not in 'test_ids', since
       additional prerequisite tests may have been run."""

       # Construct a map from test IDs to test objects.
       tests = {}
       for test_id in test_ids:
           tests[test_id] = self.__database.GetTest(test_id)

       # FIXME: Handle prerequisites and preactions here.

       # Run tests.
       results = {}
       for test_id in test_ids:
           test = tests[test_id]
           try:
               result = test.Run(context)
           except:
               # The test raised an exception.  Create a result object
               # with the ERROR outcome.
               exception = qm.format_exception(sys.exc_info())
               result = Result(outcome=Result.ERROR,
                               context=context,
                               exception=exception)
           results[test_id] = result
       return results


   def RunSuite(self, suite_id, context):
       """Execute a test suite.

       'suite_id' -- The ID of the suite to run.

       'context' -- Context to pass to the tests.

       returns -- A map from test IDs to 'Result' objects for the tests
       that were run.  There may be IDs in the map which are not in the
       specified suite, since additional prerequisite tests may have
       been run."""

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

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

import cPickle
import cStringIO
import os
import qm
import qm.attachment
import qm.graph
import qm.label
import qm.platform
import qm.structured_text
from   qm.test.context import *
from   qm.test.result import *
import qm.xmlutil
import string
import sys
import tempfile
import types

########################################################################
# constants
########################################################################

dtds = {
    "tdb-configuration":
                    "-//Software Carpentry//QMTest TDB Configuration V0.1//EN",
    "resource":     "-//Software Carpentry//QMTest Resource V0.1//EN",
    "result":       "-//Software Carpentry//QMTest Result V0.3//EN",
    "suite":        "-//Software Carpentry//QMTest Suite V0.1//EN",
    "target":       "-//Software Carpentry//QMTest Target V0.1//EN",
    "test":         "-//Software Carpentry//QMTest Test V0.1//EN",
    }
"""A mapping for DTDs used by QMTest.

Keys are DTD types ("resource", "result", etc).  Values are the
corresponding DTD public identifiers."""

########################################################################
# functions
########################################################################

def validate_id(item_id):
    """Validate a test or resource ID.

    raises -- 'RuntimeError' if 'item_id' is not a valid ID."""

    if not qm.label.is_valid(item_id, allow_separator=1):
        raise RuntimeError, qm.error("invalid id", id=item_id)


def get_db_configuration_directory(db_path):
    """Return the path to the test database's configuration directory."""
    
    return os.path.join(db_path, "QMTest")


def _get_db_configuration_path(db_path):
    """Return the path to a test database's configuration file.

    'db_path' -- The path to the test database."""

    return os.path.join(get_db_configuration_directory(db_path),
                        "configuration")


def is_database(db_path):
    """Returns true if 'db_path' looks like a test database."""

    # A test database is a directory.
    if not os.path.isdir(db_path):
        return 0
    # A test database contains a configuration subdirectory.
    if not os.path.isdir(get_db_configuration_directory(db_path)):
        return 0
    # It probably is OK.
    return 1


def load_database(db_path):
    """Load the database from 'db_path'.

    returns -- The new 'Database'."""

    # Make sure it is a directory.
    if not is_database(db_path):
        raise ValueError, \
              qm.error("not test database", path=db_path)

    # Figure out which class implements the database.  Start by looking
    # for a file called 'configuration' in the directory corresponding
    # to the database.
    config_path = _get_db_configuration_path(db_path)
    if os.path.isfile(config_path):
        # Load the configuration file.
        document = qm.xmlutil.load_xml_file(config_path)
        # Get the root node in the document.
        database = document.documentElement
        # Load the database class name.
        database_class_name = qm.xmlutil.get_child_text(database,
                                                        "class-name")
        # Get the database class.
        database_class = get_extension_class(database_class_name,
                                             "database", None)
    else:
        # If 'configuration' did not exist, fall back to the 'xmldb'
        # database.
        import xmldb
        database_class = xmldb.Database
    
    # Create the database.
    return database_class(db_path)


def create_database(db_path, class_name):
    """Create a new test database.

    'db_path' -- The path to the test database.

    'class_name' -- The class name of the test database implementation."""

    # Make sure the path doesn't already exist.
    if os.path.exists(db_path):
        raise RuntimeError, qm.error("db path exists", path=db_path)
    # Create an empty directory.
    os.mkdir(db_path)
    # Create the configuration directory.
    os.mkdir(get_db_configuration_directory(db_path))

    # Now create an XML document for the configuration file.
    document = qm.xmlutil.create_dom_document(
        public_id=dtds["tdb-configuration"],
        dtd_file_name="tdb_configuration.dtd",
        document_element_tag="tdb-configuration"
        )
    # Create an element containign the class name.
    class_element = qm.xmlutil.create_dom_text_element(
        document, "class-name", class_name)
    document.documentElement.appendChild(class_element)
    # Write it.
    configuration_path = _get_db_configuration_path(db_path)
    qm.xmlutil.write_dom_document(document, open(configuration_path, "w"))


def get_extension_directories(kind, database):
    """Return the directories to search for QMTest extensions.

    'kind' -- A string giving kind of extension for which we are looking.
    This must be of the elements of 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.
    
    returns -- A sequence of strings.  Each string is the path to a
    directory that should be searched for QMTest extensions.  The
    directories must be searched in order; the first directory
    containing the desired module is the one from which the module is
    loaded.

    The directories that are returned are, in order:

    1. Those directories present in the 'QMTEST_CLASS_PATH' environment
       variable.

    2. Those directories specified by the 'GetClassPaths' method on the
       test database -- unless 'kind' is 'database'.

    3. The directories containing classes that come with QMTest.

    By placing the 'QMTEST_CLASS_PATH' directories first, users can
    override test classes with standard names."""

    global extension_kinds

    # The kind should be one of the extension_kinds.
    assert kind in extension_kinds
    if kind != 'database':
        assert database
    else:
        assert database is None
        
    # Start with the directories that the user has specified in the
    # QNTEST_CLASSPATH environment variable.
    if os.environ.has_key('QMTEST_CLASS_PATH'):
        dirs = string.split(os.environ['QMTEST_CLASS_PATH'], ':')
    else:
        dirs = []

    # Search directories specified by the database -- unless we are
    # searching for a database class, in which case we cannot assume
    # that a database has already been loaded.
    if kind != 'database':
        dirs = dirs + database.GetClassPaths()

    # Search the builtin directory, too.
    dirs.append(qm.common.get_lib_directory("qm", "test", "classes"))

    return dirs


def get_extension_class_names_in_directory(directory):
    """Return the names of QMTest extension classes in 'directory'.

    'directory' -- A string giving the path to a directory in the file
    system.

    returns -- A dictionary mapping the strings in 'extension_kinds' to
    sequences of strings.  Each element in the sequence names an
    extension class, using the form 'module.class'"""

    global extension_kinds
    
    # Assume that there are no extension classes in this directory.
    extensions = {}
    for kind in extension_kinds:
        extensions[kind] = []
        
    # Look for a file named 'classes.qmc' in this directory.
    file = os.path.join(directory, 'classes.qmc')
    # If the file does not exist, there are no extension classes in
    # this directory.
    if not os.path.isfile(file):
        return extensions

    try:
        # Load the file.
        document = qm.xmlutil.load_xml_file(file)
        # Get the root node in the document.
        root = document.documentElement
        # Get the sequence of elements corresponding to each of the
        # classes listed in the directory.
        classes = qm.xmlutil.get_children(root, 'class')
        # Go through each of the classes to see what kind it is.
        for c in classes:
            kind = c.getAttribute('kind')
            # Skip extensions we do not understand.  Perhaps they
            # are for some other QM tool.
            if kind not in extension_kinds:
                continue
            extensions[kind].append(qm.xmlutil.get_dom_text(c))
    except:
        print sys.exc_info()[1]
        pass

    return extensions


def get_extension_class_names(kind, database):
    """Return the names of extension classes.

    'kind' -- The kind of extension class.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    returns -- A sequence of strings giving the names of the extension
    classes with the indicated 'kind', in the form 'module.class'."""

    dirs = get_extension_directories(kind, database)
    names = []
    for d in dirs:
        names.extend(get_extension_class_names_in_directory(d)[kind])
    return names


def get_extension_class(class_name, kind, database):
    """Return the extension class named 'class_name'.

    'class_name' -- The name of the class, in the form 'module.class'.

    'kind' -- The kind of class to load.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    returns -- The class object with the indicated 'class_name'."""

    global __class_caches
    
    # If this class is already in the cache, we can just return it.
    cache = __class_caches[kind]
    if cache.has_key(class_name):
        return cache[class_name]

    # Otherwise, load it now.  Get all the extension directories in
    # which this class might be located.
    klass = qm.common.load_class(class_name,
                                 get_extension_directories(kind,
                                                           database))
    # Cache it.
    cache[class_name] = klass

    return klass


def get_test_class(class_name, database):
    """Return the test class named 'class_name'.

    'class_name' -- The name of the test class, in the form
    'module.class'.

    returns -- The test class object with the indicated 'class_name'."""
    
    return get_extension_class(class_name, 'test', database)


def get_resource_class(class_name, database):
    """Return the resource class named 'class_name'.

    'class_name' -- The name of the resource class, in the form
    'module.class'.

    returns -- The resource class object with the indicated
    'class_name'."""
    
    return get_extension_class(class_name, 'resource', database)


def get_class_arguments(klass):
    """Return the arguments specified by the extension class 'klass'.

    returns -- A list of 'Field' objects containing all the
    arguments in the class hierarchy."""

    arguments = []

    # Start with the most derived class.
    classes = [klass]
    while classes:
        # Pull the first class off the list.
        c = classes.pop(0)
        # Add all of the new base classes to the end of the list.
	# The __bases__ attribute is a tuple, not a list, so we
	# must convert it to a list before using "extend".  By
	# Python 2.1, this restriction	was removed, but in order
	# to support Python 1.5.2 we must obey the old constraints.
        classes.extend(map(lambda x: x,  c.__bases__))
        # Add the arguments from this class.
        if c.__dict__.has_key("arguments"):
            arguments.extend(c.__dict__["arguments"])

    return arguments


def get_class_description(klass, brief=0):
    """Return a brief description of the extension class 'klass'.

    'brief' -- If true, return a brief (one-line) description of the
    extension class.
    
    returns -- A structured text description of 'klass'."""

    # Extract the class's doc string.
    doc_string = klass.__doc__
    if doc_string is not None:
        if brief:
            doc_string = qm.structured_text.get_first(doc_string)
        return doc_string
    else:
        return "&nbsp;"
    
    
def load_outcomes(file):
    """Load test outcomes from a file.

    'file' -- The file object from which to read the results.

    returns -- A map from test IDs to outcomes."""

    # Load full results.
    test_results = filter(lambda r: r.GetKind() == Result.TEST,
                          load_results(file))
    # Keep test outcomes only.
    outcomes = {}
    for r in test_results:
        outcomes[r.GetId()] = r.GetOutcome()
    return outcomes


def load_results(file):
    """Read test results from a file.

    'file' -- The file object from which to read the results.

    returns -- A sequence of 'Result' objects."""

    results = []
    
    results_document = qm.xmlutil.load_xml(file)
    node = results_document.documentElement
    # Extract the results.
    results_elements = qm.xmlutil.get_children(node, "result")
    for re in results_elements:
        results.append(_result_from_dom(re))

    return results


def _result_from_dom(node):
    """Extract a result from a DOM node.

    'node' -- A DOM node corresponding to a "result" element.

    returns -- A 'Result' object.  The context for the result is 'None',
    since context is not represented in a result DOM node."""

    assert node.tagName == "result"
    # Extract the outcome.
    outcome = qm.xmlutil.get_child_text(node, "outcome")
    # Extract the test ID.
    test_id = node.getAttribute("id")
    kind = node.getAttribute("kind")
    # The context is not represented in the DOM node.
    context = None
    # Build a Result.
    result = Result(kind, test_id, context, outcome)
    # Extract properties, one for each property element.
    for property_node in node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value

    return result


def count_outcomes(results):
    """Count results by outcome.

    'results' -- A sequence of 'Result' objects.

    returns -- A map from outcomes to counts of results with that
    outcome.""" 

    counts = {}
    for outcome in Result.outcomes:
        counts[outcome] = 0
    for result in results:
        outcome = result.GetOutcome()
        counts[outcome] = counts[outcome] + 1
    return counts


def split_results_by_expected_outcome(results, expected_outcomes):
    """Partition a sequence of results by expected outcomes.

    'results' -- A sequence of 'Result' objects.

    'expected_outcomes' -- A map from ID to corresponding expected
    outcome.

    returns -- A pair of lists.  The first contains results that
    produced the expected outcome.  The second contains results that
    didn't."""

    expected = []
    unexpected = []
    for result in results:
        expected_outcome = expected_outcomes.get(result.GetId(), Result.PASS)
        if result.GetOutcome() == expected_outcome:
            expected.append(result)
        else:
            unexpected.append(result)
    return expected, unexpected


########################################################################
# variables
########################################################################

extension_kinds = [ 'database',
                    'resource',
                    'target',
                    'test', ]
"""Names of different kinds of QMTest extension classes."""

__class_caches = {}
"""A dictionary of loaded class caches.

The keys are the kinds in 'extension_kinds'.  The associated value
is itself a dictionary mapping class names to class objects."""

# Initialize the caches.
for kind in extension_kinds:
    __class_caches[kind] = {}

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   base.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   Base interfaces and classes.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
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
from   qm.common import *
import qm.graph
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
    "class-directory":
                    "-//Software Carpentry//QMTest Class Directory V0.1//EN",
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

    'db_path' -- The path to the directory containing the database.
    
    returns -- The new 'Database'."""

    # Make sure it is a directory.
    if not is_database(db_path):
        raise QMException, \
              qm.error("not test database", path=db_path)

    # There are no database attributes yet.
    attributes = {}

    # Figure out which class implements the database.  Start by looking
    # for a file called 'configuration' in the directory corresponding
    # to the database.
    config_path = _get_db_configuration_path(db_path)
    # Load the configuration file.
    document = qm.xmlutil.load_xml_file(config_path)
    # Get the root node in the document.
    database = document.documentElement
    # Load the database class name.
    database_class_name = qm.xmlutil.get_child_text(database,
                                                    "class-name")
    # For backwards compatibility with QM 1.1.x, we accept
    # "xmldb.Database" and "qm.test.xmldb.Database", even though those
    # to do not name actual database classes any more.
    if database_class_name in ("xmldb.Database", "qm.test.xmldb.Database"):
        database_class_name = "xml_database.XMLDatabase"
    # Get the database class.
    database_class = get_extension_class(database_class_name,
                                         "database", None, db_path)
    # Get attributes to pass to the constructor.
    for node in qm.xmlutil.get_children(database, "attribute"):
        name = node.getAttribute("name")
        value = qm.xmlutil.get_dom_text(node)
        # Python does not allow keyword arguments to have Unicode
        # values.  Therefore, convert name to an ordinary string.
        name = str(name)
        # Keep track of the new attribute.
        attributes[str(name)] = value
    
    # Create the database.
    return database_class(db_path, attributes)


def create_database(db_path, class_name, attributes={}):
    """Create a new test database.

    'db_path' -- The path to the test database.

    'class_name' -- The class name of the test database implementation.

    'attributes' -- A dictionary mapping attribute names to values.
    These attributes will be applied to the database when it is
    used."""

    # Create the directory if it does not already exists.
    if not os.path.isdir(db_path):
        os.mkdir(db_path)
    # Create the configuration directory.
    config_dir = get_db_configuration_directory(db_path)
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

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
    # Create elements for the attributes.
    for name, value in attributes.items():
        element = qm.xmlutil.create_dom_text_element(document,
                                                     "attribute",
                                                     value)
        element.setAttribute("name", name)
        document.documentElement.appendChild(element)
    # Write it.
    configuration_path = _get_db_configuration_path(db_path)
    qm.xmlutil.write_dom_document(document, open(configuration_path, "w"))


def get_extension_directories(kind, database, database_path = None):
    """Return the directories to search for QMTest extensions.

    'kind' -- A string giving kind of extension for which we are looking.
    This must be of the elements of 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None'.

    'database_path' -- The path from which the database will be loaded.
    If 'None', 'database.GetPath()' is used.
    
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
        
    # Start with the directories that the user has specified in the
    # QNTEST_CLASSPATH environment variable.
    if os.environ.has_key('QMTEST_CLASS_PATH'):
        dirs = string.split(os.environ['QMTEST_CLASS_PATH'], ':')
    else:
        dirs = []

    # Search directories specified by the database.
    if database:
        dirs = dirs + database.GetClassPaths()
        
    # Search the database configuration directory.
    if database:
        dirs.append(get_db_configuration_directory(database.GetPath()))
    elif database_path:
        dirs.append(get_db_configuration_directory(database_path))
        
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
        pass

    return extensions


def get_extension_class_names(kind, database, database_path = None):
    """Return the names of extension classes.

    'kind' -- The kind of extension class.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    'database_path' -- The path from which the database will be loaded.
    If 'None', 'database.GetPath()' is used.

    returns -- A sequence of strings giving the names of the extension
    classes with the indicated 'kind', in the form 'module.class'."""

    dirs = get_extension_directories(kind, database, database_path)
    names = []
    for d in dirs:
        names.extend(get_extension_class_names_in_directory(d)[kind])
    return names


def get_extension_class_from_directory(class_name, kind, directory, path):
    """Load an extension class from 'directory'.

    'class_name' -- The name of the extension class, in the form
    'module.class'.

    'kind' -- The kind of class to load.  This value must be one
    of the 'extension_kinds'.

    'directory' -- The directory from which to load the class.

    'path' -- The directories to search for modules imported by the new
    module.

    returns -- The class loaded."""
    
    global __class_caches
    global __extension_bases
    
    # If this class is already in the cache, we can just return it.
    cache = __class_caches[kind]
    if cache.has_key(class_name):
        return cache[class_name]

    # Load the class.
    try:
        klass = qm.common.load_class(class_name, [directory],
                                     path + sys.path)
    except:
        raise PythonException, \
              (qm.error("extension class not found",
                        klass=class_name),
               sys.exc_info()[0],
               sys.exc_info()[1]), \
               sys.exc_info()[2]

    # Make sure the class is derived from the appropriate base class.
    if not issubclass(klass, __extension_bases[kind]):
        raise QMException, \
              qm.error("extension class not subclass",
                       kind = kind,
                       class_name = class_name,
                       base_name = __extension_bases[kind].__name__)
                      
    # Cache it.
    cache[class_name] = klass

    return klass

                                     
def get_extension_class(class_name, kind, database, database_path = None):
    """Return the extension class named 'class_name'.

    'class_name' -- The name of the class, in the form 'module.class'.

    'kind' -- The kind of class to load.  This value must be one
    of the 'extension_kinds'.

    'database' -- The 'Database' with which the extension class will be
    used, or 'None' if 'kind' is 'database'.

    'database_path' -- The path from which the database will be loaded.
    If 'None', 'database.GetPath()' is used.

    returns -- The class object with the indicated 'class_name'."""

    global __class_caches
    
    # If this class is already in the cache, we can just return it.
    cache = __class_caches[kind]
    if cache.has_key(class_name):
        return cache[class_name]

    # Look for the class in each of the extension directories.
    directories = get_extension_directories(kind, database, database_path)
    directory = None
    for d in directories:
        if class_name in get_extension_class_names_in_directory(d)[kind]:
            directory = d
            break

    # If the class could not be found, issue an error.
    if not directory:
        raise QMException, qm.error("extension class not found",
                                    klass=class_name)

    # Load the class.
    return get_extension_class_from_directory(class_name, kind,
                                              directory, directories)


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
                    'label',
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

import qm.test.database
import qm.label
import qm.test.resource
import qm.test.target
import qm.test.test

__extension_bases = {
    'database' : qm.test.database.Database,
    'label' : qm.label.Label,
    'resource' : qm.test.resource.Resource,
    'target' : qm.test.target.Target,
    'test' : qm.test.test.Test
    }
"""A map from extension class kinds to base classes.

An extension class of a particular 'kind' must be derived from
'extension_bases[kind]'."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

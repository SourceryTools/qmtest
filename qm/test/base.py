########################################################################
#
# File:   base.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   Base interfaces and classes.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
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
from   qm.test.file_result_reader import FileResultReader
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
# Exceptions
########################################################################

class CouldNotLoadExtensionError(QMException):
    """An exception indicating that an extension class could not be loaded."""

    def __init__(self, class_name, exc_info):
        """Construct a new 'CouldNotLoadExtensionError'.

        'class_name' -- The name of the class.

        'exc_info' -- An exception tuple, as returned by 'sys.exc_info'."""
        
        self.exc_info = exc_info
        message = qm.common.format_exception(exc_info)
        message += "\n" + qm.error("could not load extension class",
                                   class_name = class_name)
        QMException.__init__(self, message)
            
########################################################################
# Functions
########################################################################

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

    3. The directory specified by config.extension_path.

    4. The directories containing classes that come with QMTest.

    By placing the 'QMTEST_CLASS_PATH' directories first, users can
    override test classes with standard names."""

    global extension_kinds

    # The kind should be one of the extension_kinds.
    assert kind in extension_kinds
        
    # Start with the directories that the user has specified in the
    # QMTEST_CLASS_PATH environment variable.
    if os.environ.has_key('QMTEST_CLASS_PATH'):
        dirs = string.split(os.environ['QMTEST_CLASS_PATH'],
                            os.pathsep)
    else:
        dirs = []

    # Search directories specified by the database.
    if database:
        dirs = dirs + database.GetClassPaths()
        
    # Search the database configuration directory.
    if database:
        dirs.append(database.GetConfigurationDirectory())
    elif database_path:
        dirs.append(qm.test.database.get_configuration_directory
                    (database_path))

    # Search qmtest's own site-extensions directory.
    dirs.append(os.path.join(qm.prefix, qm.extension_path))

    dirs.append(qm.common.get_lib_directory('test', 'classes'))

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
        classes = root.getElementsByTagName("class")
        # Go through each of the classes to see what kind it is.
        for c in classes:
            kind = c.getAttribute('kind')
            # Skip extensions we do not understand.  Perhaps they
            # are for some other QM tool.
            if kind not in extension_kinds:
                continue
            if c.hasAttribute("name"):
                name = c.getAttribute("name")
            else:
                # Before QMTest 2.1, the class name was contained in
                # the class element, rather than being an attribute.
                name = qm.xmlutil.get_dom_text(c)
            # Strip whitespace.
            name = name.strip()
            extensions[kind].append(name)
    except:
        raise

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
        raise CouldNotLoadExtensionError(class_name, sys.exc_info())

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

    # For backwards compatibility with QM 1.1.x, we accept
    # "xmldb.Database" and "qm.test.xmldb.Database", even though those
    # to do not name actual database classes any more.
    if kind == "database" and class_name in ("xmldb.Database",
                                             "qm.test.xmldb.Database"):
        class_name = "xml_database.XMLDatabase"
        
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


def get_extension_classes(kind, database = None):
    """Return the extension classes for the given 'kind'.

    'kind' -- The kind of extensions being sought.  The value must be
    one of the 'extension_kinds'.

    'database' -- If not 'None', the test 'Database' in use.

    returns -- A list of the available extension classes of the
    indicated 'kind'."""

    classes = []
    directories = get_extension_directories(kind, database)
    for d in directories:
        names = get_extension_class_names_in_directory(d)[kind]
        d_classes = [get_extension_class_from_directory(n, kind, d,
                                                        directories)
                     for n in names]
        classes.extend(d_classes)

    return classes
    
    
def load_results(file, database):
    """Read test results from a file.

    'file' -- The filename or file object from which to read the
    results.  If 'file' is not a string, then it is must be a seekable
    file object, and this function will look for a 'FileResultReader'
    that accepts the file.  If 'file' is a string, then it is treated as
    either a filename or as an extension descriptor.

    'database' -- The current database.

    returns -- A 'ResultReader' object, or raises an exception if no
    appropriate reader is available."""

    f = None
    if isinstance(file, types.StringTypes):
        if os.path.exists(file):
            f = open(file, "rb")
    else:
        f = file
    if f:
        # Find the first FileResultStream that will accept this file.
        for c in get_extension_classes("result_reader", database):
            if issubclass(c, FileResultReader):
                try:
                    return c({"file" : f})
                except FileResultReader.InvalidFile:
                    # Go back to the beginning of the file.
                    f.seek(0)
    if not isinstance(file, types.StringTypes):
        raise FileResultReader.InvalidFile, \
              "not a valid results file"
    if database:
        extension_loader = database.GetExtension
    else:
        extension_loader = None
    class_loader = lambda n: get_extension_class(n,
                                                 "result_reader",
                                                 database)
    cl, args = qm.extension.parse_descriptor(file,
                                             class_loader,
                                             extension_loader)
    return cl(args)
        

def load_outcomes(file, database):
    """Load test outcomes from a file.

    'file' -- The file object from which to read the results.  See
    'load_results' for details.

    'database' -- The current database.

    returns -- A map from test IDs to outcomes."""

    results = load_results(file, database)
    outcomes = {}
    for r in results:
        # Keep test outcomes only.
        if r.GetKind() == Result.TEST:
            outcomes[r.GetId()] = r.GetOutcome()
    return outcomes


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
    # Build a Result.
    result = Result(kind, test_id, outcome)
    # Extract properties, one for each property element.
    for property_node in node.getElementsByTagName("property"):
        # The name is stored in an attribute.
        name = property_node.getAttribute("name")
        # The value is stored in the child text node.
        value = qm.xmlutil.get_dom_text(property_node)
        # Store it.
        result[name] = value

    return result


########################################################################
# variables
########################################################################

import qm.test.database
import qm.label
import qm.host
import qm.test.resource
import qm.test.result_reader
import qm.test.result_stream
import qm.test.run_database
import qm.test.suite
import qm.test.target
import qm.test.test

__extension_bases = {
    'database' : qm.test.database.Database,
    'host' : qm.host.Host,
    'label' : qm.label.Label,
    'resource' : qm.test.resource.Resource,
    'result_reader' : qm.test.result_reader.ResultReader,
    'result_stream' : qm.test.result_stream.ResultStream,
    'run_database' : qm.test.run_database.RunDatabase,
    'suite' : qm.test.suite.Suite,
    'target' : qm.test.target.Target,
    'test' : qm.test.test.Test
    }
"""A map from extension class kinds to base classes.

An extension class of a particular 'kind' must be derived from
'extension_bases[kind]'."""

extension_kinds = __extension_bases.keys()
"""Names of different kinds of QMTest extension classes."""
extension_kinds.sort()

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

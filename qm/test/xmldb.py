########################################################################
#
# File:   xmldb.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   XML-based test database implementation.
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

import base
import os
import qm.fields
import qm.label
import string
import xml.dom.ext.reader.Sax

########################################################################
# constants
########################################################################

test_file_extension = ".qmt"
"""The file extension for XML files containing tests."""

suite_file_extension = ".qms"
"""The file extension for files representing test suites."""

########################################################################
# classes
########################################################################

class UnkownTestClassError(Exception):
    """An unknown test class was specified."""
    
    pass



class TestFileError(Exception):
    """An error in the format or contents of an XML test file."""

    pass



class Database(base.Database):
    """A database represnting tests as XML files in a directory tree."""

    # When processing the DOM tree for an XML test file, we may
    # encounter two kinds of errors.  One indicates an invalid DOM tree,
    # i.e. the structure is at variance with the test DTD.  We can use
    # 'assert' to flag these, since we expect that the validating parser
    # should have caught those.  Other errors are semantic, for instance
    # specifying an argument which doesn't exist in the test class.  For
    # these, we raise an 'TestFileError'.

    def __init__(self, path, create=0):
        """Open a connection to a database.

        'path' -- The path to the database.

        'create' -- If true, the database is created.  Otherwise, it
        must already exist."""

        # Create a new database, if requested.
        if create:
            if os.path.exists(path):
                raise ValueError, \
                      qm.error("db path exists", path=path)
            os.mkdir(path)
        # Make sure the database path exists.
        if not os.path.isdir(path):
            raise ValueError, \
                  qm.error("db path doesn't exist", path=path)
        # Remember the path.
        self.__path = path


    def GetPath(self):
        """Return the path to the database."""

        return self.__path


    def HasTest(self, test_id):
        """Return true if the database contains a test with 'test_id'."""

        # Turn the period-separated test ID into a file system path,
        # relative to the top of the test database.
        path = self.IdToPath(test_id, absolute=1) + test_file_extension
        # Does the test file exist?
        return os.path.isfile(path)


    def GetTest(self, test_id):
        # Turn the period-separated test ID into a file system path,
        # relative to the top of the test database.
        path = self.IdToPath(test_id, absolute=1) + test_file_extension
        # Does the test file exist?
        if not os.path.isfile(path):
            raise base.NoSuchTestError, test_id
        # Open it.
        try:
            file = open(path, "r")
        except:
            # FIXME.  Any errors that need to be handled here?
            raise
        # Create a validating DOM reader.
        reader = xml.dom.ext.reader.Sax.Reader(validate=1)
        try:
            # Read and parse XML.
            test_document = reader.fromStream(file)
        except:
            # FIXME.  How should we handle parse errors?
            raise
        file.close()
        # Turn it into a test object.
        return self.__ParseTestDocument(test_id, test_document)
        

    def HasSuite(self, suite_id):
        """Return true if the database contains a suite with 'suite_id'."""

        id_path = self.IdToPath(suite_id, absolute=0)
        path = self.IdToPath(suite_id, absolute=1)
        # Is there a directory corresponding to the ID?
        if os.path.isdir(path):
            return 1
        # Is there an explicit suite file corresponding to the ID?
        id_path = id_path + suite_file_extension
        path = path + suite_file_extension
        if os.path.isfile(path):
            # Yes.
            return 1
        # No suite found.
        return 0


    def GetSuite(self, suite_id):
        path = self.IdToPath(suite_id, absolute=1)
        # Is there a directory corresponding to the ID?
        if os.path.isdir(path):
            # Yes.  Return the virtual suite corresponding to that
            # directory. 
            return DirectorySuite(suite_id, self)
        # Is there an explicit suite file corresponding to the ID?
        path = path + suite_file_extension
        if os.path.isfile(path):
            # Yes.  Build a suite from that file.
            return FileSuite(suite_id, self)
        # Otherwise, we can't find the suite.
        raise base.NoSuchSuiteError, "no test suite with ID %s" % suite_id
        

    def IdToPath(self, id_, absolute=0):
        """Convert an ID in the database to a path.

        'absolute' -- If true, include the path to the test database
        itself.  Otherwise, the path is relative to the top of the test
        database."""

        path = qm.label.to_path(id_)
        if absolute:
            path = os.path.join(self.__path, path)
        return path


    # Helper functions.

    def __ParseTestDocument(self, test_id, document):
        """Return a test object constructed from a test document.

        'test_id' -- The test ID of the test.

        'document' -- A DOM document containing a single test element
        from which the test is constructed."""
        
        # Make sure the document contains only a single test element.
        test_nodes = document.getElementsByTagName("test")
        assert len(test_nodes) == 1
        test_node = test_nodes[0]
        # Extract the pieces.
        test_class = self.__GetClass(test_node)
        arguments = self.__GetArguments(test_node, test_class)
        categories = qm.common.get_dom_children_texts(test_node, "categories")
        prerequisites = self.__GetPrerequisites(test_node, test_id)
        # Construct the test object.
        test = apply(test_class, [ test_id ], arguments)
        for category in categories:
            test.AddCategory(category)
        return test
        

    def __GetClass(self, test_node):
        """Return the test class of a test.

        'test_node' -- A DOM node for a test element.

        raises -- 'UnknownTestClassError' if the test class specified
        for the test is not among the registered test classes."""

        # Make sure it has a unique class element child.
        class_nodes = test_node.getElementsByTagName("class")
        assert len(class_nodes) == 1
        class_node = class_nodes[0]
        # Extract the name of the test class.
        class_name = qm.common.get_dom_node_text(class_node)
        # Obtain the test class.
        try:
            return base.get_test_class(class_name)
        except KeyError:
            raise UnknownTestClassError, class_name


    def __GetArguments(self, test_node, test_class):
        """Return the arguments of a test.

        'test_node' -- A DOM node for a test element.

        'test_class' -- The test class for this test.

        returns -- A mapping from argument names to corresponding
        values."""

        result = {}
        # The fields in the test class.
        fields = test_class.fields

        # Loop over argument child elements.
        for arg_node in test_node.getElementsByTagName("argument"):
            # Extract the (required) name attribute.  
            name = arg_node.getAttribute("name")
            try:
                # Is there a corresponding field?
                field = fields[name]
            except KeyError:
                # Nope; that's an error.
                raise TestFileError, \
                      qm.error("xml invalid arg name", name=name)
            # The argument element should have exactly one child, the
            # argument value. 
            assert len(arg_node.childNodes) == 1
            value_node = arg_node.childNodes[0]
            # The field knows how to extract its value from the value
            # node. 
            value = field.GetValueFromDomNode(value_node)
            # Make sure the value is OK.
            value = field.Validate(value)
            # Store it.
            result[field.GetName()] = value
        # All done.
        return result


    def __GetPrerequisites(self, test_node, test_id):
        """Return IDs of prerequisite tests.

        'test_node' -- A DOM node for a test element.

        'test_id' -- The corresponding test ID."""
        
        # Extract the contents of all prerequisite elements.
        results = qm.common.get_dom_children_texts(test_node, "prerequisite")
        # These test IDs are relative to the path containing this test.
        # Make them absolute.
        return map(qm.label.MakeRelativeTo(label=test_id), results)



class FileSuite(base.Suite):
    """A test suite whose elements are listed in a file.

    The test suite file lists one test ID on each line.  These IDs are
    relative to directory containing the test suite.  For example, if
    the test suite file corresponding to ID 'my.suite' lists 'foo' and
    'bar.baz', the actual test IDs relative to the top of the test
    database are 'my.foo' and 'my.bar.baz'."""

    def __init__(self, suite_id, database):
        """Create a new test suite instance.

        'suite_id' -- The test suite ID.

        'database' -- The test database."""

        base.Suite.__init__(self, suite_id)
        self.__ids = []

        path = os.path.join(database.GetPath(),
                            database.IdToPath(suite_id)) \
               + suite_file_extension
        # Make sure there is a file by that name.
        if not os.path.isfile(path):
            raise base.NoSuchSuiteError, "no suite file %s" % path
        # Read the contents of the suite file.
        suite_file = open(path, "r")
        contents = suite_file.read()
        suite_file.close()
        # Divide it into test IDs.
        content_ids = string.split(contents)
        # Clean them up.
        content_ids = map(string.strip, content_ids)
        # Make sure they're all valid.
        for id in content_ids:
            if not qm.label.is_valid(id, allow_separator=1):
                raise RuntimeError, \
                      qm.error("invalid test id", id=id)

        # The content IDs are relative to the location of the suite.
        # Construct absolute IDs.
        content_ids = map(qm.label.MakeRelativeTo(label=suite_id),
                          content_ids)
        
        # Validate the IDs, and expand any suite IDs that may be among
        # them. 
        try:
            base.expand_and_validate_ids(database,
                                         content_ids,
                                         self.__ids)
        except ValueError, invalid_id:
            raise KeyError, qm.error("invalid id in suite",
                                     id=invalid_id,
                                     suite=suite_id)

           
    def GetTestIds(self):
        return self.__ids



class DirectorySuite(base.Suite):
    """A test suite corresponding to directory in the database.

    Each directory in the test database is considered a virtual suite.
    This suite contains all of the tests in the directory or its
    subdirectories."""

    def __init__(self, suite_id, database):
        """Create a new test suite instance.

        'suite_id' -- The test suite ID.

        'database' -- The database containing the suite.

        'dir_path' -- The path, relative to 'db_path', to the directory
        containing the tests.  All tests in and under this directory are
        included in the suite."""

        base.Suite.__init__(self, suite_id)

        # Make sure the path exists.
        path = os.path.join(database.GetPath(),
                            database.IdToPath(suite_id))
        if not os.path.isdir(path):
            raise base.NoSuchSuiteError, "no directory at %s" % path

        self.__ids = None
        self.__suite_id = suite_id
        self.__suite_path = path

        # Don't look up the test IDs yet.


    def GetTestIds(self):
        # The collection of contained test IDs is determined lazily, and
        # cached for future invokations.
        if self.__ids is None:
            # We need to determine the IDs of tests under our directory. 
            self.__ids = []
            self.__AddTestsInDirectory("")

        return self.__ids


    # Helper methods.

    def __AddTestsInDirectory(self, sub_path):
        """Scan the tests in directory 'path'.

        'sub_path' -- Path relative to top of suite directory from which
        to add tests.

        This method calls itself recursively for subdirectories."""

        sub_id = qm.label.from_path(sub_path)
        dir_id = qm.label.join(self.__suite_id, sub_id)
        rel = qm.label.MakeRelativeTo(path=dir_id)
        # Generate the full path to the directory being scanned.
        path = os.path.join(self.__suite_path, sub_path)
        # Loop over its contents.
        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            # Is it a directory?
            if os.path.isdir(entry_path):
                # Yes; scan recursively.
                self.__AddTestsInDirectory(os.path.join(sub_path, entry))
            else:
                # Look at its extension.
                name, extension = os.path.splitext(entry)
                if extension == test_file_extension:
                    test_id = rel(name)
                    self.__ids.append(test_id)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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
import dircache
import os
import qm.common
import qm.fields
import qm.label
import qm.structured_text
import qm.xmlutil
import string

########################################################################
# constants
########################################################################

test_file_extension = ".qmt"
"""The file extension for XML files containing tests."""

suite_file_extension = ".qms"
"""The file extension for files representing test suites."""

resource_file_extension = ".qma"
"""The file extension for files representing resources."""

########################################################################
# classes
########################################################################

class UnknownTestClassError(RuntimeError):
    """An unknown test class was specified."""
    
    pass



class UnknownResourceClassError(RuntimeError):
    """An unknown resource class was specified."""
    
    pass



class TestFileError(RuntimeError):
    """An error in the format or contents of an XML test file."""

    pass



class Database(base.Database, qm.common.MutexMixin):
    """A database represnting tests as XML files in a directory tree."""

    # This value, used in the test and suite caches, indicates that the
    # corresponding ID doesn't correspond to an existing test or suite.
    __DOES_NOT_EXIST = "does not exist"

    # This value, used in the test and suite caches, indicates that the
    # corresponding ID corresponds to an existing test or suite, but the
    # test or suite hasn't been loaded.
    __NOT_LOADED = "not loaded"

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
        # Cache results in these attributes.  The keys are test or suite
        # IDs, and the values are either the loaded test or suite
        # objects, or the special values '__DOES_NOT_EXIST' or
        # '__NOT_LOADED'. 
        self.__tests = {}
        self.__suites = {}
        self.__resources = {}


    def GetClassPaths(self):
        lock = self.GetLock()
        # Specify the '_classes' subdirectory, if it exists.
        class_dir = os.path.join(self.__path, "_classes")
        if os.path.isdir(class_dir):
            return [class_dir]
        else:
            return []


    def GetPath(self):
        """Return the path to the database."""

        return self.__path


    def HasTest(self, test_id):
        """Return true if the database contains a test with 'test_id'."""

        lock = self.GetLock()
        return self.__HasItem(test_id, self.__tests, test_file_extension)


    def GetTest(self, test_id):
        lock = self.GetLock()
        if not self.HasTest(test_id):
            raise base.NoSuchTestError, test_id

        try:
            return self.__GetItem(test_id,
                                  self.__tests,
                                  test_file_extension,
                                  self.__ParseTestDocument)
        except qm.fields.DomNodeError, message:
            message = qm.error("error loading xml test",
                               test_id=test_id,
                               message=message)
            raise TestFileError, message
        

    def WriteTest(self, test, comments=0):
        lock = self.GetLock()
        # Invalidate the cache entry.
        self.__InvalidateItem(test.GetId(), self.__tests)
        # Generate the document and document type for XML test files.
        document = qm.xmlutil.create_dom_document(
            public_id=base.dtds["test"],
            dtd_file_name="test.dtd",
            document_element_tag="test"
            )
        # Construct the test element node.
        test_id = test.GetId()
        self.__MakeDomNodeForTest(document, document.documentElement,
                                  test, comments)
        # Find the file system path for the test file.
        test_path = self.TestIdToPath(test_id, absolute=1)
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(test_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the test.
        test_file = open(test_path, "w")
        qm.xmlutil.write_dom_document(document, test_file)
        test_file.close()


    def RemoveTest(self, test_id):
        lock = self.GetLock()
        # Make sure there is such a test.
        assert self.HasTest(test_id)
        # Invalidate the cache entry.
        self.__InvalidateItem(test_id, self.__tests)
        # Remove the test file.
        test_path = self.TestIdToPath(test_id, absolute=1)
        os.unlink(test_path)


    def GetTestIds(self, path="."):
        lock = self.GetLock()
        dir_path = self.IdToPath(path, absolute=1)
        return scan_dir_for_labels(dir_path, test_file_extension)


    def HasResource(self, resource_id):
        """Return true if we contain a resource with 'resource_id'."""

        lock = self.GetLock()
        return self.__HasItem(resource_id, self.__resources,
                              resource_file_extension)


    def GetResource(self, resource_id):
        lock = self.GetLock()
        if not self.HasResource(resource_id):
            raise base.NoSuchResourceError, resource_id

        return self.__GetItem(resource_id, self.__resources,
                              resource_file_extension,
                              self.__ParseResourceDocument)
        

    def WriteResource(self, resource, comments=0):
        lock = self.GetLock()
        # Invalidate the cache entry.
        self.__InvalidateItem(resource.GetId(), self.__resources)
        # Generate the document and document type for XML resource files.
        document = qm.xmlutil.create_dom_document(
            public_id=base.dtds["resource"],
            dtd_file_name="resource.dtd",
            document_element_tag="resource"
            )
        # Construct the resource element node.
        resource_id = resource.GetId()
        self.__MakeDomNodeForResource(document, document.documentElement,
                                    resource, comments)
        # Find the file system path for the resource file.
        resource_path = self.IdToPath(resource_id, absolute=1) \
                      + resource_file_extension
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(resource_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the resource.
        resource_file = open(resource_path, "w")
        qm.xmlutil.write_dom_document(document, resource_file)
        resource_file.close()


    def RemoveResource(self, resource_id):
        lock = self.GetLock()
        # Make sure there is such a resource.
        assert self.HasResource(resource_id)
        # Invalidate the cache entry.
        self.__InvalidateItem(resource_id, self.__resources)
        # Remove the resource file.
        resource_path = self.IdToPath(resource_id, absolute=1) \
                      + resource_file_extension
        os.unlink(resource_path)


    def GetResourceIds(self, path="."):
        lock = self.GetLock()
        dir_path = self.IdToPath(path, absolute=1)
        return scan_dir_for_labels(dir_path, resource_file_extension)


    def HasSuite(self, suite_id):
        """Return true if the database contains a suite with 'suite_id'."""

        lock = self.GetLock()
        try:
            # Check the cache.  If there's an entry for this suite ID,
            # use the caches state.
            return self.__suites[suite_id] is not self.__DOES_NOT_EXIST
        except KeyError:
            # It's not in the cache, so check the file system.
            id_path = self.IdToPath(suite_id, absolute=0)
            path = self.IdToPath(suite_id, absolute=1)
            # Is there a directory corresponding to the ID?
            if os.path.isdir(path):
                # Yes.  Indicate in the cache that the suite exists.
                self.__suites[suite_id] = self.__NOT_LOADED
                return 1
            # Is there an explicit suite file corresponding to the ID?
            id_path = id_path + suite_file_extension
            path = path + suite_file_extension
            if os.path.isfile(path):
                # Yes.  Indicate in the cache that the suite exists.
                self.__suites[suite_id] = self.__NOT_LOADED
                return 1
            # No suite found.  Enter that into the cache.
            self.__suites[suite_id] = self.__DOES_NOT_EXIST
            return 0


    def GetSuite(self, suite_id):
        lock = self.GetLock()

        if not self.HasSuite(suite_id):
            raise base.NoSuchSuiteError, \
                  "no test suite with ID %s" % suite_id

        # Look in the cache.
        suite = self.__suites[suite_id]
        if suite == self.__NOT_LOADED:
            path = self.IdToPath(suite_id, absolute=1)
            # The suite exists, but is not loaded.  We'll have to load
            # it here.  Is there a directory corresponding to the ID?
            if os.path.isdir(path):
                # Return the virtual suite corresponding to that
                # directory.
                suite = DirectorySuite(suite_id, self)
            else:
                # Load a suite from a file.
                suite = self.__GetSuite(suite_id)
            # Enter the suite into the cache.
            self.__suites[suite_id] = suite
            return suite
        else:
            # Already loaded; return cached value.
            return suite


    def WriteSuite(self, suite):
        """Write 'suite' to the database as a suite file."""

        # Don't write directory suites to suite file.
        assert not isinstance(suite, DirectorySuite)

        lock = self.GetLock()
        # Invalidate the cache entry.
        self.__InvalidateItem(suite.GetId(), self.__suites)
        # Generate the document and document type for XML suite files.
        document = qm.xmlutil.create_dom_document(
            public_id=base.dtds["suite"],
            dtd_file_name="suite.dtd",
            document_element_tag="suite"
            )
        # Construct the suite element node by adding children for test
        # IDs and suite IDs.  Use the raw test and suite IDs, i.e. don't
        # expand suites to their contained tests. 
        suite_element = document.documentElement
        for test_id in suite.GetRawTestIds():
            test_id_element = qm.xmlutil.create_dom_text_element(
                document, "test_id", test_id)
            suite_element.appendChild(test_id_element)
        for suite_id in suite.GetRawSuiteIds():
            suite_id_element = qm.xmlutil.create_dom_text_element(
                document, "suite_id", suite_id)
            suite_element.appendChild(suite_id_element)
        # Find the file system path for the suite file.
        suite_path = self.IdToPath(suite.GetId(), absolute=1) \
                     + suite_file_extension
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(suite_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the suite.
        suite_file = open(suite_path, "w")
        qm.xmlutil.write_dom_document(document, suite_file)
        suite_file.close()


    def RemoveSuite(self, suite_id):
        lock = self.GetLock()
        # Make sure there is such a suite.
        assert self.HasSuite(suite_id)
        # Make sure it's not an implicit test suite.
        suite = self.GetSuite(suite_id)
        assert not suite.IsImplicit()
        # Invalidate the cache entry.
        self.__InvalidateItem(suite_id, self.__suites)
        # Remove the suite file.
        suite_path = self.IdToPath(suite_id, absolute=1) \
                     + suite_file_extension
        os.unlink(suite_path)


    def GetSuiteIds(self, path=".", implicit=0):
        lock = self.GetLock()
        # First find IDs corresponding to test suite files.
        dir_path = self.IdToPath(path, absolute=1)
        suites = scan_dir_for_labels(dir_path, suite_file_extension)
        # Were implicit suite IDs requested?
        if implicit:
            # Yes.  Scan for subdirectories.
            suites = suites + scan_dir_for_suite_dirs(dir_path)
        return suites


    def TestIdToPath(self, test_id, absolute=0):
        """Convert a test ID in the database to a path to the test file."""

        return self.IdToPath(test_id, absolute) + test_file_extension


    def IdToPath(self, id_, absolute=0):
        """Convert an ID in the database to a path.

        'absolute' -- If true, include the path to the test database
        itself.  Otherwise, the path is relative to the top of the test
        database."""

        path = qm.label.to_path(id_)
        if absolute:
            path = os.path.join(self.__path, path)
        return path


    def SetAttachmentData(self, attachment, data, item_id):
        lock = self.GetLock()
        # Construct the path to the directory in which the test or
        # resource given by 'item_id' is written.  The attachment should
        # be written to this directory.
        dir_path = self.IdToPath(qm.label.dirname(item_id), absolute=1)
        # Construct the file name to which the attachment data is
        # written.  Try to use the file name associated with the
        # attachment. 
        file_name = attachment.file_name
        path = os.path.join(dir_path, file_name)
        # If a file by that name already exists, generate a new file
        # name by appending subsequent integers until we have a file
        # name that doesn't already exist.
        count = 0
        while os.path.exists(path):
            file_name = "%s.%d" % (attachment.file_name, count)
            count = count + 1
            path = os.path.join(dir_path, file_name)
        # Open the attachment file, and set its permissions.
        attachment_file = open(path, "wb")
        os.chmod(path, 0600)
        # Write the attachment data.
        attachment_file.write(data)
        attachment_file.close()
        # Update the 'Attachment' object to the new location of the
        # attachment data. 
        attachment.location = file_name


    # Helper functions.

    def __InvalidateItem(self, item_id, cache):
        """Invalidate the cache entry for 'item_id'."""

        if cache.has_key(item_id):
            del cache[item_id]


    def __HasItem(self, item_id, cache, file_extension):
        """Return true if an item (a test or resource) exits.

        This function is used for logic common to tests and resources.

        'item_id' -- The ID of the item.

        'cache' -- A cache map in which to look up the item ID, and to
        update if the item is found.

        'file_extension' -- The file extension that is used for files
        representing this kind of item."""

        try:
            # Try looking it up in the cache.
            return cache[item_id] is not self.__DOES_NOT_EXIST
        except KeyError:
            # Not found in the cache, so check in the file system.  Turn
            # the period-separated test ID into a file system path,
            # relative to the top of the test database.
            path = self.IdToPath(item_id, absolute=1) + file_extension
            # Does the test file exist?
            if os.path.isfile(path):
                # Yes.  Enter into the cache that the test exists but is
                # not loaded.
                cache[item_id] = self.__NOT_LOADED
                return 1
            else:
                # No.  Enter into the cache that the test does not exist.
                cache[item_id] = self.__DOES_NOT_EXIST
                return 0


    def __GetItem(self, item_id, cache, file_extension, document_parser):
        """Return an item (a test or resource).

        This function is used for logic common to tests and resources.

        'item_id' -- The ID of the item to get.

        'cache' -- A cache map in which to look up the item ID, and if
        the item is loaded, into which to enter it.

        'file_extension' -- The file extension that is used for files
        representing this kind of item.  The file contents are XML.

        'document_parser' -- A function that takes an XML DOM document
        as its argument and returns the constructed item object."""

        # Look in the cache.
        item = cache[item_id]
        if item == self.__NOT_LOADED:
            # The item exists, but hasn't been loaded, so we'll have to
            # load it here.  Turn the period-separated ID into a file
            # system path, relative to the top of the item database.
            path = self.IdToPath(item_id, absolute=1) + file_extension
            # Load and parse the XML item representation.
            document = qm.xmlutil.load_xml_file(path)
            # Turn it into an object.
            item = document_parser(item_id, document)
            # Set its working directory.
            item.SetWorkingDirectory(os.path.dirname(path))
            # Enter it into the cache.
            cache[item_id] = item
            return item
        else:
            # Already loaded; return the cached value.
            return item


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
        test_class_name = self.__GetClassNameFromDomNode(test_node)
        # Obtain the test class.
        try:
            test_class = base.get_class(test_class_name)
        except ImportError:
            raise UnknownTestClassError, \
                  qm.error("unknown test class",
                           test_class_name=test_class_name,
                           test_id=test_id)
        arguments = self.__GetArgumentsFromDomNode(test_node, test_class)
        categories = qm.xmlutil.get_dom_children_texts(test_node,
                                                       "category")
        prerequisites = self.__GetPrerequisitesFromDomNode(test_node)
        resources = self.__GetResourcesFromDomNode(test_node)
        properties = self.__GetPropertiesFromDomNode(test_node)
        # Construct a test wrapper around it.
        test = base.Test(test_id,
                         test_class_name,
                         arguments,
                         prerequisites,
                         categories,
                         resources,
                         properties)
        return test
        

    def __ParseResourceDocument(self, resource_id, document):
        """Return a resource object constructed from a resource document.

        'resource_id' -- The resource ID of the resource.

        'document' -- A DOM document node containing a single resource
        element from which the resource object is constructed."""

        # Make sure the document contains only a single test element.
        resource_nodes = document.getElementsByTagName("resource")
        assert len(resource_nodes) == 1
        resource_node = resource_nodes[0]
        # Extract the pieces.
        resource_class_name = self.__GetClassNameFromDomNode(resource_node)
        # Obtain the test class.
        try:
            resource_class = base.get_class(resource_class_name)
        except KeyError:
            raise UnknownResourceClassError, class_name
        arguments = self.__GetArgumentsFromDomNode(resource_node,
                                                   resource_class)
        properties = self.__GetPropertiesFromDomNode(resource_node)
        # Construct a test wrapper around it.
        return base.Resource(resource_id, resource_class_name,
                             arguments, properties)


    def __GetClassNameFromDomNode(self, node):
        """Return the name of the test or resource class of a test.

        'node' -- A DOM node for a test element.

        raises -- 'UnknownTestClassError' if the test class specified
        for the test is not among the registered test classes."""

        # Make sure it has a unique class element child.
        class_nodes = node.getElementsByTagName("class")
        assert len(class_nodes) == 1
        class_node = class_nodes[0]
        # Extract the name of the test class.
        return qm.xmlutil.get_dom_text(class_node)


    def __GetArgumentsFromDomNode(self, node, klass):
        """Return the arguments of a test or resource.

        'node' -- A DOM node for a test or resource element.

        'klass' -- The test or resource class.

        returns -- A mapping from argument names to corresponding
        values."""

        result = {}
        # The fields in the test class.
        fields = klass.fields

        # Loop over argument child elements.
        for arg_node in node.getElementsByTagName("argument"):
            # Extract the (required) name attribute.  
            name = arg_node.getAttribute("name")
            # Look for a field with the same name.
            field = None
            for f in fields:
                if f.GetName() == name:
                    field = f
                    break
            # Did we find a field by this name?
            if field is None:
                # No.  That's an error.
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


    def __GetPrerequisitesFromDomNode(self, test_node):
        """Return the prerequisite tests for 'test_node'.

        'test_node' -- A DOM node for a test element.

        returns -- A mapping from prerequisite test ID to the outcome
        required for that test."""
        
        # Extract the contents of all prerequisite elements.
        results = {}
        for child_node in test_node.getElementsByTagName("prerequisite"):
            test_id = qm.xmlutil.get_dom_text(child_node)
            # Get the required outcome.
            outcome = child_node.getAttribute("outcome")
            results[test_id] = outcome
        return results


    def __GetResourcesFromDomNode(self, test_node):
        """Return the resources for 'test_node'.

        'test_node' -- A DOM node for a test element.

        returns -- A sequence of resource IDs."""
        
        # Extract the contents of all resource elements.
        results = []
        for child_node in test_node.getElementsByTagName("resource"):
            resource_id = qm.xmlutil.get_dom_text(child_node)
            results.append(resource_id)
        return results


    def __GetPropertiesFromDomNode(self, item_node):
        """Return the properties for an 'item_node'.

        'item_node' -- A DOM node for a test or resource element.

        returns -- A map from property names to values."""

        properties = {}
        for child_node in item_node.getElementsByTagName("property"):
            name = child_node.getAttribute("name")
            value = qm.xmlutil.get_dom_text(child_node)
            properties[name] = value
        return properties


    def __MakeDomNodeForTest(self, document, element, test, comments=0):
        """Construct a DOM node for a test.

        'document' -- The DOM document in which the node is being
        constructed.

        'element' -- A test element DOM node in which the test is
        assembled.  If 'None', a new test element node is created.

        'test' -- The test to write.

        'comments' -- If true, add DOM comment nodes."""

        test_id = test.GetId()

        # Make an element node unless one was specified.
        if element is None:
            element = document.createElement("test")
        else:
            assert element.tagName == "test"

        # Build common stuff.
        self.__MakeDomNodeForItem(document, element, test, comments)

        # Build and add category elements.
        for category in test.GetCategories():
            cat_element = qm.xmlutil.create_dom_text_element(
                document, "category", category)
            element.appendChild(cat_element)

        # Build and add prerequisite elements.  First find the ID path
        # containing this test.
        containing_id = qm.label.split(test_id)[0]
        # Loop over prerequisites.
        for prerequisite_id, outcome in test.GetPrerequisites().items():
            # The ID of the prerequisite test is stored as the element
            # contents.
            prq_element = qm.xmlutil.create_dom_text_element(
                document, "prerequisite", prerequisite_id)
            # The outcome is stored as an attribute.
            prq_element.setAttribute("outcome", outcome)
            element.appendChild(prq_element)

        # Build and add resource elements.
        for resource in test.GetResources():
            act_element = qm.xmlutil.create_dom_text_element(
                document, "resource", resource)
            element.appendChild(act_element)

        # All done.
        return element


    def __MakeDomNodeForResource(self,
                                 document,
                                 element,
                                 resource,
                                 comments=0):
        """Construct a DOM node for a resource.

        'document' -- The DOM document in which the node is being
        constructed.

        'element' -- A test element DOM node in which the test is
        assembled.  If 'None', a new test element node is created.

        'resource' -- The resource to write.

        'comments' -- If true, add DOM comment nodes."""

        # Make an element node unless one was specified.
        if element is None:
            element = document.createElement("resource")
        else:
            assert element.tagName == "resource"
        # Build common stuff.
        self.__MakeDomNodeForItem(document, element, resource, comments)
        # All done.
        return element


    def __MakeDomNodeForItem(self, document, element, item, comments=0):
        """Construct common DOM node elements for a test or resource.

        'document' -- The DOM document in which the node is being
        constructed.

        'element' -- An element DOM node in which the test or resource is
        assembled.

        'item' -- The test or resource to write.  Only components common
        to tests and resources are written.

        'comments' -- If true, add DOM comment nodes."""

        item_id = item.GetId()
        item_class = item.GetClass()
        item_class_name = item.GetClassName()

        # Build and add the class element, which contains the test class
        # name. 
        class_element = document.createElement("class")
        text = document.createTextNode(item_class_name)
        class_element.appendChild(text)
        element.appendChild(class_element)
        
        # Build and add argument elements, one for each argument that's
        # specified for the item.
        arguments = item.GetArguments()
        for name, value in arguments.items():
            arg_element = document.createElement("argument")
            # Store the argument name in the name attribute.
            arg_element.setAttribute("name", name)
            # From the list of fields in the test class, find the one
            # whose name matches this argument.  There should be exactly
            # one. 
            field = filter(lambda f, name=name: f.GetName() == name,
                           item_class.fields)
            assert len(field) == 1
            field = field[0]
            # Add a comment describing the field, if requested.
            if comments:
                # Format the field description as text.
                description = qm.structured_text.to_text(
                    field.GetDescription(), indent=8, width=72)
                # Strip off trailing newlines.
                description = string.rstrip(description)
                # Construct the comment, including the field title.
                comment = "%s:\n%s" % (field.GetTitle(), description)
                # Build and add a comment node.
                comment = qm.xmlutil.sanitize_text_for_comment(comment)
                comment_node = document.createComment(comment)
                arg_element.appendChild(comment_node)
            # Construct a node for the argument/field value itself.
            value_node = field.MakeDomNodeForValue(value, document)
            arg_element.appendChild(value_node)
            element.appendChild(arg_element)

        # Build and add property elements.
        for name, value in item.GetProperties().items():
            property_element = qm.xmlutil.create_dom_text_element(
                document, "property", value)
            property_element.setAttribute("name", name)
            element.appendChild(property_element)


    def __GetSuite(self, suite_id):
        """Load the test suite file with ID 'suite_id'.

        returns -- A 'Suite' object."""

        path = self.IdToPath(suite_id, absolute=1) + suite_file_extension
        # Make sure there is a file by that name.
        if not os.path.isfile(path):
            raise base.NoSuchSuiteError, "no suite file %s" % path
        # Load and parse the suite file.
        document = qm.xmlutil.load_xml_file(path)
        suite = document.documentElement
        assert suite.tagName == "suite"
        # Extract the test and suite IDs.
        test_ids = qm.xmlutil.get_dom_children_texts(suite, "test_id")
        suite_ids = qm.xmlutil.get_dom_children_texts(suite, "suite_id")
        # Make sure they're all valid.
        for id_ in test_ids + suite_ids:
            if not qm.label.is_valid(id_, allow_separator=1):
                raise RuntimeError, qm.error("invalid id", id=id_)
        # Construct the suite.
        return base.Suite(suite_id, test_ids, suite_ids)



class DirectorySuite(base.Suite):
    """A test suite corresponding to directory in the database.

    Each directory in the test database is considered a virtual suite.
    This suite contains all of the tests in the directory and its
    subdirectories."""

    def __init__(self, suite_id, database):
        """Create a new test suite instance.

        'suite_id' -- The test suite ID.

        'database' -- The database containing the suite.

        'dir_path' -- The path, relative to 'db_path', to the directory
        containing the tests.  All tests in and under this directory are
        included in the suite."""

        # Make sure the path exists.
        path = os.path.join(database.GetPath(),
                            database.IdToPath(suite_id))
        if not os.path.isdir(path):
            raise base.NoSuchSuiteError, "no directory at %s" % path
        # Initialize the base class. 
        base.Suite.__init__(self, suite_id, implicit=1)
        # Store the path to the directory.
        self.__suite_path = path


    def GetRawTestIds(self):
        test_ids = {}
        suite_ids = {}
        self.__ScanDirectory(test_ids)
        return test_ids.keys()


    def GetRawSuiteIds(self):
        # Implicit suites don't contain other suites.
        return []


    def GetTestIds(self):
        return self.GetRawTestIds()


    # Helper methods.

    def __ScanDirectory(self, test_ids, sub_path=""):
        """Recursively scan the tests in directory 'sub_path'.

        'test_ids' -- A map whose keys are test IDs.

        'sub_path' -- Path relative to top of suite directory from which
        to add tests.

        This method calls itself recursively for subdirectories."""

        suite_id = self.GetId()
        sub_id = qm.label.from_path(sub_path)
        # Generate the full path to the directory being scanned.
        path = os.path.join(self.__suite_path, sub_path)
        # Loop over its contents.
        for entry in dircache.listdir(path):
            entry_path = os.path.join(path, entry)
            # Is it a directory?
            if os.path.isdir(entry_path):
                # Yes.  Scan recursively.
                self.__ScanDirectory(test_ids, os.path.join(sub_path, entry))
            else:
                # Look at its extension.
                name, extension = os.path.splitext(entry)
                if extension == test_file_extension:
                    # It looks like a test file.
                    test_id = qm.label.join(suite_id, sub_id, name)
                    test_ids[test_id] = None
                    


########################################################################
# functions
########################################################################

def scan_dir_for_labels(dir, extension): 
    """Return labels for files in and under 'dir' matching 'extension'.

    Recursively searches for files under 'dir' whose names end in
    'extension'.  Returns a list of corresponding labels, relative to
    'dir'."""

    results = []
    # Scan contents of 'dir'.
    for entry in dircache.listdir(dir):
        # Construct the full path to the entry.
        entry_path = os.path.join(dir, entry)
        # Is it a subdirectory?
        if os.path.isdir(entry_path):
            # Yes.  Call ourselves recursively.
            sub_results = scan_dir_for_labels(entry_path, extension)
            # Make the contents of the subdirectory relative to the
            # top-level 'dir' by prefixing the subdirectory name.
            rel = qm.label.MakeRelativeTo(entry)
            sub_results = map(rel, sub_results)
            # Add to the results.
            results = results + sub_results
        else:
            # Not a directory.  Is it a file ending with the desired
            # extension? 
            if os.path.isfile(entry_path):
                entry_name, entry_extension = os.path.splitext(entry)
                if extension == entry_extension:
                    # Yes; keep it.
                    results.append(entry_name)

    return results


def scan_dir_for_suite_dirs(dir):
    """Return labels for directories under 'dir' that are suites."""

    results = []
    # Scan contents of 'dir'.
    for entry in dircache.listdir(dir):
        # Construct the full path to the entry.
        entry_path = os.path.join(dir, entry)
        # Is it a subdirectory?
        if os.path.isdir(entry_path):
            # Yes.  If it's called 'CVS', though, skip it, so that we
            # don't get confused by CVS-controlled test suite directory
            # hierarchies.
            if entry == "CVS":
                continue
            # Add the directory itself.
            # FIXME: Check if it's empty?
            results.append(entry)
            # Call ourselves recursively.
            sub_results = scan_dir_for_suite_dirs(entry_path)
            # Make the contents of the subdirectory relative to the
            # top-level 'dir' by prefixing the subdirectory name.
            rel = qm.label.MakeRelativeTo(entry)
            sub_results = map(rel, sub_results)
            # Add to the results.
            results = results + sub_results
    return results


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

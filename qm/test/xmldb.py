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
from   file_database import *
import os
import qm.common
import qm.fields
import qm.label
import qm.structured_text
from   qm.test.database import *
from   qm.test.suite import *
import qm.xmlutil
import shutil
import string

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



class Database(FileDatabase, qm.common.MutexMixin):
    """A database represnting tests as XML files in a directory tree."""

    # When processing the DOM tree for an XML test file, we may
    # encounter two kinds of errors.  One indicates an invalid DOM tree,
    # i.e. the structure is at variance with the test DTD.  We can use
    # 'assert' to flag these, since we expect that the validating parser
    # should have caught those.  Other errors are semantic, for instance
    # specifying an argument which doesn't exist in the test class.  For
    # these, we raise an 'TestFileError'.

    def __init__(self, path):
        """Open a connection to a database.

        'path' -- The absolute path to the directory that represents
        the database."""

        # Initialize base classes.
        FileDatabase.__init__(self, path, AttachmentStore(path, self))
        # Make sure the database path exists.
        if not os.path.isdir(path):
            raise ValueError, \
                  qm.error("db path doesn't exist", path=path)
        # Cache loaded objects in these attributes.
        self.__tests = {}
        self.__suites = {}
        self.__resources = {}


    def GetClassPaths(self):
        lock = self.GetLock()
        # Use the base class implementation.
        return FileDatabase.GetClassPaths(self)


    def _GetTestFromPath(self, test_id, test_path):
        # Try to use a cached value.
        try:
            return self.__tests[test_id]
        except KeyError:
            # Not in cache; no biggie.
            pass

        # Load the test file.
        lock = self.GetLock()
        try:
            test = self.__LoadItem(test_id, test_path,
                                   self.__ParseTestDocument)
        except (qm.fields.DomNodeError, qm.xmlutil.ParseError), \
               exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml test",
                               test_id=test_id,
                               message=str(exception))
            raise TestFileError, message
        else:
            # Cache the test for next time.
            self.__tests[test_id] = test
            # Return it.
            return test
        

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
        test_path = self.GetTestPath(test_id)
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
        FileDatabase.RemoveTest(self, test_id)


    def _GetResourceFromPath(self, resource_id, resource_path):
        # Try to use a cached value.
        try:
            return self.__resources[resource_id]
        except KeyError:
            pass

        # Load the resource file.
        lock = self.GetLock()
        try:
            resource = self.__LoadItem(resource_id, resource_path,
                                       self.__ParseResourceDocument)
        except (qm.fields.DomNodeError, qm.xmlutil.ParseError), \
               exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml resource",
                               resource_id=resource_id,
                               message=str(exception))
            raise TestFileError, message
        else:
            # Cache the resource for next time.
            self.__resources[resource_id] = resource
            # Return it.
            return resource
        

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
        resource_path = self.GetResourcePath(resource_id)
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
        FileDatabase.RemoveResource(self, resource_id)


    def _GetSuiteFromPath(self, suite_id, suite_path):
        try:
            return self.__suites[suite_id]
        except KeyError:
            pass
        
        lock = self.GetLock()
        suite = self.__LoadSuiteFile(suite_id, suite_path)
        self.__suites[suite_id] = suite
        return suite
            

    def WriteSuite(self, suite):
        """Write 'suite' to the database as a suite file."""

        # Don't write directory suites to suite file.
        assert not suite.IsImplicit()

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
        for test_id in suite.GetTestIds():
            test_id_element = qm.xmlutil.create_dom_text_element(
                document, "test_id", test_id)
            suite_element.appendChild(test_id_element)
        for suite_id in suite.GetSuiteIds():
            suite_id_element = qm.xmlutil.create_dom_text_element(
                document, "suite_id", suite_id)
            suite_element.appendChild(suite_id_element)
        # Find the file system path for the suite file.
        suite_path = self.GetSuitePath(suite)
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
        FileDatabase.RemoveSuite(self, suite_id)


    # Helper functions.

    def __InvalidateItem(self, item_id, cache):
        """Invalidate the cache entry for 'item_id'."""

        if cache.has_key(item_id):
            del cache[item_id]
        # Invalidate the suite containing this item.
        parent_suite_id = qm.label.split(item_id)[0]
        if self.__suites.has_key(parent_suite_id):
            del self.__suites[parent_suite_id]


    def __LoadItem(self, item_id, path, document_parser):
        """Load an item (a test or resource) from an XML file.

        This function is used for logic common to tests and resources.

        'item_id' -- The ID of the item to get.

        'path' -- The path to the test or resource file.

        'document_parser' -- A function that takes an XML DOM document
        as its argument and returns the constructed item object."""

        # Load and parse the XML item representation.
        document = qm.xmlutil.load_xml_file(path)
        # Turn it into an object.
        item = document_parser(item_id, document)
        # Set its working directory.
        item.SetWorkingDirectory(os.path.dirname(path))

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
            test_class = base.get_test_class(test_class_name, self)
        except ImportError:
            raise UnknownTestClassError, \
                  qm.error("unknown test class",
                           test_class_name=test_class_name,
                           test_id=test_id)
        arguments = self.__GetArgumentsFromDomNode(test_node, test_class)
        categories = qm.xmlutil.get_child_texts(test_node,
                                                "category")
        prerequisites = self.__GetPrerequisitesFromDomNode(test_node)
        resources = self.__GetResourcesFromDomNode(test_node)
        # Construct a test descriptor for it.
        test = TestDescriptor(self,
                              test_id,
                              test_class_name,
                              arguments,
                              prerequisites,
                              categories,
                              resources)
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
            resource_class = \
               base.get_resource_class(resource_class_name, self)
        except KeyError:
            raise UnknownResourceClassError, class_name
        arguments = self.__GetArgumentsFromDomNode(resource_node,
                                                   resource_class)
        # Construct a ResourceDescriptor for it.
        return ResourceDescriptor(self, resource_id,
                                  resource_class_name,
                                  arguments)
    

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
        fields = qm.test.base.get_class_arguments(klass)

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
            value = field.GetValueFromDomNode(value_node,
                                              self.GetAttachmentStore())
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

        'test' -- The 'TestDescriptor' for the test for which we are to
        create a DOM node.

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

        # Build and add prerequisite elements.  Loop over prerequisites.
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
                           qm.test.base.get_class_arguments(item_class))
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


    def __LoadSuiteFile(self, suite_id, path):
        """Load the test suite file at 'path' with suite ID 'suite_id'.

        returns -- A 'Suite' object."""

        # Make sure there is a file by that name.
        if not os.path.isfile(path):
            raise NoSuchSuiteError, "no suite file %s" % path
        # Load and parse the suite file.
        document = qm.xmlutil.load_xml_file(path)
        suite = document.documentElement
        assert suite.tagName == "suite"
        # Extract the test and suite IDs.
        test_ids = qm.xmlutil.get_child_texts(suite, "test_id")
        suite_ids = qm.xmlutil.get_child_texts(suite, "suite_id")
        # Make sure they're all valid.
        for id_ in test_ids + suite_ids:
            if not qm.label.is_valid(id_, allow_separator=1):
                raise RuntimeError, qm.error("invalid id", id=id_)
        # Construct the suite.
        return Suite(self, suite_id, implicit=0,
                     test_ids=test_ids, suite_ids=suite_ids)



class AttachmentStore(qm.attachment.AttachmentStore):
    """The attachment store implementation to use with the XML database.

    The attachment store stores attachment data in the same directory
    hierarchy as test files.  The data file for a test's attachment is
    stored in the same subdirectory as the test.  Where possible, the
    attachment's file name is used."""

    def __init__(self, path, database):
        """Create a connection to an attachment store.

        'path' -- The path to the top of the attachment store directory
        tree.

        'database' -- The database with which this attachment store is
        associated."""

        self.__path = path
        self.__database = database


    def Store(self, item_id, mime_type, description, file_name, data):
        """Store attachment data, and construct an attachment object.

        'item_id' -- The ID of the test or resource of which this
        attachment is part.

        'mime_type' -- The attachment MIME type.

        'description' -- A description of the attachment.

        'file_name' -- The name of the file from which the attachment
        was uploaded.

        'data' -- The attachment data.

        returns -- An 'Attachment' object, with its location set
        correctly."""

        # Construct the path at which we'll store the attachment data.
        data_file_path = self.__MakeDataFilePath(item_id, file_name)
        # Store it.
        data_file = open(os.path.join(self.__path, data_file_path), "w")
        data_file.write(data)
        data_file.close()
        # Construct an 'Attachment'.
        return qm.attachment.Attachment(
            mime_type,
            description,
            file_name,
            location=data_file_path)


    # Implementation of base class methods.

    def GetData(self, location):
        data_file_path = os.path.join(self.__path, location)
        return open(data_file_path, "r").read()


    def GetDataFile(self, location):
        data_file_path = os.path.join(self.__path, location)
        return data_file_path


    def GetSize(self, location):
        data_file_path = os.path.join(self.__path, location)
        return os.stat(data_file_path)[6]


    # Helper functions.

    def __MakeDataFilePath(self, item_id, file_name):
        """Construct the path to an attachment data file.

        'item_id' -- The test or resource item of which the attachment
        is part.

        'file_name' -- The file name specified for the attachment."""
        
        # Convert the item's containing suite to a path.
        parent_suite_id = qm.label.split(item_id)[0]
        parent_suite_path = qm.label.to_path(parent_suite_id)
        # Construct a file name free of suspicious characters.
        base, extension = os.path.splitext(file_name)
        safe_file_name = qm.label.thunk(base) + extension

        data_file_path = os.path.join(parent_suite_path, safe_file_name)
        full_data_file_path = os.path.join(self.__path, data_file_path)
        # Is the file name by itself OK in this directory?  It must not
        # have a file extension used by the XML database itself, and
        # there must be no other file with the same name there.
        if extension not in [self.__database.GetTestExtension(),
                             self.__database.GetSuiteExtension(),
                             self.__database.GetResourceExtension()] \
           and not os.path.exists(full_data_file_path):
            return data_file_path

        # No good.  Construct alternate names by appending numbers
        # incrementally.
        index = 0
        while 1:
            data_file_path = os.path.join(parent_suite_path, safe_file_name) \
                             + ".%d" % index
            full_data_file_path = os.path.join(self.__path, data_file_path)
            if os.path.exists(full_data_file_path):
                index = index + 1
                continue
            else:
                return data_file_path
        


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

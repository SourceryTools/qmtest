########################################################################
#
# File:   xml_database.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   XML-based test database implementation.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from   __future__ import nested_scopes
import dircache
import os
import qm.common
import qm.fields
import qm.label
import qm.structured_text
import qm.test.base
from   qm.test.database import *
from   qm.test.file_database import *
from   qm.test.suite import *
import qm.xmlutil
import shutil
import string
import xml
import xml.dom

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



class XMLDatabase(ExtensionDatabase):
    """A database representing tests as XML files in a directory tree."""

    def __init__(self, path, arguments):

        # Initialize base classes.
        ExtensionDatabase.__init__(self, path, arguments)
        # Create an AttachmentStore for this database.
        self.__store = AttachmentStore(path, self)
        # Make sure the database path exists.
        if not os.path.isdir(path):
            raise qm.common.QMException, \
                  qm.error("db path doesn't exist", path=path)


    def _GetTestFromPath(self, test_id, test_path):
        try:
            return self.__LoadItem(test_id, test_path,
                                   self.__ParseTestDocument)
        except (qm.fields.DomNodeError, qm.xmlutil.ParseError), \
               exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml test",
                               test_id=test_id,
                               message=str(exception))
            raise TestFileError, message
        

    def WriteTest(self, test):

        # Generate the document.
        document = \
            qm.extension.make_dom_document(test.GetClass(),
                                           test.GetArguments())
        # Find the file system path for the test file.
        test_path = self.GetTestPath(test.GetId())
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(test_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the test.
        document.writexml(open(test_path, "w"))


    def _GetResourceFromPath(self, resource_id, resource_path):
        try:
            return self.__LoadItem(resource_id, resource_path,
                                   self.__ParseResourceDocument)
        except (qm.fields.DomNodeError, qm.xmlutil.ParseError), \
               exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml resource",
                               resource_id=resource_id,
                               message=str(exception))
            raise TestFileError, message
        

    def WriteResource(self, resource):

        # Generate the document.
        document = \
            qm.extension.make_dom_document(resource.GetClass(),
                                           resource.GetArguments())
        # Find the file system path for the resource file.
        resource_path = self.GetResourcePath(resource.GetId())
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(resource_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the resource.
        document.writexml(open(resource_path, "w"))


    def WriteSuite(self, suite):
        """Write 'suite' to the database as a suite file."""

        # Don't write directory suites to suite file.
        assert not suite.IsImplicit()

        # Generate the document and document type for XML suite files.
        document = qm.xmlutil.create_dom_document(
            public_id=qm.test.base.dtds["suite"],
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
        suite_path = self.GetSuitePath(suite.GetId())
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(suite_path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        # Write out the suite.
        document.writexml(open(suite_path, "w"))


    # Helper functions.

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
        
        # Parse the DOM node.
        test_class, arguments \
            = (qm.extension.parse_dom_element
               (document.documentElement,
                lambda n : qm.test.base.get_test_class(n, self)))
        test_class_name = qm.extension.get_extension_class_name(test_class)
        # For backwards compatibility, look for "prerequisite" elements.
        for p in document.documentElement.getElementsByTagName("prerequisite"):
            if not arguments.has_key("prerequisites"):
                arguments["prerequisites"] = []
            arguments["prerequisites"].append((qm.xmlutil.get_dom_text(p),
                                               p.getAttribute("outcome")))
        # For backwards compatibility, look for "resource" elements.
        for r in document.documentElement.getElementsByTagName("resource"):
            if not arguments.has_key("resources"):
                arguments["resources"] = []
            arguments["resources"].append(qm.xmlutil.get_dom_text(r))
        # Construct a descriptor for it.
        test = TestDescriptor(self,
                              test_id,
                              test_class_name,
                              arguments)
        return test
        

    def __ParseResourceDocument(self, resource_id, document):
        """Return a resource object constructed from a resource document.

        'resource_id' -- The resource ID of the resource.

        'document' -- A DOM document node containing a single resource
        element from which the resource object is constructed."""

        # Parse the DOM node.
        resource_class, arguments \
            = (qm.extension.parse_dom_element
               (document.documentElement,
                lambda n : qm.test.base.get_resource_class(n, self)))
        resource_class_name \
            = qm.extension.get_extension_class_name(resource_class)
        # Construct a descriptor for it.
        resource = ResourceDescriptor(self,
                                      resource_id,
                                      resource_class_name,
                                      arguments)
        return resource
    

    def _GetSuiteFromPath(self, suite_id, path):
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
            if not self.IsValidLabel(id_, is_component = 0):
                raise RuntimeError, qm.error("invalid id", id=id_)
        # Construct the suite.
        return Suite(self, suite_id, implicit=0,
                     test_ids=test_ids, suite_ids=suite_ids)


    def GetAttachmentStore(self):
        """Returns the 'AttachmentStore' associated with the database.

        returns -- The 'AttachmentStore' containing the attachments
        associated with tests and resources in this database."""

        return self.__store


    def _Trace(self, message,):
        """Write a trace 'message'.

        'message' -- A string to be output as a trace message."""

        tracer = qm.test.cmdline.get_qmtest().GetTracer()
        tracer.Write(message, "xmldb")
    


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
        parent_suite_id = self.SplitLabel(item_id)[0]
        parent_suite_path = self._LabelToPath(parent_suite_id)
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

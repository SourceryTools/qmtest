########################################################################
#
# File:   xml_database.py
# Author: Alex Samuel
# Date:   2001-03-08
#
# Contents:
#   XML-based test database implementation.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os
import qm.common
from   qm.extension import get_class_arguments
import qm.fields
import qm.label
import qm.structured_text
import qm.test.base
from   qm.test.database import *
from   qm.test.file_database import *
from   qm.test.suite import *
from   qm.test.classes.explicit_suite import ExplicitSuite
import qm.xmlutil
import shutil
import string
import xml
import xml.dom
import xml.sax

########################################################################
# classes
########################################################################

class TestFileError(RuntimeError):
    """An error in the format or contents of an XML test file."""

    pass



class XMLDatabase(ExtensionDatabase):
    """A database representing tests as XML files in a directory tree."""

    def __init__(self, path, arguments):

        # Initialize base classes.
        ExtensionDatabase.__init__(self, path, arguments)
        # Create an AttachmentStore for this database.
        self.__store = qm.attachment.FileAttachmentStore(path)


    def _GetTestFromPath(self, test_id, test_path):
        try:
            return self.__LoadItem(test_id, test_path,
                                   self.__ParseTestDocument)
        except Exception, exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml test",
                               test_id=test_id,
                               message=str(exception))
            raise TestFileError, message
        

    def _GetResourceFromPath(self, resource_id, resource_path):
        try:
            return self.__LoadItem(resource_id, resource_path,
                                   self.__ParseResourceDocument)
        except Exception, exception:
            # Problem while parsing XML.
            message = qm.error("error loading xml resource",
                               resource_id=resource_id,
                               message=str(exception))
            raise TestFileError, message
        
    # Helper functions.

    def __StoreAttachments(self, item):
        """Store all attachments in 'item' in the attachment store.

        'item' -- A 'Test' or 'Resource'.  If any of its fields contain
        attachments, add them to the 'AttachmentStore'."""

        # Get all of the attachments associated with the new item.
        new_attachments = item.GetAttachments()

        # Remove old attachments that are not also among the new
        # attachments.
        store = self.GetAttachmentStore()
        try:
            old_item = self.GetItem(item.kind, item.GetId())
        except:
            old_item = None
        if old_item:
            old_attachments = old_item.GetItem().GetAttachments()
            for o in old_attachments:
                found = 0
                for n in new_attachments:
                    if (n.GetStore() == store
                        and n.GetFileName() == o.GetFileName()):
                        found = 1
                        break
                if not found:
                    store.Remove(o.GetLocation())

        # Put any new attachments into the attachment store.
        for a in new_attachments:
            if a.GetStore() != store:
                location = self.__MakeDataFilePath(item.GetId(),
                                                   a.GetFileName())
                a.Move(store, location)

         
    def __MakeDataFilePath(self, item_id, file_name):
        """Construct the path to an attachment data file.

        'item_id' -- The test or resource item of which the attachment
        is part.

        'file_name' -- The file name specified for the attachment."""
        
        # Convert the item's containing suite to a path.
        parent_suite_path \
            = os.path.dirname(self._GetPathFromLabel(item_id))
        # The relative part of the eventual full file name will be
        # the part after the parent_suite_path and the directory
        # name separator character(s).
        abs_len = len(parent_suite_path) + len(os.sep)
        
        # Construct a file name free of suspicious characters.
        base, extension = os.path.splitext(file_name)
        safe_file_name = qm.label.thunk(base) + extension

        data_file_path = os.path.join(parent_suite_path, safe_file_name)
        # Is the file name by itself OK in this directory?  It must not
        # have a file extension used by the XML database itself, and
        # there must be no other file with the same name there.
        if extension not in [self.GetTestExtension(),
                             self.GetSuiteExtension(),
                             self.GetResourceExtension()] \
           and not os.path.exists(data_file_path):
            return data_file_path[abs_len:]

        # No good.  Construct alternate names by appending numbers
        # incrementally.
        index = 0
        while 1:
            data_file_path = os.path.join(parent_suite_path,
                                          safe_file_name + ".%d" % index)
            if not os.path.exists(data_file_path):
                return data_file_path[abs_len:]
            index = index + 1


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
                lambda n : qm.test.base.get_test_class(n, self),
                self.__store))
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
        # For backwards compatibility, handle XML files using the
        # "suite" tag.  New databases will have Suite files using the
        # "extension" tag.
        suite = document.documentElement
        if suite.tagName == "suite":
            assert suite.tagName == "suite"
            # Extract the test and suite IDs.
            test_ids = qm.xmlutil.get_child_texts(suite, "test_id")
            suite_ids = qm.xmlutil.get_child_texts(suite, "suite_id")
            # Make sure they're all valid.
            for id_ in test_ids + suite_ids:
                if not self.IsValidLabel(id_, is_component = 0):
                    raise RuntimeError, qm.error("invalid id", id=id_)
            # Construct the suite.
            return ExplicitSuite({ "is_implicit" : "false",
                                   "test_ids" : test_ids,
                                   "suite_ids" : suite_ids },
                                 **{ ExplicitSuite.EXTRA_ID : suite_id,
                                     ExplicitSuite.EXTRA_DATABASE : self })
        else:
            # Load the extension.
            extension_class, arguments = \
                qm.extension.parse_dom_element(
                    suite,
                    lambda n: get_extension_class(n, "suite", self),
                    self.GetAttachmentStore())
            # Construct the actual instance.
            extras = { extension_class.EXTRA_ID : suite_id,
                       extension_class.EXTRA_DATABASE : self }
            return extension_class(arguments, **extras)


    def WriteExtension(self, id, extension):

        kind = extension.kind
        if kind in ("resource", "test"):
            self.__StoreAttachments(extension)
        # Figure out what path should be used to store the test.
        path = self._GetPath(kind, id)
        # If the file is in a new subdirectory, create it.
        containing_directory = os.path.dirname(path)
        if not os.path.isdir(containing_directory):
            os.makedirs(containing_directory)
        extension.Write(open(path, "w"))
        
                 
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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   attachment.py
# Author: Alex Samuel
# Date:   2001-03-21
#
# Contents:
#   Generic code for handling arbitrary file attachments.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""Code for handling arbitrary file attachments.

'Attachment' is a base class for classes that represent arbitrary
attachments.  Each 'Attachment' object has these four attributes:

  'mime_type' -- The MIME type of the attachment contents.  This
  information enables user interfaces to handle attachment data in a
  sensible fasion.

  'description' -- The user's description of the attachment contents.

  'file_name' -- A file name associated with the description.  This is
  usually the name of the file from which the attachment was originally
  uploaded or inserted.

  'location' -- A string containing the external location of the
  attachment data.  The semantics of this string are defined by
  implementations of 'AttachmentStore', which use it to locate the
  attachment's data.

A special 'TemporaryAttachmentStore', with a different interface, is
used to store attachment data temporarily, at most for the life of the
program.  The 'temporary_store' global instance should be used.""" 

########################################################################
# imports
########################################################################

import common
import mimetypes
import os
import xmlutil
import temporary_directory

########################################################################
# classes
########################################################################

class Attachment:
    """An arbitrary file attachment.

    Conceptually, an attachment is composed of these parts:

     1. A MIME type, as a string.

     2. A description, as a structured text string.

     3. A file name, corresponding to the original name of the file from
        which the attachment was uploaded, or the name of the file to
        use when the attachment is presented to the user in a file
        system.

     4. A block of arbitrary data.

    For efficiency reasons, the attachment data is not stored in the
    attachment.  Instead, a *location* is stored, which is a key into
    the associated 'AttachmentStore' object."""

    def __init__(self,
                 mime_type,
                 description,
                 file_name,
                 location,
                 store):
        """Create a new attachment.

        'mime_type' -- The MIME type.  If 'None' or an empty string, the
        function attempts to guess the MIME type from other information.

        'description' -- A description of the attachment contents.

        'file_name' -- The user-visible file name to associate the
        attachment.

        'location' -- The location in an attachment store at which to
        find the attachment data.

        'store' -- The attachment store in which the data is stored."""

        # If no MIME type is specified, try to guess it from the file
        # name.
        if mime_type == "" or mime_type is None:
            mime_type = mimetypes.guess_type(file_name)[0]
            if mime_type is None:
                # Couldn't guess from the file name.  Use a safe
                # default.
                mime_type = "application/octet-stream"
        self.__mime_type = mime_type
        # Store other attributes.
        self.__description = description
        self.__file_name = file_name
        self.__location = location
        self.__store = store


    def GetMimeType(self):
        """Return the attachment's MIME type."""

        return self.__mime_type


    def GetDescription(self):
        """Return the attachment's description."""

        return self.__description


    def GetFileName(self):
        """Return the attachment's file name."""

        return self.__file_name


    def GetLocation(self):
        """Return the attachment's location in an attachment store."""

        return self.__location


    def GetData(self):
        """Get attachment data.

        returns -- The attachment data."""

        return self.GetStore().GetData(self.GetLocation())
        

    def GetDataFile(self):
        """Return the path to a file containing attachment data.

        returns -- A file system path.  The file should be considered
        read-only, and should not be modified in any way."""

        return self.GetStore().GetDataFile(self.GetLocation())


    def GetStore(self):
        """Return the store in which this attachment is located.

        returns -- The 'AttachmentStore' that contains this attachment."""

        return self.__store

    
    def __str__(self):
        return '<Attachment "%s" (%s)>' \
               % (self.GetDescription(), self.GetMimeType())


    def __cmp__(self, other):
        return other is None \
               or self.GetDescription() != other.GetDescription() \
               or self.GetMimeType() != other.GetMimeType() \
               or self.GetFileName() != other.GetFileName() \
               or self.GetLocation() != other.GetLocation() \
               or self.GetStore() != other.GetStore()
    


class AttachmentStore(object):
    """Interface for classes which store attachment data.

    An attachment store stores the raw data for an attachment.  The
    store is not responsible for storing auxiliary information,
    including the attachment's description, file name, or MIME type.

    Users of an 'AttachmentStore' reference attachment data by a
    *location*, which is stored with the attachment.

    Please note that the 'AttachmentStore' interface provides methods
    for retrieving attachment data only; not for storing it.  The
    interface for storing may be defined in any way by implementations."""

    def GetData(self, location):
        """Return the data for an attachment.

        returns -- A string containing the attachment data."""

        raise NotImplementedError


    def GetDataFile(self, location):
        """Return the path to a file containing the data for
        'attachment'.

        returns -- A file system path.

        The file is read-only, and may be a temporary file.  The caller
        should not modify the file in any way."""

        raise NotImplementedError


    def GetSize(self, location):
        """Return the size of the data for an attachment.

        returns -- The length of the attachment data, in bytes.

        This method may be overridden by derived classes."""

        return len(self.GetData(location))


    def HandleDownloadRequest(self, request):
        """Handle a web request to download attachment data.

        'request' -- A 'WebRequest' object.  The location of the
        attachment data is stored in the 'location' property, and the
        MIME type in the 'mime_type' property.

        returns -- A pair '(mime_type, data)' where 'mime_type' is the
        MIME type stored in the request and 'data' is the contents of
        the attachment."""

        location = request["location"]
        mime_type = request["mime_type"]
        data = self.GetData(location)
        return (mime_type, data)


    def Store(self, attachment, location):
        """Add an attachment to the store.

        'attachment' -- The 'Attachment' to store.

        'location' -- The location in which to store the 'attachment'.

        returns -- A new 'Attachment' whose 'AttachmentStore' is
        'self'."""

        raise NotImplementedError
        


class FileAttachmentStore(AttachmentStore):
    """An attachment store based on the file system.

    The locations are the names of files in the file system."""

    def __init__(self, root = None):
        """Construct a new 'FileAttachmentStore'

        'root' -- If not 'None', the root directory for the store.  All
        locations are relative to this directory.  If 'None', all
        locations are relative to the current directory."""
        
        super(AttachmentStore, self).__init__()
        self.__root = root
        
        
    def GetData(self, location):

        # Open the file.
        f = open(self.GetDataFile(location))
        # Read the contents.
        s = f.read()
        # Close the file.
        f.close()

        return s


    def GetDataFile(self, location):

        if self.__root is not None:
            return os.path.join(self.__root, location)
        else:
            return location


    def GetSize(self, location):
        
        return os.stat(self.GetDataFile(location))[6]


    def Store(self, attachment, location):

        # Create the file.
        file = open(self.GetDataFile(location), "w")
        # Write the data.
        file.write(attachment.GetData())
        # Close the file.
        file.close()

        return Attachment(attachment.GetMimeType(),
                          attachment.GetDescription(),
                          attachment.GetFileName(),
                          location,
                          self)


    def Remove(self, location):
        """Remove an attachment.

        'location' -- The location whose data should be removed."""

        os.remove(self.GetDataFile(location))



class TemporaryAttachmentStore(FileAttachmentStore):
    """Temporary storage for attachment data.

    A 'TemporaryAttachmentStore' stores attachment data in a temporary
    location, for up to the lifetime of the running program.  When the
    program ends, all temporarily stored attachment data is deleted.

    A data object in the temporary store is identified by its location.
    Locations should be generated by 'make_temporary_location'."""

    def __init__(self):
        """Construct a temporary attachment store.

        The store is initially empty."""

        # Construct a temporary directory in which to store attachment
        # data.
        self.__tmpdir = temporary_directory.TemporaryDirectory()
        # Initialize the base class.
        path = self.__tmpdir.GetPath()
        super(TemporaryAttachmentStore, self).__init__(path)


    def HandleUploadRequest(self, request):
        """Handle a web request to upload attachment data.

        Store the attachment data contained in the request as a
        temporary attachment.  It is assumed that the request is being
        submitted from a popup upload browser window, so the returned
        HTML page instructs the window to close itself.

        'request' -- A 'WebRequest' object.

        returns -- HTML text of a page that instructs the browser window
        to close."""

        location = request["location"]
        # Because this data is in the temporary attachment store, the
        # location should be a temporary location.
        assert is_temporary_location(location)
        # Create the file.
        file = open(self.GetDataFile(location), "w")
        # Write the data.
        file.write(request["file_data"])
        # Close the file.
        file.close()
        # Return a page that closes the popup window from which the
        # attachment was submitted.
        return '''
        <html><body>
        <script type="text/javascript" language="JavaScript">
        window.close();
        </script>
        </body></html>
        '''

########################################################################
# functions
########################################################################

_temporary_location_prefix = "_temporary"


def make_temporary_location():
    """Return a unique location for temporary attachment data."""

    return _temporary_location_prefix + common.make_unique_tag()

        
def is_temporary_location(location):
    """Return true if 'location' is a temporary attachment location."""

    return location.startswith(_temporary_location_prefix)


def make_dom_node(attachment, document):
    """Create a DOM element node for this attachment.

    'document' -- A DOM document node in which to create the
    element.

    returns -- A DOM element node."""

    # Create an attachment element.
    node = document.createElement("attachment")
    # Is it a null attachment?
    if attachment is None:
        # Then that's it.
        return node

    mime_type = attachment.GetMimeType()

    # Create and add the description node.
    child = xmlutil.create_dom_text_element(
        document, "description", attachment.GetDescription())
    node.appendChild(child)
    # Create and add the MIME type node.
    child = xmlutil.create_dom_text_element(
        document, "mime-type", mime_type)
    node.appendChild(child)
    # Create and add the file name node.
    child = xmlutil.create_dom_text_element(
        document, "filename", attachment.GetFileName())
    node.appendChild(child)
    # Create a location element, to include attachment data by
    # reference.
    location = attachment.GetLocation()
    # Attchments whose data is in the temporary store should not be
    # externalized. 
    assert not is_temporary_location(location)
    child = xmlutil.create_dom_text_element(
        document, "location", location)

    node.appendChild(child)
    return node


def from_dom_node(node, store):
    """Construct an attachment object from a DOM element node.

    'node' -- A DOM attachment element node.

    'store' -- The associated attachment store.
    
    returns -- An attachment instance.  The type is determined by
    'attachment_class'.

    If the attachment object requires additional context information to
    interpret the location (if it's specified in the attachment
    element), the caller must provide it directly to the object."""

    if len(node.childNodes) == 0:
        # It's an empty element, signifying a null attachment.
        return None

    # Extract the fixed fields; use a default value for each that is not
    # present. 
    description = xmlutil.get_child_text(node, "description", "")
    mime_type = xmlutil.get_child_text(
        node, "mime-type", "application/octet-stream")
    file_name = xmlutil.get_child_text(node, "filename", "")
    location = xmlutil.get_child_text(node, "location")
    # Construct the resulting attachment.
    return Attachment(mime_type, description, file_name, location, store)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

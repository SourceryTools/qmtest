########################################################################
#
# File:   attachment.py
# Author: Alex Samuel
# Date:   2001-03-21
#
# Contents:
#   Generic code for handling arbitrary file attachments.
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

"""Code for handling arbitrary file attachments.

'Attachment' is a base class for classes that represent arbitrary
attachments.  All subclasses have the same semantics in general, but
they vary in how they store externalize the attachment data.

Each 'Attachment' object has these three attributes:

  'mime_type' -- The MIME type of the attachment contents.  This
  information enables user interfaces to handle attachment data in a
  sensible fasion.

  'description' -- The user's description of the attachment contents.

  'file_name' -- A file name associated with the description.  This is
  usually the name of the file from which the attachment was originally
  uploaded or inserted.

In addition, an 'Attachment' will have either one, but not both, of
these attributes:

  'data' -- The attachment data, as a string.

  'location' -- A string containing the external location of the
  attachment data.  The semantics of this string are not defined;
  subclasses may use it as it sees fit.

""" 

########################################################################
# imports
########################################################################

import common
import diagnostic
import mimetypes
import xmlutil

########################################################################
# classes
########################################################################

class Attachment:
    """Base class for file attachment classes."""

    def __init__(self,
                 mime_type=None,
                 description="",
                 file_name=""):
        """Create a new attachment object.

        'mime_type' -- The MIME type of the attachment's contents.

        'description' -- A text description of the attachment's
        contents.

        'file_name' -- The original file name associated with this
        attachment, such as the name of the file from which the user
        uploaded it."""

        # Store the description and file name.
        self.description = description
        self.file_name = file_name
        # If no MIME type is specified, try to guess it from the file
        # name.
        if mime_type == "" or mime_type == None:
            mime_type = mimetypes.guess_type(file_name)[0]
            if mime_type is None:
                # Couldn't guess from the file name.  Use a safe
                # default.
                mime_type = "application/octet-stream"
        self.mime_type = mime_type
            

    def __str__(self):
        return '<Attachment "%s" (%s)>' \
               % (self.description, self.mime_type)


    def __cmp__(self, other):
        if other is None:
            return 1
        if self.description != other.description \
           or self.mime_type != other.mime_type \
           or self.file_name != other.file_name:
            return 1
        if hasattr(self, "location") \
           and hasattr(other, "location") \
           and self.location == other.location:
            return 0
        if hasattr(self, "data") \
           and hasattr(other, "data") \
           and self.data == other.data:
            return 0
        # FIXME!  This doesn't always work.
        return 1


    # Methods that should be overridden.

    def GetData(self):
        """Return the attachment data."""

        raise common.MethodShouldBeOverriddenError, "Attachment.GetData"


    def GetDataSize(self):
        """Return the size, in bytes, of the attachment data."""

        raise common.MethodShouldBeOverriddenError, "Attachment.GetSize"


    def MakeDomNode(self, document):
        """Return a DOM element node representing this attachment."""

        raise common.MethodShouldBeOverriddenError, \
              "Attachment.MakeDomNode"
        



########################################################################
# functions
########################################################################

def make_dom_node(attachment, document, data=None, location=None):
    """Create a DOM element node for this attachment.

    'document' -- A DOM document node in which to create the
    element.

    'data' -- If not 'None', the attachment contents.

    'location' -- If not 'None', a string containing the external
    location of the attachment's contents.

    Exactly one of 'data' and 'location' should be specified.  Note that
    the 'location' and 'data' attributes of the attachment object are
    *not* used automatically.

    Classes derived from 'Attachment' use this function to implmenet the
    'MakeDomeNode' method, passing either 'data' or 'location'.  This
    allows the XML representation of an attachment to differ from the
    in-memory/database representation.  For instance, a subclass may
    choose to use the 'location' attribute, thus storing the attachment
    data externally, and at the same time pass the 'data' argument to
    this function, which causes the attachment data to be included
    in-line in the XML representation of the attachment.

    returns -- A DOM element node."""

    # Exactly one of 'data' and 'location' should be specified.
    assert data is None or location is None
    assert data is not None or location is not None

    # Create an attachment element.
    node = document.createElement("attachment")
    # Create and add the description node.
    child = xmlutil.create_dom_text_element(document, "description",
                                            attachment.description)
    node.appendChild(child)
    # Create and add the MIME type node.
    child = xmlutil.create_dom_text_element(document, "mimetype",
                                            attachment.mime_type)
    node.appendChild(child)
    # Create and add the file name node.
    child = xmlutil.create_dom_text_element(document, "filename",
                                            attachment.file_name)
    node.appendChild(child)

    if data is not None:
        # 'data' was specified.  Encode the data appropriately.
        encoding, data = common.encode_data_as_text(data, attachment.mime_type)
        # Create a data element.  This contains in-line attachment
        # data. 
        child = xmlutil.create_dom_text_element(document, "data", data)
        # Store the encoding as an attribute.
        child.setAttribute("encoding", encoding)
    else:
        # Create a location element.  This includes attachment data
        # by refernece.
        child = xmlutil.create_dom_text_element(document, "location",
                                                location)
    node.appendChild(child)

    return node


def from_dom_node(node):
    """Construct an attachment object from a DOM element node.

    'node' -- A DOM attachment element node.

    returns -- An attachment instance.  The type is determined by
    'attachment_class'.

    If the attachment object requires additional context information to
    interpret the location (if it's specified in the attachment
    element), the caller must provide it directly to the object."""

    # We'll construct the argument list to the attachment initializer as
    # a map.
    arguments = {}

    # Extract the fixed fields.
    arguments["description"] = xmlutil.get_dom_child_text(node, "description")
    arguments["mime_type"] = xmlutil.get_dom_child_text(node, "mimetype")
    arguments["file_name"] = xmlutil.get_dom_child_text(node, "filename")

    # Extract the data or location elements.
    data_nodes = node.getElementsByTagName("data")
    location_nodes = node.getElementsByTagName("location")
    # Exactly one of the two should be present.
    assert len(data_nodes) + len(location_nodes) == 1
    if len(data_nodes) == 1:
        # The data element is present.  It contains in-line attachment
        # data. 
        data_node = data_nodes[0]
        data = xmlutil.get_dom_text(data_node)
        # Get the scheme used to encode the data.
        encoding = data_node.getAttribute("encoding")
        # Decode the data.
        data = common.decode_data_from_text(data, encoding)
        arguments["data"] = data
    else:
        # The location element is present.  It contains the external
        # location of the attachment data.  Store it unaltered.
        arguments["location"] = xmlutil.get_dom_text(location_nodes[0])

    # Construct the resulting attachment.
    return apply(attachment_class, [], arguments)


########################################################################
# variables
########################################################################

attachment_class = None
"""The attachment class to use.

The program should set this to a class, probably a subclass of
'Attachment'."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

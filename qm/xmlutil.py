########################################################################
#
# File:   xmlutil.py
# Author: Alex Samuel
# Date:   2001-03-18
#
# Contents:
#   Miscellaneous XML-related functions.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import os
import qm
import re
import xml.dom
import xml.dom.minidom

########################################################################
# functions
########################################################################

def make_public_id(name):
    """Return a public ID for the DTD with the given 'name'.

    'name' -- The name of the DTD.

    returns -- A public ID for the DTD."""

    return "-//QM/%s/%s//EN" % (qm.version, name)

    
def make_system_id(name):
    """Return a system ID for the DTD with the given 'name'.

    'name' -- The name of the DTD, as a relative UNIX path.

    returns -- A URL for the DTD."""

    return "http://www.codesourcery.com/qm/dtds/%s/%s" % (qm.version, name)


def load_xml_file(path):
    """Return a DOM document loaded from the XML file 'path'."""

    # Open the file.
    file = open(path, "r")
    return load_xml(file)


def load_xml(file):
    """Return a DOM document loaded from the XML file object 'file'.

    'file' -- A file object, opened for reading.
    
    returns -- The DOM document contained in 'file'.
    
    This function closes 'file', whether or not reading the document was
    successful."""

    try:
        document = xml.dom.minidom.parse(file)
    finally:
        file.close()
    return document


def get_dom_text(node):
    """Return the text contained in DOM 'node'.

    'node' -- A DOM element node.

    prerequisites -- 'node' is an element node with exactly one child,
    which is a text node."""

    assert node.nodeType == xml.dom.Node.ELEMENT_NODE
    # Normalize the node so that multiple TEXT_NODEs are collapsed into
    # a single node.
    node.normalize()
    # If there are no children, the string is empty.
    if len(node.childNodes) == 0:
        return ""
    # If there is a child, there should be only one.
    if len(node.childNodes) != 1:
        raise QMException, "Invalid XML text node."
    child = node.childNodes[0]
    if child.nodeType != xml.dom.Node.TEXT_NODE:
        raise QMException, "Invalid XML text node."
    return child.data


def child_tag_predicate(child_tag):
    """Return a predicate function for finding element nodes by tag.

    returns -- A predicate function that takes a node as its argument
    and returns true if the node is an element node whose tag is
    'child_tag'."""

    return lambda node, tag=child_tag: \
           node.nodeType == xml.dom.Node.ELEMENT_NODE \
           and node.tagName == tag


def get_child(node, child_tag):
    """Return the child element node of 'node' whose tag is 'child_tag'.

    'node' -- A DOM node.  It must have exactly one element child with
    the tag 'child_tag'.

    'child_tag' -- The desired element tag.

    returns -- A child DOM node of 'node'.

    raises -- 'KeyError' if 'node' has no element child with tag
    'child_tag', or more than one.. """

    matching_children = \
        filter(child_tag_predicate(child_tag), node.childNodes)
    if len(matching_children) != 1:
        raise KeyError, child_tag
    return matching_children[0]


def get_child_text(node, child_tag, default=None):
    """Return the text contained in a child of DOM 'node'.

    'child_tag' -- The tag of the child node whose text is to be
    retrieved.

    'default' -- If 'node' has no child element with tag 'child_tag',
    returns 'default', unless 'default' is 'None'.

    raises -- 'KeyError' if 'default' is 'None' and 'node' has no child
    element with tag 'child_tag'."""

    try:
        return get_dom_text(get_child(node, child_tag))
    except KeyError:
        if default is not None:
            return default
        else:
            raise


def get_child_texts(node, child_tag):
    """Return a sequence of text contents of children.

    'node' -- A DOM node.

    returns -- The list containing all child nodes of 'node' which have
    tag 'child_tag'.  Each child must have exactly one child of its own,
    which must be a text node."""

    return map(get_dom_text, node.getElementsByTagName(child_tag))


def create_dom_text_element(document, tag, text):
    """Return a DOM element containing a single text node.

    'document' -- The containing DOM document.

    'tag' -- The element tag.

    'text' -- The text contents of the text node."""

    element = document.createElement(tag)
    if text != "":
        text_node = document.createTextNode(text)
        element.appendChild(text_node)
    else:
        # Don't create a child node in this case.  For some reason, it
        # gets written out with an extraneous newline, and therefore
        # when the text is read in, its no longer an empty string.
        pass
    return element


__dom_implementation = xml.dom.minidom.getDOMImplementation()

def create_dom_document(public_id, document_element_tag):
    """Create a DOM document.

    'public_id' -- The (partial) public ID for the DTD.

    'document_element_tag' -- The tag of the main document element.

    returns -- A DOM document node."""

    public_id = make_public_id(public_id)
    system_id = make_system_id(public_id.lower() + ".dtd")
    # Create the document type for the XML document.
    document_type = __dom_implementation.createDocumentType(
        qualifiedName=document_element_tag,
        publicId=public_id,
        systemId=system_id
        )
    # Create a new DOM document.
    document = __dom_implementation.\
                    createDocument(namespaceURI=None,
                                   qualifiedName=document_element_tag,
                                   doctype=document_type)
    return document


__hyphen_regex = re.compile("(--+)")

def __hyphen_replacement(match):
    return "-" + " -" * (len(match.group(0)) - 1)


def sanitize_text_for_comment(text):
    """Return 'text' modified so that it is valid for an XML comment."""

    # A comment cannot contain two or more hyphens in a row.
    text = __hyphen_regex.sub(__hyphen_replacement, text)

    return text


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   xmlutil.py
# Author: Alex Samuel
# Date:   2001-03-18
#
# Contents:
#   Miscellaneous XML-related functions.
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

import os
import qm
import re
import xml.dom
import xml.dom.ext 
import xml.dom.ext.reader.Sax
import xml.dom.DOMImplementation

########################################################################
# exceptions
########################################################################

class ParseError(Exception):
    pass

    

########################################################################
# functions
########################################################################

def make_system_id(name):
    """Construct a system ID for the file 'name'."""

    return "http://www.software-carpentry.com/qm/xml/%s" % name


def load_xml_file(path):
    """Return a DOM document loaded from the XML file 'path'.

    raises -- 'ParseError' if an error occurs while parsing the file.
    This may occur if the file is either not well-formed or not
    valid."""

    # Open the file.
    try:
        file = open(path, "r")
    except:
        # FIXME.  Any errors that need to be handled here?
        raise
    else:
        return load_xml(file, whence=path)


def load_xml(file, whence="(input)"):
    """Return a DOM document loaded from the XML file object 'file'.

    'file' -- A file object from which to read XML.

    'whence' -- Where the XML came from (e.g. a file path), for use in
    diagnostic messages.

    raises -- 'ParseError' if an error occurs while parsing the file.
    This may occur if the file is either not well-formed or not
    valid."""

    # Construct the path to the DTD catalog.
    catalog_path = os.path.join(qm.get_share_directory(),
                                "xml", "CATALOG")
    # Create a validating DOM reader.
    reader = xml.dom.ext.reader.Sax.Reader(validate=1, catName=catalog_path)
    try:
        # Read and parse XML.
        document = reader.fromStream(file)
    except xml.sax._exceptions.SAXParseException, exception:
        raise ParseError, qm.error("xml parse error",
                                   line=exception.getLineNumber(),
                                   character=exception.getColumnNumber(),
                                   file_name=whence,
                                   message=exception._msg)
    file.close()
    return document


def get_dom_text(node):
    """Return the text contained in DOM 'node'.

    'node' -- A DOM element node.

    prerequisites -- 'node' is an element node with exactly one child,
    which is a text node."""

    assert node.nodeType == xml.dom.Node.ELEMENT_NODE
    if len(node.childNodes) == 0:
        # Missing the text node; assume it's empty.
        return ""
    assert len(node.childNodes) == 1
    child = node.childNodes[0]
    assert child.nodeType == xml.dom.Node.TEXT_NODE
    return child.data


def get_dom_child_text(node, child_tag):
    """Return the text contained in a child of DOM 'node'.

    'child_tag' -- The tag of the child node whose text is to be
    retrieved.

    prerequisites -- 'node' is an element node with exactly one child
    with the tag 'child_tag'.  That child has exactly one child, which
    is a text node."""

    assert node.nodeType == xml.dom.Node.ELEMENT_NODE
    children = node.getElementsByTagName(child_tag)
    assert len(children) == 1
    return get_dom_text(children[0])


def get_dom_children_texts(node, child_tag):
    """Return a sequence of text contents of children.

    'node' -- A DOM node.

    returns -- The list containing all child nodes of 'node' which have
    tag 'child_tag'.  Each child must have exactly one child of its own,
    which must be a text node."""

    results = []
    for child_node in node.getElementsByTagName(child_tag):
        text = get_dom_text(child_node)
        results.append(text)
    return results


def create_dom_text_element(document, tag, text):
    """Return a DOM element containing a single text node.

    'document' -- The containing DOM document node.

    'tag' -- The element tag.

    'text' -- The text contents of the text node."""

    element = document.createElement(tag)
    text_node = document.createTextNode(text)
    element.appendChild(text_node)
    return element


__dom_implementation = xml.dom.DOMImplementation.DOMImplementation()

def create_dom_document(public_id, dtd_file_name, document_element_tag):
    """Create a DOM document.

    'public_id' -- The public ID of the DTD to use for this document.

    'dtd_file_name' -- The name of the DTD file for this document.

    'document_element_tag' -- The tag of the main document element.

    returns -- A DOM document node."""

    system_id = make_system_id(dtd_file_name)
    # Create the document type for the XML document.
    document_type = __dom_implementation.createDocumentType(
        qualifiedName=document_element_tag,
        publicId=public_id,
        systemId=system_id
        )
    # Create a new DOM document.
    return __dom_implementation.createDocument(
        namespaceURI=None,
        qualifiedName=document_element_tag,
        doctype=document_type
        )
    

def write_dom_document(document, stream):
    """Write a DOM document.

    'document' -- A DOM document node.

    'stream' -- A file object."""

    xml.dom.ext.PrettyPrint(document,
                            stream=stream,
                            indent=" ",
                            encoding="ISO-8859-1")


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

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

import xml.dom
import xml.dom.ext 
import xml.dom.DOMImplementation

########################################################################
# classes
########################################################################

# Place class definitions here.

########################################################################
# functions
########################################################################

def get_dom_text(node):
    """Return the text contained in DOM 'node'.

    'node' -- A DOM element node.

    prerequisites -- 'node' is an element node with exactly one child,
    which is a text node."""

    assert node.nodeType == xml.dom.Node.ELEMENT_NODE
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

    returns -- The text contained in all child nodes of 'node' which
    have tag 'child_tag'.  Each child must have exactly one child of its
    own, which must be a text node."""

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

def create_dom_document(public_id, system_id, document_element_tag):
    """Create a DOM document.

    'public_id' -- The public ID of the DTD to use for this document.

    'system_id' -- The system ID of the DTD to use for this document.

    'document_element_tag' -- The tag of the main document element.

    returns -- A DOM document node."""

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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

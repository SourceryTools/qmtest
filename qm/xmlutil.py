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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

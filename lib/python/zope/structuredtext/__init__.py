##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Consider the following example::

  >>> from structuredtext.stng import structurize
  >>> from structuredtext.document import DocumentWithImages
  >>> from structuredtext.html import HTMLWithImages
  >>> from structuredtext.docbook import DocBook

  We first need to structurize the string and make a full-blown
  document out of it:

  >>> struct = structurize(structured_string)
  >>> doc = DocumentWithImages()(struct)

  Now feed it to some output generator, in this case HTML or DocBook:
  
  >>> output = HTMLWithImages()(doc, level=1)
  >>> output = DocBook()(doc, level=1)

$Id: __init__.py 67724 2006-04-28 16:52:39Z jim $
"""
__docformat__ = 'restructuredtext'

import re
from zope.structuredtext import stng, document, html
from string import letters

def stx2html(aStructuredString, level=1, header=1):
    st = stng.structurize(aStructuredString)
    doc = document.DocumentWithImages()(st)
    return html.HTMLWithImages()(doc, header=header, level=level)

def stx2htmlWithReferences(text, level=1, header=1):
    text = re.sub(
        r'[\000\n]\.\. \[([0-9_%s-]+)\]' % letters,
        r'\n  <a name="\1">[\1]</a>',
        text)

    text = re.sub(
        r'([\000- ,])\[(?P<ref>[0-9_%s-]+)\]([\000- ,.:])'   % letters,
        r'\1<a href="#\2">[\2]</a>\3',
        text)

    text = re.sub(
        r'([\000- ,])\[([^]]+)\.html\]([\000- ,.:])',
        r'\1<a href="\2.html">[\2]</a>\3',
        text)

    return stx2html(text, level=level, header=header)

##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Structured Text Renderer Classes

$Id: stx.py 67630 2006-04-27 00:54:03Z jim $
"""
import re

from zope.interface import implements
from zope.structuredtext.document import Document
from zope.structuredtext.html import HTML
from zope.publisher.browser import BrowserView

from zope.app.i18n import ZopeMessageFactory as _
from zope.app.renderer.interfaces import ISource, IHTMLRenderer
from zope.app.renderer import SourceFactory


class IStructuredTextSource(ISource):
    """Marker interface for a structured text source. Note that an
    implementation of this interface should always derive from unicode or
    behave like a unicode class."""

StructuredTextSourceFactory = SourceFactory(
    IStructuredTextSource, _("Structured Text (STX)"),
    _("Structured Text (STX) Source"))


class StructuredTextToHTMLRenderer(BrowserView):
    r"""A view to convert from Plain Text to HTML.

    Example::

      >>> from zope.publisher.browser import TestRequest
      >>> source = StructuredTextSourceFactory(u'This is source.')
      >>> renderer = StructuredTextToHTMLRenderer(source, TestRequest())
      >>> renderer.render()
      u'<p>This is source.</p>\n'

      Make sure that unicode works as well.

      >>> source = StructuredTextSourceFactory(u'This is \xc3\x9c.')
      >>> renderer = StructuredTextToHTMLRenderer(source, TestRequest())
      >>> renderer.render()
      u'<p>This is \xc3\x9c.</p>\n'
    """ 
    implements(IHTMLRenderer)
    __used_for__ = IStructuredTextSource

    def render(self):
        "See zope.app.interfaces.renderer.IHTMLRenderer"
        encoded = self.context.encode('UTF-8')
        doc = Document()(encoded)
        html = HTML()(doc)

        # strip html & body added by some zope versions
        html = re.sub(
            r'(?sm)^<html.*<body.*?>\n(.*)</body>\n</html>\n',r'\1', html)

        return html.decode('UTF-8')

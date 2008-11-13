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
"""Plain Text Renderer Classes

$Id: plaintext.py 80175 2007-09-27 00:02:00Z mgedmin $
"""
__docformat__ = 'restructuredtext'

import cgi

from zope.interface import implements
from zope.publisher.browser import BrowserView

from zope.app.renderer.i18n import ZopeMessageFactory as _
from zope.app.renderer.interfaces import ISource, IHTMLRenderer
from zope.app.renderer import SourceFactory

class IPlainTextSource(ISource):
    """Marker interface for a plain text source. Note that an implementation
    of this interface should always derive from unicode or behave like a
    unicode class."""

PlainTextSourceFactory = SourceFactory(
    IPlainTextSource, _("Plain Text"), _("Plain Text Source"))


class PlainTextToHTMLRenderer(BrowserView):
    r"""A view to convert from Plain Text to HTML.

    Example::

      >>> from zope.publisher.browser import TestRequest
      >>> source = PlainTextSourceFactory(u'I hear that 1 > 2.\n')
      >>> renderer = PlainTextToHTMLRenderer(source, TestRequest())
      >>> renderer.render()
      u'I hear that 1 &gt; 2.<br />\n'
    """
    implements(IHTMLRenderer)
    __used_for__ = IPlainTextSource

    def render(self):
        "See zope.app.interfaces.renderer.IHTMLRenderer"
        return cgi.escape(self.context).replace('\n', '<br />\n')

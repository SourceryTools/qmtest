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
"""ReStructured Text Renderer Classes

$Id: rest.py 73674 2007-03-27 07:52:12Z dobe $
"""
__docformat__ = 'restructuredtext'

import docutils.core
from docutils.writers.html4css1 import HTMLTranslator
from docutils.writers.html4css1 import Writer

from zope.interface import implements
from zope.publisher.browser import BrowserView

from zope.app.renderer.i18n import ZopeMessageFactory as _
from zope.app.renderer.interfaces import ISource, IHTMLRenderer
from zope.app.renderer import SourceFactory


class IReStructuredTextSource(ISource):
    """Marker interface for a restructured text source. Note that an
    implementation of this interface should always derive from unicode or
    behave like a unicode class."""


ReStructuredTextSourceFactory = SourceFactory(
    IReStructuredTextSource, _("ReStructured Text (ReST)"),
    _("ReStructured Text (ReST) Source"))


class ZopeTranslator(HTMLTranslator):
    """
    The ZopeTranslator extends the base HTML processor for reST.  It
    augments reST by:

    - Outputs *only* the 'body' parts of the document tree, using the
      internal docutils structure.
    """

    def astext(self):
        """
        This is where we join the document parts that we want in
        the output.
        """
        # use the title, subtitle, author, date, etc., plus the content
        body = self.body_pre_docinfo + self.docinfo + self.body
        return u"".join(body)


class ReStructuredTextToHTMLRenderer(BrowserView):
    r"""An Adapter to convert from Restructured Text to HTML.

    Examples::

      >>> from zope.publisher.browser import TestRequest
      >>> source = ReStructuredTextSourceFactory(u'''
      ... This is source.
      ...
      ... Header 3
      ... --------
      ... This is more source.
      ... ''')
      >>> renderer = ReStructuredTextToHTMLRenderer(source, TestRequest())
      >>> print renderer.render().strip()
      <p>This is source.</p>
      <div class="section">
      <h3><a id="header-3" name="header-3">Header 3</a></h3>
      <p>This is more source.</p>
      </div>
    """


    implements(IHTMLRenderer)
    __used_for__ = IReStructuredTextSource

    def render(self, settings_overrides={}):
        """See zope.app.interfaces.renderer.IHTMLRenderer

        Let's make sure that inputted unicode stays as unicode:

        >>> renderer = ReStructuredTextToHTMLRenderer(u'b\xc3h', None)
        >>> repr(renderer.render())
        "u'<p>b\\\\xc3h</p>\\\\n'"
        
        >>> text = u'''
        ... =========
        ... Heading 1
        ... =========
        ...
        ... hello world
        ...
        ... Heading 2
        ... ========='''
        >>> overrides = {'initial_header_level': 2, 
        ...              'doctitle_xform': 0 }
        >>> renderer = ReStructuredTextToHTMLRenderer(text, None)
        >>> print renderer.render(overrides)
        <div class="section">
        <h2><a id="heading-1" name="heading-1">Heading 1</a></h2>
        <p>hello world</p>
        <div class="section">
        <h3><a id="heading-2" name="heading-2">Heading 2</a></h3>
        </div>
        </div>
        <BLANKLINE>
        """
        # default settings for the renderer
        overrides = {
            'halt_level': 6,
            'input_encoding': 'unicode',
            'output_encoding': 'unicode',
            'initial_header_level': 3,
            }
        overrides.update(settings_overrides)
        writer = Writer()
        writer.translator_class = ZopeTranslator
        html = docutils.core.publish_string(
            self.context,
            writer=writer,
            settings_overrides=overrides,
            )
        return html

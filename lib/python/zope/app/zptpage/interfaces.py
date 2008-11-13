##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""ZPT Page Content Component Interfaces

$Id: interfaces.py 73726 2007-03-27 13:04:40Z dobe $
"""
from zope.schema import SourceText, Bool, TextLine
from zope.interface import Interface
from zope.app.zptpage.i18n import ZopeMessageFactory as _

class IZPTPage(Interface):
    """ZPT Pages are a persistent implementation of Page Templates."""


    def setSource(text, content_type='text/html'):
        """Save the source of the page template.

        'text' must be Unicode.
        """

    def getSource():
        """Get the source of the page template."""

    source = SourceText(
        title=_("Source"),
        description=_("The source of the page template."),
        required=True)

    expand = Bool(
        title=_("Expand macros when editing"),
        description=_("Expand macros so that they all are shown in the "
                      "code."),
        default=False,
        required=True)

    evaluateInlineCode = Bool(
        title=_("Evaluate Inline Code"),
        description=_("Evaluate code snippets in TAL. We usually discourage "
                      "people from using this feature."),
        default=False,
        required=True)


class IRenderZPTPage(Interface):

    content_type = TextLine(
        title=_("Content Type"),
        description=_("Content type of generated output"),
        default=u"text/html",
        required=True)

    def render(request, *args, **kw):
        """Render the page template.

        The first argument is bound to the top-level 'request'
        variable. The positional arguments are bound to the 'args'
        variable and the keyword arguments are bound to the 'options'
        variable.
        """


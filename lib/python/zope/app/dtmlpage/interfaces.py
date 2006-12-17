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
"""DTML Page content component interfaces

$Id: interfaces.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

import zope.schema
from zope.interface import Interface, Attribute
from zope.app.i18n import ZopeMessageFactory as _

class IDTMLPage(Interface):
    """DTML Pages are a persistent implementation of DTML."""

    def setSource(text, content_type='text/html'):
        """Save the source of the page template."""

    def getSource():
        """Get the source of the page template."""

    source = zope.schema.Text(
        title=_(u"Source"),
        description=_(u"""The source of the dtml page."""),
        required=True)


class IRenderDTMLPage(Interface):

    content_type = Attribute('Content type of generated output')

    def render(request, *args, **kw):
        """Render the page template.

        The first argument is bound to the top-level `request`
        variable. The positional arguments are bound to the `args`
        variable and the keyword arguments are bound to the `kw`
        variable.
        """

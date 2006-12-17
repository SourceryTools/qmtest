##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Function Views

$Id: browser.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.component import getUtility
from zope.traversing.api import getParent
from zope.traversing.browser import absoluteURL

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import renderText

from class_ import getTypeLink

class FunctionDetails(object):
    """Represents the details of the function."""

    def getDocString(self):
        """Get the doc string of the function in a rendered format."""
        return renderText(self.context.getDocString() or '',
                          getParent(self.context).getPath())


    def getAttributes(self):
        """Get all attributes of this function."""
        return [{'name': name,
                 'value': `attr`,
                 'type': type(attr).__name__,
                 'type_link': getTypeLink(type(attr))}

                for name, attr in self.context.getAttributes()]


    def getBaseURL(self):
        """Return the URL for the API Documentation Tool."""
        m = getUtility(IDocumentationModule, "Code")
        return absoluteURL(getParent(m), self.request)

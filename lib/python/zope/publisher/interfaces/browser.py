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
"""Browser Interfaces

$Id: browser.py 70896 2006-10-23 21:06:10Z ctheune $
"""

__docformat__ = "reStructuredText"

from zope.interface import Interface, Attribute, directlyProvides
from zope.interface.interfaces import IInterface
from zope.component.interfaces import IView

from zope.publisher.interfaces import IPublication
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces.http import IHTTPApplicationRequest
from zope.publisher.interfaces.http import IHTTPRequest

class IBrowserApplicationRequest(IHTTPApplicationRequest):
    """Browser-specific requests
    """

    def __getitem__(key):
        """Return Browser request data

        Request data are retrieved from one of:

        - Environment variables

          These variables include input headers, server data, and other
          request-related data.  The variable names are as <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
          in the <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
          specification</a>

        - Cookies

          These are the cookie data, if present.

        - Form data

        Form data are searched before cookies, which are searched
        before environmental data.
        """

    form = Attribute(
        """Form data

        This is a read-only mapping from name to form value for the name.
        """)


class IBrowserPublication(IPublication):
    """Object publication framework.
    """

    def getDefaultTraversal(request, ob):
        """Get the default published object for the request

        Allows a default view to be added to traversal.
        Returns (ob, steps_reversed).
        """


class IBrowserRequest(IHTTPRequest):
    """Browser-specific Request functionality.

    Note that the browser is special in many ways, since it exposes
    the Request object to the end-developer.
    """


class IBrowserPublisher(IPublishTraverse):

    def browserDefault(request):
        """Provide the default object

        The default object is expressed as a (possibly different)
        object and/or additional traversal steps.

        Returns an object and a sequence of names.  If the sequence of
        names is not empty, then a traversal step is made for each name.
        After the publisher gets to the end of the sequence, it will
        call browserDefault on the last traversed object.

        Normal usage is to return self for object and a default view name.

        The publisher calls this method at the end of each traversal path. If
        a non-empty sequence of names is returned, the publisher will traverse
        those names and call browserDefault again at the end.

        Note that if additional traversal steps are indicated (via a
        nonempty sequence of names), then the publisher will try to adjust
        the base href.
        """

class IBrowserPage(IBrowserPublisher):
    """Browser page"""

    def __call__(*args, **kw):
        """Compute a response body"""

class IBrowserView(IView):
    """Browser View"""

class IDefaultBrowserLayer(IBrowserRequest):
    """The default layer."""

class IBrowserSkinType(IInterface):
    """A skin is a set of layers."""

##############################################################################
#
# BBB 2006/02/18, to be removed after 12 months
#

# mark the default layer for BBB reasons
from zope.publisher.interfaces.back35 import ILayer
directlyProvides(IDefaultBrowserLayer, ILayer)

import zope.deprecation
ISkin = IBrowserSkinType
zope.deprecation.deprecated('ISkin',
                            'The zope.publisher.interfaces.browser.ISkin '
                            'interface has been renamed to IBrowserSkinType. '
                            'The old alias will go away in Zope 3.5.')
#
##############################################################################

class IDefaultSkin(Interface):
    """Any component providing this interface must be a skin.

    This is a marker interface, so that we can register the default skin as an
    adapter from the presentation type to `IDefaultSkin`.
    """

class ISkinChangedEvent(Interface):
    """Event that gets triggered when the skin of a request is changed."""

    request = Attribute("The request for which the skin was changed.")

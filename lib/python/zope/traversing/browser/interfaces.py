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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Browser traversal interfaces

$Id: interfaces.py 25219 2004-06-03 05:10:47Z BjornT $
"""
from zope.interface import Interface

class IAbsoluteURL(Interface):

    def __unicode__():
        """Returns the URL as a unicode string."""

    def __str__():
        """Returns an ASCII string with all unicode characters url quoted."""

    def __repr__():
        """Get a string representation """

    def __call__():
        """Returns an ASCII string with all unicode characters url quoted."""

    def breadcrumbs():
        """Returns a tuple like ({'name':name, 'url':url}, ...)

        Name is the name to display for that segment of the breadcrumbs.
        URL is the link for that segment of the breadcrumbs.
        """

class IAbsoluteURLAPI(Interface):

    def absoluteURL(ob, request):
        """Compute the absolute URL of an object """

##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Browser Resource

$Id: resource.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.component import getMultiAdapter
from zope.component.interfaces import IResource
from zope.interface import implements
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.location import Location

from zope.app.component.hooks import getSite

class Resource(Location):
    implements(IResource)

    def __init__(self, request):
        self.request = request

    def __call__(self):
        name = self.__name__
        if name.startswith('++resource++'):
            name = name[12:]

        site = getSite()
        url = str(getMultiAdapter((site, self.request), IAbsoluteURL))
        return "%s/@@/%s" % (url, name)

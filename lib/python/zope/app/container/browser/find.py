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
"""Find View Class

$Id: find.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.traversing.api import getName
from zope.traversing.browser.absoluteurl import absoluteURL
from zope.publisher.browser import BrowserView

from zope.app.container.find import SimpleIdFindFilter
from zope.app.container.interfaces import IFind

# Very simple implementation right now
class Find(BrowserView):

    def findByIds(self, ids):
        """Do a find for the `ids` listed in `ids`, which is a string."""
        finder = IFind(self.context)
        ids = ids.split()
        # if we don't have any ids listed, don't search at all
        if not ids:
            return []
        request = self.request
        result = []
        for object in finder.find([SimpleIdFindFilter(ids)]):
            url = absoluteURL(object, request)
            result.append({ 'id': getName(object), 'url': url})
        return result

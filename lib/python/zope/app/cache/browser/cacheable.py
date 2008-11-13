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
"""Management view for binding caches to content objects.

$Id: cacheable.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserView
from zope.annotation.interfaces import IAnnotatable

from zope.app.cache.caching import getCacheForObject, getLocationForCache
from zope.app.form.utility import setUpEditWidgets
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.cache.interfaces import ICacheable
from zope.app.form.interfaces import WidgetInputError
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

class CacheableView(BrowserView):

    __used_for__ = IAnnotatable

    form = ViewPageTemplateFile("cacheableedit.pt")

    def __init__(self, *args):
        super(CacheableView, self).__init__(*args)
        self.cacheable = ICacheable(self.context)
        setUpEditWidgets(self, ICacheable, self.cacheable)

    def current_cache_id(self):
        "Returns the current cache ID."
        return self.cacheable.getCacheId()

    def current_cache_url(self):
        "Returns the current cache provider's URL."
        cache = getCacheForObject(self.context)
        absolute_url = getMultiAdapter((cache, self.request),
                                       name='absolute_url')
        try:
            return absolute_url()
        except TypeError:
            # In case the cache object is a global one and does not have a
            # location, then we just return None. 
            return None

    def invalidate(self):
        "Invalidate the current cached value."

        cache = getCacheForObject(self.context)
        location = getLocationForCache(self.context)
        if cache and location:
            cache.invalidate(location)
            return self.form(message=_("cache-invalidated", u"Invalidated."))
        else:
            return self.form(message=_("no-cache-associated",
                                       u"No cache associated with object."))

    def action(self):
        "Change the cacheId"
        try:
            cacheId = self.cacheId_widget.getInputValue()
        except WidgetInputError, e:
            #return self.form(errors=e.errors)
            return repr(e.errors)
        else:
            self.cacheable.setCacheId(cacheId)
            return self.form(message=_(u"Saved changes."))

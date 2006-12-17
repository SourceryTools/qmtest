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
"""Absolute URL View components

$Id: absoluteurl.py 66592 2006-04-06 15:53:30Z philikon $
"""
import urllib
import zope.component
from zope.interface import implements
from zope.proxy import sameProxiedObjects
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import BrowserView
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

_insufficientContext = _("There isn't enough context to get URL information. "
                       "This is probably due to a bug in setting up location "
                       "information.")

_safe = '@+' # Characters that we don't want to have quoted

def absoluteURL(ob, request):
    return zope.component.getMultiAdapter((ob, request), IAbsoluteURL)()

class AbsoluteURL(BrowserView):
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        context = self.context
        request = self.request

        # The application URL contains all the namespaces that are at the
        # beginning of the URL, such as skins, virtual host specifications and
        # so on.
        if (context is None
            or sameProxiedObjects(context, request.getVirtualHostRoot())):
            return request.getApplicationURL()

        container = getattr(context, '__parent__', None)
        if container is None:
            raise TypeError(_insufficientContext)

        url = str(zope.component.getMultiAdapter((container, request),
                                                 name='absolute_url'))
        name = self._getContextName(context)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            url += '/' + urllib.quote(name.encode('utf-8'), _safe)

        return url

    __call__ = __str__

    def _getContextName(self, context):
        return getattr(context, '__name__', None)

    def breadcrumbs(self):
        context = self.context
        request = self.request

        # We do this here do maintain the rule that we must be wrapped
        container = getattr(context, '__parent__', None)
        if container is None:
            raise TypeError(_insufficientContext)

        if sameProxiedObjects(context, request.getVirtualHostRoot()) or \
               isinstance(context, Exception):
            return ({'name':'', 'url': self.request.getApplicationURL()}, )

        base = tuple(zope.component.getMultiAdapter(
                (container, request), name='absolute_url').breadcrumbs())

        name = getattr(context, '__name__', None)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            base += ({'name': name,
                      'url': ("%s/%s" % (base[-1]['url'],
                                         urllib.quote(name.encode('utf-8'),
                                                      _safe)))
                      }, )

        return base

class SiteAbsoluteURL(BrowserView):
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        context = self.context
        request = self.request

        if sameProxiedObjects(context, request.getVirtualHostRoot()):
            return request.getApplicationURL()

        url = request.getApplicationURL()
        name = getattr(context, '__name__', None)
        if name:
            url += '/' + urllib.quote(name.encode('utf-8'), _safe)

        return url

    __call__ = __str__

    def breadcrumbs(self):
        context = self.context
        request = self.request

        if sameProxiedObjects(context, request.getVirtualHostRoot()):
            return ({'name':'', 'url': self.request.getApplicationURL()}, )

        base = ({'name':'', 'url': self.request.getApplicationURL()}, )

        name = getattr(context, '__name__', None)
        if name:
            base += ({'name': name,
                      'url': ("%s/%s" % (base[-1]['url'],
                                         urllib.quote(name.encode('utf-8'),
                                                      _safe)))
                      }, )

        return base

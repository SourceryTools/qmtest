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
"""Traversal components for containers

$Id: traversal.py 68737 2006-06-18 22:49:03Z ctheune $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.component import queryMultiAdapter
from zope.traversing.interfaces import TraversalError, ITraversable
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.xmlrpc import IXMLRPCPublisher
from zope.publisher.interfaces import NotFound

from zope.app import zapi
from zope.app.container.interfaces import ISimpleReadContainer, IItemContainer
from zope.app.container.interfaces import IReadContainer

# Note that the next two classes are included here because they
# can be used for multiple view types.

class ContainerTraverser(object):
    """A traverser that knows how to look up objects by name in a container."""

    implements(IBrowserPublisher, IXMLRPCPublisher)
    __used_for__ = ISimpleReadContainer

    def __init__(self, container, request):
        self.context = container
        self.request = request

    def publishTraverse(self, request, name):
        """See zope.publisher.interfaces.IPublishTraverse"""
        subob = self.context.get(name, None)
        if subob is None:
            view = queryMultiAdapter((self.context, request), name=name)
            if view is not None:
                return view

            raise NotFound(self.context, name, request)

        return subob

    def browserDefault(self, request):
        """See zope.publisher.browser.interfaces.IBrowserPublisher"""
        view_name = zapi.getDefaultViewName(self.context, request)
        view_uri = "@@%s" %view_name
        return self.context, (view_uri,)


class ItemTraverser(ContainerTraverser):
    """A traverser that knows how to look up objects by name in an item
    container."""

    __used_for__ = IItemContainer

    def publishTraverse(self, request, name):
        """See zope.publisher.interfaces.IPublishTraverse"""
        try:
            return self.context[name]
        except KeyError:
            view = queryMultiAdapter((self.context, request), name=name)
            if view is not None:
                return view

        raise NotFound(self.context, name, request)


_marker = object()

class ContainerTraversable(object):
    """Traverses containers via `getattr` and `get`."""

    implements(ITraversable)
    __used_for__ = IReadContainer

    def __init__(self, container):
        self._container = container


    def traverse(self, name, furtherPath):
        container = self._container

        v = container.get(name, _marker)
        if v is _marker:
            v = getattr(container, name, _marker)
            if v is _marker:
                raise TraversalError(container, name)

        return v

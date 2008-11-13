##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""HTTP-specific traversers

For straight HTTP, we need to be able to create null resources.
We also never traverse to views.

$Id: traversal.py 28261 2004-10-26 22:22:37Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.publisher.interfaces.http import IHTTPPublisher
from zope.app.container.interfaces import ISimpleReadContainer, IItemContainer
from zope.app.http.put import NullResource
from zope.publisher.interfaces import NotFound
from zope.interface import implements

class ContainerTraverser(object):
    implements(IHTTPPublisher)
    __used_for__ = ISimpleReadContainer

    def __init__(self, container, request):
        self.context = container
        self.request = request

    def publishTraverse(self, request, name):
        subob = self.context.get(name, None)
        if subob is None:
            subob = self.nullResource(request, name)

        return subob

    def nullResource(self, request, name):
        # we traversed to something that doesn't exist.

        # The name must be the last name in the path, so the traversal
        # name stack better be empty:
        if request.getTraversalStack():
            raise NotFound(self.context, name, request)

        # This should only happen for a PUT or MKCOL:
        if request.method not in  ['PUT', 'MKCOL']:
            raise NotFound(self.context, name, request)

        return NullResource(self.context, name)

class ItemTraverser(ContainerTraverser):
    __used_for__ = IItemContainer

    def publishTraverse(self, request, name):
        context = self.context

        try:
            return context[name]
        except KeyError:
            return self.nullResource(request, name)

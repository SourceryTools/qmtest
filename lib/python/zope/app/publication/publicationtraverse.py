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
"""Publication Traverser

$Id: publicationtraverse.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'
from types import StringTypes

from zope.component import queryMultiAdapter
from zope.publisher.interfaces import NotFound
from zope.security.checker import ProxyFactory
from zope.traversing.namespace import namespaceLookup
from zope.traversing.namespace import nsParse
from zope.traversing.interfaces import TraversalError
from zope.publisher.interfaces import IPublishTraverse

class DuplicateNamespaces(Exception):
    """More than one namespace was specified in a request"""

class UnknownNamespace(Exception):
    """A parameter specified an unknown namespace"""

class PublicationTraverse(object):

    def traverseName(self, request, ob, name):
        nm = name # the name to look up the object with

        if name and name[:1] in '@+':
            # Process URI segment parameters.
            ns, nm = nsParse(name)
            if ns:
                try:
                    ob2 = namespaceLookup(ns, nm, ob, request)
                except TraversalError:
                    raise NotFound(ob, name)

                return ProxyFactory(ob2)

        if nm == '.':
            return ob

        if IPublishTraverse.providedBy(ob):
            ob2 = ob.publishTraverse(request, nm)
        else:
            # self is marker
            adapter = queryMultiAdapter((ob, request), IPublishTraverse,
                                        default=self)
            if adapter is not self:
                ob2 = adapter.publishTraverse(request, nm)
            else:
                raise NotFound(ob, name, request)

        return ProxyFactory(ob2)

class PublicationTraverser(PublicationTraverse):

    def traversePath(self, request, ob, path):

        if isinstance(path, StringTypes):
            path = path.split('/')
            if len(path) > 1 and not path[-1]:
                # Remove trailing slash
                path.pop()
        else:
            path = list(path)

        # Remove single dots
        path = [x for x in path if x != '.']

        path.reverse()

        # Remove double dots
        while '..' in path:
            l = path.index('..')
            if l < 0 or l+2 > len(path):
                break
            del path[l:l+2]

        pop = path.pop

        while path:
            name = pop()
            ob = self.traverseName(request, ob, name)

        return ob

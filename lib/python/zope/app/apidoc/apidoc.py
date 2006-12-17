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
"""Zope 3 API Documentation

$Id: apidoc.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.component
from zope.interface import implements
from zope.publisher.browser import applySkin
from zope.location import locate
from zope.location.interfaces import ILocation

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase

class APIDocumentation(ReadContainerBase):
    """Represent the complete API Documentation.

    This documentation is implemented using a simply `IReadContainer`. The
    items of the container are all registered utilities for
    `IDocumentationModule`.
    """
    implements(ILocation)

    def __init__(self, parent, name):
        self.__parent__ = parent
        self.__name__ = name

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer"""
        utility = zope.component.queryUtility(IDocumentationModule, key, default)
        if utility != default:
            locate(utility, self, key)
        return utility

    def items(self):
        """See zope.app.container.interfaces.IReadContainer"""
        items = list(zope.component.getUtilitiesFor(IDocumentationModule))
        items.sort()
        utils = []
        for key, value in items:
            locate(value, self, key)
            utils.append((key, value))
        return utils


class apidocNamespace(object):
    """Used to traverse to an API Documentation."""
    def __init__(self, ob, request=None):
        if request:
            from zope.app.apidoc.browser.skin import APIDOC
            applySkin(request, APIDOC)
        self.context = ob

    def traverse(self, name, ignore):
        return handleNamespace(self.context, name)

def handleNamespace(ob, name):
    """Used to traverse to an API Documentation."""
    return APIDocumentation(ob, '++apidoc++'+name)

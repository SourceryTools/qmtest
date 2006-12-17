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
"""Object adapters

This module contains adapters necessary to use common objects with
statictree. The most prominent ones are those for ILocation and
IContainer. We also provide adapters for any object, so we don't end
up with ComponentLookupErrors whenever encounter unknown objects.

$Id: adapters.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.interface import Interface, implements
from zope.component.interfaces import ComponentLookupError
from zope.security import canAccess
from zope.security.interfaces import Unauthorized
from zope.location.interfaces import ILocation

from zope.app import zapi
from zope.app.container.interfaces import IReadContainer
from zope.app.component.interfaces import ISite

from zope.app.tree.interfaces import IUniqueId, IChildObjects

class StubUniqueId(object):
    implements(IUniqueId)
    __used_for__ = Interface

    def __init__(self, context):
        self.context = context

    def getId(self):
        # this does not work for persistent objects
        return str(id(self.context))

class StubChildObjects(object):
    implements(IChildObjects)
    __used_for__ = Interface

    def __init__(self, context):
        pass

    def hasChildren(self):
        return False

    def getChildObjects(self):
        return []

class LocationUniqueId(object):
    implements(IUniqueId)
    __used_for__ = ILocation

    def __init__(self, context):
        self.context = context

    def getId(self):
        context = self.context
        if not context.__name__:
            # always try to be unique
            return str(id(context))
        parents = [context.__name__]
        parents += [parent.__name__ for parent in zapi.getParents(context)
                    if parent.__name__]
        return '\\'.join(parents)

class ContainerChildObjects(object):
    implements(IChildObjects)
    __used_for__ = IReadContainer

    def __init__(self, context):
        self.context = context

    def hasChildren(self):
        # make sure we check for access
        try:
            lenght = bool(len(self.context))
            if lenght > 0:
                return True
            else:
                return False
        except Unauthorized:
            return False

    def getChildObjects(self):
        if self.hasChildren():
            return self.context.values()
        else:
            return []

class ContainerSiteChildObjects(ContainerChildObjects):
    """Adapter for read containers which are sites as well. The site
    manager will be treated as just another child object.
    """
    __used_for__ = ISite

    def hasChildren(self):
        if super(ContainerSiteChildObjects, self).hasChildren():
            return True
        if self._canAccessSiteManager():
            return True
        else:
            return False

    def getChildObjects(self):
        if self.hasChildren():
            values = super(ContainerSiteChildObjects, self).getChildObjects()
            if self._canAccessSiteManager():
                return [self.context.getSiteManager()] + list(values)
            else:
                return values
        else:
            return []

    def _canAccessSiteManager(self):
        try:
            # the ++etc++ namespace is public this means we get the sitemanager
            # without permissions. But this does not mean we can access it
            # Right now we check the __getitem__ method on the sitemamanger
            # but this means we don't show the ++etc++site link if we have
            # registred views on the sitemanager which have other permission
            # then the __getitem__ method form the interface IReadContainer
            # in the LocalSiteManager.
            # If this will be a problem in the future, we can add a 
            # attribute to the SiteManager which we can give individual 
            # permissions and check it via canAccess.
            sitemanager = self.context.getSiteManager()
            authorized = canAccess(sitemanager, '__getitem__')
            if authorized:
                return True
            else:
                return False
        except ComponentLookupError:
            return False
        except TypeError:
            # we can't check unproxied objects, but unproxied objects
            # are public.
            return True

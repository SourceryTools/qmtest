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
"""Interfaces for the Local Component Architecture

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""


import zope.interface
import zope.component.interfaces
import zope.app.container.interfaces
import zope.app.container.constraints
from zope.app.i18n import ZopeMessageFactory as _
import registration

import zope.deferredimport

zope.deferredimport.deprecatedFrom(
    "Local registration is now much simpler.  The old baroque APIs "
    "will go away in Zope 3.5.  See the new component-registration APIs "
    "defined in zope.component, especially IComponentRegistry.",
    'zope.app.component.back35',
    'ILocalAdapterRegistry', 'ILocalUtility', 'IAdapterRegistration',
    'IUtilityRegistration',
    )

class IPossibleSite(zope.interface.Interface):
    """An object that could be a site
    """

    def setSiteManager(sitemanager):
        """Sets the site manager for this object.
        """

    def getSiteManager():
        """Returns the site manager contained in this object.

        If there isn't a site manager, raise a component lookup.
        """

class ISite(IPossibleSite):
    """Marker interface to indicate that we have a site"""

class INewLocalSite(zope.interface.Interface):
    """Event: a local site was created
    """

    manager = zope.interface.Attribute("The new site manager")

class NewLocalSite:
    """Event: a local site was created
    """
    zope.interface.implements(INewLocalSite)
    
    def __init__(self, manager):
        self.manager = manager


class ILocalSiteManager(zope.component.interfaces.IComponents):
    """Site Managers act as containers for registerable components.

    If a Site Manager is asked for an adapter or utility, it checks for those
    it contains before using a context-based lookup to find another site
    manager to delegate to.  If no other site manager is found they defer to
    the global site manager which contains file based utilities and adapters.
    """

    subs = zope.interface.Attribute(
        "A collection of registries that describe the next level "
        "of the registry tree. They are the children of this "
        "registry node. This attribute should never be "
        "manipulated manually. Use `addSub()` and `removeSub()` "
        "instead.")

    def addSub(sub):
        """Add a new sub-registry to the node.

        Important: This method should *not* be used manually. It is
        automatically called by `setNext()`. To add a new registry to the
        tree, use `sub.setNext(self, self.base)` instead!
        """

    def removeSub(sub):
        """Remove a sub-registry to the node.

        Important: This method should *not* be used manually. It is
        automatically called by `setNext()`. To remove a registry from the
        tree, use `sub.setNext(None)` instead!
        """
    

class ISiteManagementFolder(zope.app.container.interfaces.IContainer):
    """Component and component registration containers."""

    # XXX we need to figure out how to constrain this or, alternatively,
    # just use regular folders, which is probably the beter choice.
    # zope.app.container.constraints.containers(ILocalSiteManager)


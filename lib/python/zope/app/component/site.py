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
"""Site and Local Site Manager implementation

A local site manager has a number of roles:

  - A local site manager, that provides a local adapter and utility registry.

  - A place to do TTW development and/or to manage database-based code.

  - A registry for persistent modules.  The Zope 3 import hook uses the
    SiteManager to search for modules.

$Id: site.py 68941 2006-07-02 10:17:39Z philikon $
"""

import zope.event
import zope.interface
import zope.component
import zope.component.registry
import zope.component.persistentregistry
import zope.component.interfaces
import zope.traversing.api
import zope.deprecation
import zope.deferredimport
import zope.location

from zope.component.interfaces import ComponentLookupError
from zope.traversing.interfaces import IContainmentRoot
from zope.security.proxy import removeSecurityProxy
from zope.lifecycleevent import ObjectCreatedEvent
from zope.filerepresentation.interfaces import IDirectoryFactory

import zope.app.component.back35
from zope.app import zapi
from zope.app.component import interfaces
from zope.app.component import registration
from zope.app.component.hooks import setSite
from zope.app.container.btree import BTreeContainer
from zope.app.container.contained import Contained

##############################################################################
# from zope.app.module import resolve

# Break the dependency on zope.app.module.  In the long run,
# we need to handle this better.  Perhaps througha utility.

## def findModule(name, context=None):
##     """Find the module matching the provided name."""
##     module = ZopeModuleRegistry.findModule(name)
##     return module or sys.modules.get(name)

import sys

def resolve(name, context=None):
    """Resolve a dotted name to a Python object."""
    pos = name.rfind('.')
    mod = sys.modules.get(name[:pos])
##    mod = findModule(name[:pos], context)
    return getattr(mod, name[pos+1:], None)

# from zope.app.module import resolve
##############################################################################

class SiteManagementFolder(zope.app.component.back35.RegisterableContainer,
                           BTreeContainer):
    zope.interface.implements(interfaces.ISiteManagementFolder)


class SMFolderFactory(object):
    zope.interface.implements(IDirectoryFactory)

    def __init__(self, context):
        self.context = context

    def __call__(self, name):
        return SiteManagementFolder()


class SiteManagerContainer(Contained):
    """Implement access to the site manager (++etc++site).

    This is a mix-in that implements the IPossibleSite
    interface; for example, it is used by the Folder implementation.
    """
    zope.interface.implements(interfaces.IPossibleSite)

    _sm = None

    def getSiteManager(self):
        if self._sm is not None:
            return self._sm
        else:
            raise ComponentLookupError('no site manager defined')

    def setSiteManager(self, sm):
        if interfaces.ISite.providedBy(self):
            raise TypeError("Already a site")

        if zope.component.interfaces.IComponentLookup.providedBy(sm):
            self._sm = sm
            sm.__name__ = '++etc++site'
            sm.__parent__ = self
        else:
            raise ValueError('setSiteManager requires an IComponentLookup')

        zope.interface.directlyProvides(
            self, interfaces.ISite,
            zope.interface.directlyProvidedBy(self))

        zope.event.notify(interfaces.NewLocalSite(sm))

def _findNextSiteManager(site):
    while True:
        if IContainmentRoot.providedBy(site):
            # we're the root site, return None
            return None

        try:
            site = zope.traversing.api.getParent(site)
        except TypeError:
            # there was not enough context; probably run from a test
            return None

        if interfaces.ISite.providedBy(site):
            return site.getSiteManager()


class _LocalAdapterRegistry(
    zope.app.component.back35._LocalAdapterRegistryGeneration3SupportMixin,
    zope.component.persistentregistry.PersistentAdapterRegistry,
    zope.location.Location,
    ):
    pass

class LocalSiteManager(
    BTreeContainer,
    zope.app.component.back35.LocalSiteGeneration3SupportMixin,
    zope.component.persistentregistry.PersistentComponents,
    ):
    """Local Site Manager implementation"""
    zope.interface.implements(interfaces.ILocalSiteManager)

    subs = ()

    @property
    @zope.deprecation.deprecate("Goes away in Zope 3.5.  Use __bases__[0]")
    def next(self):
        if self.__bases__:
            return self.__bases__[0]

    def _setBases(self, bases):

        # Update base subs
        for base in self.__bases__:
            if ((base not in bases)
                and interfaces.ILocalSiteManager.providedBy(base)
                ):
                base.removeSub(self)

        for base in bases:
            if ((base not in self.__bases__)
                and interfaces.ILocalSiteManager.providedBy(base)
                ):
                base.addSub(self)

        super(LocalSiteManager, self)._setBases(bases)

    def __init__(self, site):
        # Locate the site manager
        self.__parent__ = site
        self.__name__ = '++etc++site'

        BTreeContainer.__init__(self)
        zope.component.persistentregistry.PersistentComponents.__init__(self)
        
        next = _findNextSiteManager(site)
        if next is None:
            next = zope.component.getGlobalSiteManager()
        self.__bases__ = (next, )

        # Setup default site management folder
        folder = SiteManagementFolder()
        zope.event.notify(ObjectCreatedEvent(folder))
        self['default'] = folder

    def _init_registries(self):
        self.adapters = _LocalAdapterRegistry()
        self.utilities = _LocalAdapterRegistry()

    def addSub(self, sub):
        """See interfaces.registration.ILocatedRegistry"""
        self.subs += (sub, )

    def removeSub(self, sub):
        """See interfaces.registration.ILocatedRegistry"""
        self.subs = tuple(
            [s for s in self.subs if s is not sub] )

    @zope.deprecation.deprecate("Will go away in Zope 3.5")
    def setNext(self, next, base=None):
        self.__bases__ = tuple([b for b in (next, base) if b is not None])

    def __getRegistry(self, registration):
        """Determine the correct registry for the registration."""
        if interfaces.IUtilityRegistration.providedBy(registration):
            return self.utilities
        elif interfaces.IAdapterRegistration.providedBy(registration):
            return self.adapters
        raise ValueError("Unable to detect registration type or registration "
                         "type is not supported. The registration object must "
                         "provide `IAdapterRegistration` or "
                         "`IUtilityRegistration`.")

    @zope.deprecation.deprecate(
        "Local registration is now much simpler.  The old baroque APIs "
        "will go away in Zope 3.5.  See the new component-registration APIs "
        "defined in zope.component, especially IComponentRegistry.",
        )
    def register(self, registration):
        if interfaces.IUtilityRegistration.providedBy(registration):
            self.registerUtility(
                registration.component,
                registration.provided,
                registration.name,
                )
        elif interfaces.IAdapterRegistration.providedBy(registration):
            self.registerAdapter(
                registration.component,
                (registration.required, ) + registration.with,
                registration.provided,
                registration.name,
                )
        try:
            f = registration.activated
        except AttributeError:
            pass
        else:
            f()

    @zope.deprecation.deprecate(
        "Local registration is now much simpler.  The old baroque APIs "
        "will go away in Zope 3.5.  See the new component-registration APIs "
        "defined in zope.component, especially IComponentRegistry.",
        )
    def unregister(self, registration):
        if interfaces.IUtilityRegistration.providedBy(registration):
            self.unregisterUtility(
                registration.component,
                registration.provided,
                registration.name,
                )
        elif interfaces.IAdapterRegistration.providedBy(registration):
            self.unregisterAdapter(
                registration.component,
                (registration.required, ) + registration.with,
                registration.provided,
                registration.name,
                )
        try:
            f = registration.deactivated
        except AttributeError:
            pass
        else:
            f()

    @zope.deprecation.deprecate(
        "Local registration is now much simpler.  The old baroque APIs "
        "will go away in Zope 3.5.  See the new component-registration APIs "
        "defined in zope.component, especially IComponentRegistry.",
        )
    def registered(self, registration):
        if zope.component.interfaces.IUtilityRegistration.providedBy(
            registration):
            return bool([
                r for r in self.registeredUtilities()
                if (
                   r.component == registration.component
                   and
                   r.provided == registration.provided
                   and
                   r.name == registration.name
                )
                ])
        elif zope.component.interfaces.IAdapterRegistration.providedBy(
            registration):
            return bool([
                r for r in self.registeredAdapters()
                if (
                   r.factory == registration.component
                   and
                   r.provided == registration.provided
                   and
                   r.name == registration.name
                   and
                   r.required == ((registration.required, )
                                  + registration.with)
                )
                ])
        elif (
         zope.component.interfaces.ISubscriptionAdapterRegistration.providedBy(
            registration)):
            return bool([
                r for r in self.registeredSubscriptionAdapters()
                if (
                   r.factory == registration.component
                   and
                   r.provided == registration.provided
                   and
                   r.name == registration.name
                   and
                   r.required == ((registration.required, )
                                  + registration.with)
                )
                ])
        elif zope.component.interfaces.IHandlerRegistration.providedBy(
            registration):
            return bool([
                r for r in self.registeredHandlers()
                if (
                   r.factory == registration.component
                   and
                   r.provided == registration.provided
                   and
                   r.name == registration.name
                   and
                   r.required == ((registration.required, )
                                  + registration.with)
                )
                ])
        return False

    @zope.deprecation.deprecate(
        "Local registration is now much simpler.  The old baroque APIs "
        "will go away in Zope 3.5.  See the new component-registration APIs "
        "defined in zope.component, especially IComponentRegistry.",
        )
    def registrations(self):
        """See zope.component.interfaces.IRegistry"""
        for r in self.registeredUtilities():
            yield r
        for r in self.registeredAdapters():
            yield r
        for r in self.registeredHandlers():
            yield r
        for r in self.registeredSubscriptionAdapters():
            yield r

zope.deferredimport.deprecated(
    "Local registration is now much simpler.  The old baroque APIs "
    "will go away in Zope 3.5.  See the new component-registration APIs "
    "defined in zope.component, especially IComponentRegistry.",
    LocalAdapterRegistry = 'zope.app.component.site:_LocalAdapterRegistry',
    LocalUtilityRegistry = 'zope.app.component.site:_LocalAdapterRegistry',
    UtilityRegistration = 'zope.app.component.back35:UtilityRegistration',
    AdaptersRegistration = 'zope.app.component.back35:AdaptersRegistration',
    )

def threadSiteSubscriber(ob, event):
    """A subscriber to BeforeTraverseEvent

    Sets the 'site' thread global if the object traversed is a site.
    """
    setSite(ob)


def clearThreadSiteSubscriber(event):
    """A subscriber to EndRequestEvent

    Cleans up the site thread global after the request is processed.
    """
    clearSite()

# Clear the site thread global
clearSite = setSite
from zope.testing.cleanup import addCleanUp
addCleanUp(clearSite)


@zope.component.adapter(zope.interface.Interface)
@zope.interface.implementer(zope.component.interfaces.IComponentLookup)
def SiteManagerAdapter(ob):
    """An adapter from ILocation to IComponentLookup.

    The ILocation is interpreted flexibly, we just check for
    ``__parent__``.
    """
    current = ob
    while True:
        if interfaces.ISite.providedBy(current):
            return current.getSiteManager()
        current = getattr(current, '__parent__', None)
        if current is None:
            # It is not a location or has no parent, so we return the global
            # site manager
            return zope.component.getGlobalSiteManager()

def changeSiteConfigurationAfterMove(site, event):
    """After a site is moved, its site manager links have to be updated."""
    if event.newParent is not None:
        next = _findNextSiteManager(site)
        site.getSiteManager().__bases__ = (next, )

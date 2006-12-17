##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Basic components support

$Id: registry.py 69628 2006-08-17 21:07:01Z ctheune $
"""

import types
import zope.deprecation
import zope.interface.adapter
from zope import component, interface
from zope.component import interfaces
import zope.interface.interfaces
import zope.event

class Components(object):

    interface.implements(interfaces.IComponents)

    def __init__(self, name='', bases=()):
        assert isinstance(name, basestring)
        self.__name__ = name
        self._init_registries()
        self._init_registrations()
        self.__bases__ = tuple(bases)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__name__)

    def _init_registries(self):
        self.adapters = zope.interface.adapter.AdapterRegistry()
        self.utilities = zope.interface.adapter.AdapterRegistry()

    def _init_registrations(self):
        self._utility_registrations = {}
        self._adapter_registrations = {}
        self._subscription_registrations = []
        self._handler_registrations = []

    def _getBases(self):
        # Subclasses might override
        return self.__dict__.get('__bases__', ())

    def _setBases(self, bases):
        # Subclasses might override
        self.adapters.__bases__ = tuple([
            base.adapters for base in bases])
        self.utilities.__bases__ = tuple([
            base.utilities for base in bases])
        self.__dict__['__bases__'] = bases

    __bases__ = property(
        lambda self: self._getBases(),
        lambda self, bases: self._setBases(bases),
        )

    def registerUtility(self, component, provided=None, name=u'', info=u'',
                        event=True):
        if provided is None:
            provided = _getUtilityProvided(component)

        if (self._utility_registrations.get((provided, name))
            == (component, info)):
            # already registered
            return

        subscribed = [
            1
            for ((p, _), (c,_)) in self._utility_registrations.iteritems()
            if p == provided and c == component
            ]

        self._utility_registrations[(provided, name)] = component, info
        self.utilities.register((), provided, name, component)

        if not subscribed:
            self.utilities.subscribe((), provided, component)

        if event:
            zope.event.notify(interfaces.Registered(
                UtilityRegistration(self, provided, name, component, info)
                ))

    def unregisterUtility(self, component=None, provided=None, name=u''):
        if provided is None:
            if component is None:
                raise TypeError("Must specify one of component and provided")
            provided = _getUtilityProvided(component)

        old = self._utility_registrations.get((provided, name))
        if (old is None) or ((component is not None) and
                             (component != old[0])):
            return False

        if component is None:
            component = old[0]
        del self._utility_registrations[(provided, name)]
        self.utilities.unregister((), provided, name)

        subscribed = [
            1
            for ((p, _), (c,_)) in self._utility_registrations.iteritems()
            if p == provided and c == component
            ]

        if not subscribed:
            self.utilities.unsubscribe((), provided, component)

        zope.event.notify(interfaces.Unregistered(
            UtilityRegistration(self, provided, name, component, old[1])
            ))

        return True

    def registeredUtilities(self):
        for ((provided, name), (component, info)
             ) in self._utility_registrations.iteritems():
            yield UtilityRegistration(self, provided, name, component, info)

    def queryUtility(self, provided, name=u'', default=None):
        return self.utilities.lookup((), provided, name, default)

    def getUtility(self, provided, name=u''):
        utility = self.utilities.lookup((), provided, name)
        if utility is None:
            raise interfaces.ComponentLookupError(provided, name)
        return utility

    def getUtilitiesFor(self, interface):
        for name, utility in self.utilities.lookupAll((), interface):
            yield name, utility

    def getAllUtilitiesRegisteredFor(self, interface):
        return self.utilities.subscriptions((), interface)

    def registerAdapter(self, factory, required=None, provided=None, name=u'',
                        info=u'', event=True):
        if provided is None:
            provided = _getAdapterProvided(factory)
        required = _getAdapterRequired(factory, required)
        self._adapter_registrations[(required, provided, name)
                                    ] = factory, info
        self.adapters.register(required, provided, name, factory)

        if event:
            zope.event.notify(interfaces.Registered(
                AdapterRegistration(self, required, provided, name,
                                    factory, info)
                ))


    def unregisterAdapter(self, factory=None,
                          required=None, provided=None, name=u'',
                          ):
        if provided is None:
            if factory is None:
                raise TypeError("Must specify one of factory and provided")
            provided = _getAdapterProvided(factory)

        if (required is None) and (factory is None):
            raise TypeError("Must specify one of factory and required")

        required = _getAdapterRequired(factory, required)
        old = self._adapter_registrations.get((required, provided, name))
        if (old is None) or ((factory is not None) and
                             (factory != old[0])):
            return False

        del self._adapter_registrations[(required, provided, name)]
        self.adapters.unregister(required, provided, name)

        zope.event.notify(interfaces.Unregistered(
            AdapterRegistration(self, required, provided, name,
                                *old)
            ))

        return True

    def registeredAdapters(self):
        for ((required, provided, name), (component, info)
             ) in self._adapter_registrations.iteritems():
            yield AdapterRegistration(self, required, provided, name,
                                      component, info)

    def queryAdapter(self, object, interface, name=u'', default=None):
        return self.adapters.queryAdapter(object, interface, name, default)

    def getAdapter(self, object, interface, name=u''):
        adapter = self.adapters.queryAdapter(object, interface, name)
        if adapter is None:
            raise interfaces.ComponentLookupError(object, interface, name)
        return adapter

    def queryMultiAdapter(self, objects, interface, name=u'', default=None):
        return self.adapters.queryMultiAdapter(
            objects, interface, name, default)

    def getMultiAdapter(self, objects, interface, name=u''):
        adapter = self.adapters.queryMultiAdapter(objects, interface, name)
        if adapter is None:
            raise interfaces.ComponentLookupError(objects, interface, name)
        return adapter

    def getAdapters(self, objects, provided):
        for name, factory in self.adapters.lookupAll(
            map(interface.providedBy, objects),
            provided):
            adapter = factory(*objects)
            if adapter is not None:
                yield name, adapter

    def registerSubscriptionAdapter(self,
                                    factory, required=None, provided=None,
                                    name=u'', info=u'',
                                    event=True):
        if name:
            raise TypeError("Named subscribers are not yet supported")
        if provided is None:
            provided = _getAdapterProvided(factory)
        required = _getAdapterRequired(factory, required)
        self._subscription_registrations.append(
            (required, provided, name, factory, info)
            )
        self.adapters.subscribe(required, provided, factory)

        if event:
            zope.event.notify(interfaces.Registered(
                SubscriptionRegistration(self, required, provided, name,
                                         factory, info)
                ))

    def registeredSubscriptionAdapters(self):
        for data in self._subscription_registrations:
            yield SubscriptionRegistration(self, *data)

    def unregisterSubscriptionAdapter(self, factory=None,
                          required=None, provided=None, name=u'',
                          ):
        if name:
            raise TypeError("Named subscribers are not yet supported")
        if provided is None:
            if factory is None:
                raise TypeError("Must specify one of factory and provided")
            provided = _getAdapterProvided(factory)

        if (required is None) and (factory is None):
            raise TypeError("Must specify one of factory and required")

        required = _getAdapterRequired(factory, required)

        if factory is None:
            new = [(r, p, n, f, i)
                   for (r, p, n, f, i)
                   in self._subscription_registrations
                   if not (r == required and p == provided)
                   ]
        else:
            new = [(r, p, n, f, i)
                   for (r, p, n, f, i)
                   in self._subscription_registrations
                   if not (r == required and p == provided and f == factory)
                   ]

        if len(new) == len(self._subscription_registrations):
            return False


        self._subscription_registrations[:] = new
        self.adapters.unsubscribe(required, provided)

        zope.event.notify(interfaces.Unregistered(
            SubscriptionRegistration(self, required, provided, name,
                                     factory, '')
            ))

        return True

    def subscribers(self, objects, provided):
        return self.adapters.subscribers(objects, provided)

    def registerHandler(self,
                        factory, required=None,
                        name=u'', info=u'',
                        event=True):
        if name:
            raise TypeError("Named handlers are not yet supported")
        required = _getAdapterRequired(factory, required)
        self._handler_registrations.append(
            (required, name, factory, info)
            )
        self.adapters.subscribe(required, None, factory)

        if event:
            zope.event.notify(interfaces.Registered(
                HandlerRegistration(self, required, name, factory, info)
                ))

    def registeredHandlers(self):
        for data in self._handler_registrations:
            yield HandlerRegistration(self, *data)

    def unregisterHandler(self, factory=None, required=None, name=u''):
        if name:
            raise TypeError("Named subscribers are not yet supported")

        if (required is None) and (factory is None):
            raise TypeError("Must specify one of factory and required")

        required = _getAdapterRequired(factory, required)

        if factory is None:
            new = [(r, n, f, i)
                   for (r, n, f, i)
                   in self._handler_registrations
                   if r != required
                   ]
        else:
            new = [(r, n, f, i)
                   for (r, n, f, i)
                   in self._handler_registrations
                   if not (r == required and f == factory)
                   ]

        if len(new) == len(self._handler_registrations):
            return False

        self._handler_registrations[:] = new
        self.adapters.unsubscribe(required, None, factory)

        zope.event.notify(interfaces.Unregistered(
            HandlerRegistration(self, required, name, factory, '')
            ))

        return True

    def handle(self, *objects):
        self.adapters.subscribers(objects, None)


def _getUtilityProvided(component):
    provided = list(interface.providedBy(component))
    if len(provided) == 1:
        return provided[0]
    raise TypeError(
        "The utility doesn't provide a single interface "
        "and no provided interface was specified.")

def _getAdapterProvided(factory):
    provided = list(interface.implementedBy(factory))
    if len(provided) == 1:
        return provided[0]
    raise TypeError(
        "The adapter factory doesn't implement a single interface "
        "and no provided interface was specified.")


classTypes = type, types.ClassType
def _getAdapterRequired(factory, required):
    if required is None:
        try:
            required = factory.__component_adapts__
        except AttributeError:
            raise TypeError(
                "The adapter factory doesn't have a __component_adapts__ "
                "attribute and no required specifications were specified"
                )
    elif zope.interface.interfaces.ISpecification.providedBy(required):
        raise TypeError("the required argument should be a list of "
                        "interfaces, not a single interface")

    result = []
    for r in required:
        if r is None:
            r = interface.Interface
        elif not zope.interface.interfaces.ISpecification.providedBy(r):
            if isinstance(r, classTypes):
                r = interface.implementedBy(r)
            else:
                raise TypeError("Required specification must be a "
                                "specification or class."
                                )
        result.append(r)
    return tuple(result)


class UtilityRegistration(object):

    interface.implements(interfaces.IUtilityRegistration)

    def __init__(self, registry, provided, name, component, doc):
        (self.registry, self.provided, self.name, self.component, self.info
         ) = registry, provided, name, component, doc

    def __repr__(self):
        return '%s(%r, %s, %r, %s, %r)' % (
            self.__class__.__name__,
            self.registry,
            getattr(self.provided, '__name__', None), self.name,
            getattr(self.component, '__name__', `self.component`), self.info,
            )

    def __cmp__(self, other):
        return cmp(self.__repr__(), other.__repr__())

class AdapterRegistration(object):

    interface.implements(interfaces.IAdapterRegistration)

    def __init__(self, registry, required, provided, name, component, doc):
        (self.registry, self.required, self.provided, self.name,
         self.factory, self.info
         ) = registry, required, provided, name, component, doc

    def __repr__(self):
        return '%s(%r, %s, %s, %r, %s, %r)' % (
            self.__class__.__name__,
            self.registry,
            '[' + ", ".join([r.__name__ for r in self.required]) + ']',
            getattr(self.provided, '__name__', None), self.name,
            getattr(self.factory, '__name__', `self.factory`), self.info,
            )

    def __cmp__(self, other):
        return cmp(self.__repr__(), other.__repr__())

    # this may actually not be needed as component did not exist as
    # an attribute in Zope 3.2, but we'll leave it in to be sure.
    @property
    @zope.deprecation.deprecate(
        "The component attribute on adapter registrations will be unsupported "
        "in Zope 3.5. Use the factory attribute instead.")
    def component(self):
        return self.factory

    @property
    @zope.deprecation.deprecate(
        "The value attribute on adapter registrations will be unsupported "
        "in Zope 3.5. Use the factory attribute instead.")
    def value(self):
        return self.factory

    @property
    @zope.deprecation.deprecate(
        "The doc attribute on adapter registrations will be unsupported "
        "in Zope 3.5. Use the info attribute instead.")
    def doc(self):
        return self.info
    
class SubscriptionRegistration(AdapterRegistration):

    interface.implementsOnly(interfaces.ISubscriptionAdapterRegistration)

class HandlerRegistration(AdapterRegistration):

    interface.implementsOnly(interfaces.IHandlerRegistration)

    def __init__(self, registry, required, name, handler, doc):
        (self.registry, self.required, self.name, self.handler, self.info
         ) = registry, required, name, handler, doc

    @property
    def factory(self):
        return self.handler

    provided = None

    def __repr__(self):
        return '%s(%r, %s, %r, %s, %r)' % (
            self.__class__.__name__,
            self.registry,
            '[' + ", ".join([r.__name__ for r in self.required]) + ']',
            self.name,
            getattr(self.factory, '__name__', `self.factory`), self.info,
            )


@component.adapter(interfaces.IUtilityRegistration,
                   interfaces.IRegistrationEvent)
def dispatchUtilityRegistrationEvent(registration, event):
    component.handle(registration.component, event)

@component.adapter(interfaces.IAdapterRegistration,
                   interfaces.IRegistrationEvent)
def dispatchAdapterRegistrationEvent(registration, event):
    component.handle(registration.factory, event)

@component.adapter(interfaces.ISubscriptionAdapterRegistration,
                   interfaces.IRegistrationEvent)
def dispatchSubscriptionAdapterRegistrationEvent(registration, event):
    component.handle(registration.factory, event)

@component.adapter(interfaces.IHandlerRegistration,
                   interfaces.IRegistrationEvent)
def dispatchHandlerRegistrationEvent(registration, event):
    component.handle(registration.handler, event)



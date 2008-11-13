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
"""Support for taking security into account in adaptation

$Id: adapter.py 73624 2007-03-26 12:50:23Z dobe $
"""

from zope.security.checker import ProxyFactory
from zope.security.proxy import removeSecurityProxy
from zope.location import ILocation, LocationProxy

def assertLocation(adapter, parent):
    """Assert locatable adapters.

    This function asserts that the adapter get location-proxied if
    it doesn't provide ILocation itself. Further more the returned
    locatable adapter get its parent set if its __parent__ attribute
    is currently None.

    see adapter.txt
    """
    # handle none-locatable adapters (A)
    if not ILocation.providedBy(adapter):
        locatable = LocationProxy(adapter)
        locatable.__parent__ = parent
        return locatable

    # handle locatable, parentless adapters (B)
    if adapter.__parent__ is None:
        adapter.__parent__ = parent
        return adapter

    # handle locatable, parentful adapters (C)
    else:
        return adapter


class LocatingTrustedAdapterFactory(object):
    """Adapt an adapter factory to provide trusted and (locatable) adapters.

    Trusted adapters always adapt unproxied objects. If asked to
    adapt any proxied objects, it will unproxy them and then
    security-proxy the resulting adapter (S) unless the objects where not
    security-proxied before (N).

    Further locating trusted adapters provide a location for protected
    adapters only (S). If such a protected adapter itself does not provide
    ILocation it is wrapped within a location proxy and it parent will
    be set. If the adapter does provide ILocation and it's __parent__ is None,
    we set the __parent__ to the adapter's context:

    see adapter.txt
    """
    def __init__(self, factory):
        self.factory = factory
        self.__name__ = factory.__name__
        self.__module__ = factory.__module__

    # protected methods
    def _customizeProtected(self, adapter, context):
        return assertLocation(adapter, context)

    def _customizeUnprotected(self, adapter, context):
        if (ILocation.providedBy(adapter)
            and adapter.__parent__ is None):
                    adapter.__parent__ = context
        return adapter

    def __call__(self, *args):
        for arg in args:
            if removeSecurityProxy(arg) is not arg:
                args = map(removeSecurityProxy, args)
                adapter = self.factory(*args)
                adapter = self._customizeProtected(adapter, args[0])
                return ProxyFactory(adapter)

        adapter = self.factory(*args)
        adapter = self._customizeUnprotected(adapter, args[0])
        return adapter


# BBB, entire class gone in 3.2
class TrustedAdapterFactory(LocatingTrustedAdapterFactory):
    """Adapt an adapter factory to provide trusted adapters.

    Trusted adapters always adapt unproxied objects. If asked to
    adapt any proxied objects, it will unproxy them and then
    security-proxy the resulting adapter unless the objects where not
    security-proxied before.

    If the adapter does provide ILocation and it's __parent__ is None,
    we set the __parent__ to the adapter's context.
    """

    # do not location-proxy the adapter
    def _customizeProtected(self, adapter, context):
        return self._customizeUnprotected(adapter, context)


class LocatingUntrustedAdapterFactory(object):
    """Adapt an adapter factory to provide locatable untrusted adapters

    Untrusted adapters always adapt proxied objects. If any permission
    other than zope.Public is required, untrusted adapters need a location
    in order that the local authentication mechanism can be inovked
    correctly.

    If the adapter does not provide ILocation, we location proxy it and
    set the parent. If the adapter does provide ILocation and
    it's __parent__ is None, we set the __parent__ to the adapter's
    context only:

    see adapter.txt
    """

    def __init__(self, factory):
        self.factory = factory
        self.__name__ = factory.__name__
        self.__module__ = factory.__module__

    def __call__(self, *args):
        adapter = self.factory(*args)
        return assertLocation(adapter, args[0])

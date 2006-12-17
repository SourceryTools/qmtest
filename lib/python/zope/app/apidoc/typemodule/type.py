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
"""Interface Types Documentation Module

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.component import queryUtility, getUtilitiesFor
from zope.interface.interfaces import IInterface
from zope.location import LocationProxy
from zope.location.interfaces import ILocation

from zope.app.i18n import ZopeMessageFactory as _
from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase

class TypeInterface(ReadContainerBase):
    """Representation of the special type interface.

    Demonstration::

      >>> from zope.interface import Interface
      >>> class IFoo(Interface):
      ...    pass
      >>> class Foo:
      ...     implements(IFoo)
      >>> from zope.app.testing import ztapi
      >>> ztapi.provideUtility(IFoo, Foo(), 'Foo')

      >>> typeiface = TypeInterface(IFoo, None, None)
      >>> typeiface.interface
      <InterfaceClass zope.app.apidoc.typemodule.type.IFoo>
      
      >>> typeiface.get('Foo').__class__ == Foo
      True

      >>> typeiface.items() #doctest:+ELLIPSIS
      [(u'Foo', <zope.app.apidoc.typemodule.type.Foo instance at ...>)]
      
    """

    implements(ILocation)

    def __init__(self, interface, parent, name):
        self.__parent__ = parent
        self.__name__ = name
        self.interface = interface

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer"""
        return LocationProxy(
            queryUtility(self.interface, key, default=default),
            self, key)

    def items(self):
        """See zope.app.container.interfaces.IReadContainer"""
        results = [(name, LocationProxy(iface, self, name))
                   for name, iface in getUtilitiesFor(self.interface)]
        results.sort(lambda x, y: cmp(x[1].getName(), y[1].getName()))
        return results


class TypeModule(ReadContainerBase):
    r"""Represent the Documentation of all interface types.

    Demonstration::

      >>> class IFoo(IInterface):
      ...    pass
      
      >>> from zope.app.testing import ztapi
      >>> ztapi.provideUtility(IInterface, IFoo, 'IFoo')

      >>> module = TypeModule()
      >>> type = module.get('IFoo')

      >>> type.interface
      <InterfaceClass zope.app.apidoc.typemodule.type.IFoo>

      >>> [type.interface for name, type in module.items()]
      [<InterfaceClass zope.app.apidoc.typemodule.type.IFoo>]
    """

    implements(IDocumentationModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('Interface Types')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    Here you can see all registered interface types. When you open the subtree
    of a specific interface type, you can see all the interfaces that provide
    this type. This can be very useful in cases where you want to determine
    all content type interfaces, for example.
    """)

    def get(self, key, default=None):
        return TypeInterface(
            queryUtility(IInterface, key, default=default), self, key)

    def items(self):
        results = [(name, TypeInterface(iface, self, name))
                   for name, iface in getUtilitiesFor(IInterface)
                   if iface.extends(IInterface)]
        results.sort(lambda x, y: cmp(x[1].interface.getName(),
                                      y[1].interface.getName()))
        return results

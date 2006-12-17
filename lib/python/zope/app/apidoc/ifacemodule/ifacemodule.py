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
"""Interface Documentation Module

The interface documentation module retrieves its information from the
site manager. Therefore, currently there are no unregsitered interfaces
listed in the documentation. This might be good, since unregistered interfaces
are usually private and not of interest to a general developer.

$Id: __init__.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.location import LocationProxy
from zope.component.interface import queryInterface
from zope.component.interface import searchInterfaceUtilities

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase
from zope.app.i18n import ZopeMessageFactory as _

class IInterfaceModule(IDocumentationModule):
    """Interface API Documentation Module

    This is a marker interface, so that we can write adapters for objects
    implementing this interface.
    """

class InterfaceModule(ReadContainerBase):
    r"""Represent the Documentation of all Interfaces.

    This documentation is implemented using a simple `IReadContainer`. The
    items of the container are all the interfaces listed in the global
    site manager."""

    implements(IInterfaceModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('Interfaces')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    All used and important interfaces are registered through the site
    manager. While it would be possible to just list all attributes, it is
    hard on the user to read such an overfull list. Therefore, interfaces that
    have partial common module paths are bound together.

    The documentation of an interface also provides a wide variety of
    information, including of course the declared attributes/fields and
    methods, but also available adapters, and utilities that provide
    this interface.
    """)

    def get(self, key, default=None):
        """See zope.app.interfaces.container.IReadContainer"""
        iface = queryInterface(key, default)
        if iface is default:
            # Yeah, we find more items than we claim to have! This way we can
            # handle all interfaces using this module. :-)
            parts = key.split('.')
            try:
                mod = __import__('.'.join(parts[:-1]), {}, {}, ('*',))
            except ImportError:
                iface = default
            else:
                iface = getattr(mod, parts[-1], default)

        if not iface is default:
            iface = LocationProxy(iface, self, key)

        return iface

    def items(self):
        """See zope.app.interfaces.container.IReadContainer"""
        items = list(searchInterfaceUtilities(self))
        items.sort()
        items = [(i[0], LocationProxy(i[1], self, i[0])) for i in items]
        return items

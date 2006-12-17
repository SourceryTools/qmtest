#############################################################################
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
"""Browser-Presentation related Fields.

$Id: fields.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.schema
from zope.component.interfaces import ComponentLookupError
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.fields import GlobalObject
from zope.interface.interfaces import IInterface
from zope.app.publisher.interfaces.browser import IMenuItemType

from zope.app import zapi


class MenuField(GlobalObject):
    r"""This fields represents a menu (item type).

    Besides being able to look up the menu by importing it, we also try
    to look up the name in the site manager.

    >>> from zope.interface import directlyProvides
    >>> from zope.interface.interface import InterfaceClass

    >>> menu1 = InterfaceClass('menu1', (),
    ...                        __doc__='Menu Item Type: menu1',
    ...                        __module__='zope.app.menus')
    >>> directlyProvides(menu1, IMenuItemType)

    >>> menus = None
    >>> class Resolver(object):
    ...     def resolve(self, path):
    ...         if path.startswith('zope.app.menus') and \
    ...             hasattr(menus, 'menu1') or \
    ...             path == 'zope.app.component.menus.menu1':
    ...             return menu1
    ...         raise ConfigurationError('menu1')

    >>> field = MenuField()
    >>> field = field.bind(Resolver())

    Test 1: Import the menu
    -----------------------

    >>> field.fromUnicode('zope.app.component.menus.menu1') is menu1
    True

    Test 2: We have a shortcut name. Import the menu from `zope.app.menus1`.
    ------------------------------------------------------------------------

    >>> from types import ModuleType as module
    >>> import sys
    >>> menus = module('menus')
    >>> old = sys.modules.get('zope.app.menus', None)
    >>> sys.modules['zope.app.menus'] = menus
    >>> setattr(menus, 'menu1', menu1)

    >>> field.fromUnicode('menu1') is menu1
    True

    >>> if old is not None:
    ...     sys.modules['zope.app.menus'] = old

    Test 3: Get the menu from the Site Manager
    ------------------------------------------
    
    >>> from zope.app.testing import ztapi
    >>> ztapi.provideUtility(IMenuItemType, menu1, 'menu1')

    >>> field.fromUnicode('menu1') is menu1
    True
    """

    def fromUnicode(self, u):
        name = str(u.strip())

        try:
            value = zapi.queryUtility(IMenuItemType, name)
        except ComponentLookupError:
            # The component architecture is not up and running.
            pass
        else: 
            if value is not None:
                self.validate(value)
                return value

        try:
            value = self.context.resolve('zope.app.menus.'+name)
        except ConfigurationError, v:
            try:
                value = self.context.resolve(name)
            except ConfigurationError, v:
                raise zope.schema.ValidationError(v)
        
        self.validate(value)
        return value

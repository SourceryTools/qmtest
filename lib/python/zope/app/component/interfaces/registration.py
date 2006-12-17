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
"""Interfaces for objects supporting registration

$Id: registration.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope import interface, schema
import zope.schema.interfaces

import zope.deferredimport

zope.deferredimport.deprecatedFrom(
    "Local registration is now much simpler.  The old baroque APIs "
    "will go away in Zope 3.5.  See the new component-registration APIs "
    "defined in zope.component, especially IComponentRegistry.",
    'zope.app.component.back35',
    'IRegistration',
    'InactiveStatus',
    'ActiveStatus',
    'IComponentRegistration',
    'IRegistry',
    'ILocatedRegistry',
    'IRegistrationManager',
    'IRegistrationManagerContained',
    'IRegisterableContainer',
    'IRegisterable',
    'IRegisterableContainerContaining',
    'IRegistered',
    )

zope.deferredimport.deprecated(
    "Registration events are not defined in zope.component.interfaces. "
    "Importing them from zope.app.component.registration will be disallowed "
    "in Zope 3.5",
    IRegistrationEvent = 'zope.component.interfaces:IRegistrationEvent',
    IRegistrationActivatedEvent = 'zope.component.interfaces:IRegistered',
    IRegistrationDeactivatedEvent = 'zope.component.interfaces:IUnregistered',
    )

class IComponent(zope.schema.interfaces.IField):
    """A component 

    This is just the interface for the ComponentPath field below.  We'll use
    this as the basis for looking up an appropriate widget.
    """

class Component(schema.Field):
    """A component 

    Values of the field are absolute unicode path strings that can be
    traversed to get an object.
    """
    interface.implements(IComponent)


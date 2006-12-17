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
"""Component registration support

$Id: registration.py 67630 2006-04-27 00:54:03Z jim $
"""

import zope.deferredimport

zope.deferredimport.deprecatedFrom(
    """The old registration APIs, are deprecated and will go away in Zope 3.5

    See the newer component-registration APIs in
    zope.component.interfaces.IComponentRegistry.
    """,
    "zope.app.component.back35",
    'RegistrationStatusProperty',
    'SimpleRegistration',
    'ComponentRegistration',
    'Registered',
    'RegistrationManager',
    'RegisterableContainer',
    'RegistrationManagerNamespace',
    )

zope.deferredimport.deprecated(
    "Registration events are now defined in zope.component.interfaces. "
    "Importing them from zope.app.component.registration will be disallowed "
    "in Zope 3.5",
    RegistrationEvent = 'zope.component.interfaces:RegistrationEvent',
    RegistrationActivatedEvent = 'zope.component.interfaces:Registered',
    RegistrationDeactivatedEvent = 'zope.component.interfaces:Unregistered',
    )

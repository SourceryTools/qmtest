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
"""DEPRECATED"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "Local registration is now much simpler.  The old baroque APIs "
    "will go away in Zope 3.5.  See the new component-registration APIs "
    "defined in zope.component, especially IComponentRegistry.",
    LocalAdapterRegistry = 'zope.app.component.site:_LocalAdapterRegistry',
    AdapterRegistration = 'zope.app.component.back35:AdapterRegistration2',
    )


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
"""Persistent component managers

$Id: persistentregistry.py 67729 2006-04-28 18:07:25Z jim $
"""
import persistent.mapping
import persistent.list
import zope.interface.adapter

import zope.component.registry

class PersistentAdapterRegistry(
    zope.interface.adapter.VerifyingAdapterRegistry,
    persistent.Persistent,
    ):

    def changed(self, originally_changed):
        if originally_changed is self:
            self._p_changed = True
        super(PersistentAdapterRegistry, self).changed(originally_changed)

    def __getstate__(self):
        state = super(PersistentAdapterRegistry, self).__getstate__().copy()
        for name in self._delegated:
            state.pop(name, 0)
        return state

    def __setstate__(self, state):
        super(PersistentAdapterRegistry, self).__setstate__(state)
        self._createLookup()
        self._v_lookup.changed(self)
        
        
class PersistentComponents(zope.component.registry.Components):

    def _init_registries(self):
        self.adapters = PersistentAdapterRegistry()
        self.utilities = PersistentAdapterRegistry()

    def _init_registrations(self):
        self._utility_registrations = persistent.mapping.PersistentMapping()
        self._adapter_registrations = persistent.mapping.PersistentMapping()
        self._subscription_registrations = persistent.list.PersistentList()
        self._handler_registrations = persistent.list.PersistentList()

    

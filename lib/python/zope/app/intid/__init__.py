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
"""Unique id utility.

This utility assigns unique integer ids to objects and allows lookups
by object and by id.

This functionality can be used in cataloging.

$Id: __init__.py 69786 2006-08-26 18:06:12Z philikon $
"""
import random
from BTrees import IOBTree, OIBTree
from ZODB.interfaces import IConnection
from persistent import Persistent

from zope.event import notify
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy
from zope.location.interfaces import ILocation
from zope.component import adapter, getAllUtilitiesRegisteredFor

from zope.app.container.interfaces import IObjectRemovedEvent
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.contained import Contained
from zope.app.keyreference.interfaces import IKeyReference, NotYet

from zope.app.intid.interfaces import IIntIds
from zope.app.intid.interfaces import IntIdRemovedEvent
from zope.app.intid.interfaces import IntIdAddedEvent

class IntIds(Persistent, Contained):
    """This utility provides a two way mapping between objects and
    integer ids.

    IKeyReferences to objects are stored in the indexes.
    """
    implements(IIntIds)

    _v_nextid = None   

    _randrange = random.randrange

    def __init__(self):
        self.ids = OIBTree.OIBTree()
        self.refs = IOBTree.IOBTree()

    def __len__(self):
        return len(self.ids)

    def items(self):
        return list(self.refs.items())

    def __iter__(self):
        return self.refs.iterkeys()

    def getObject(self, id):
        return self.refs[id]()

    def queryObject(self, id, default=None):
        r = self.refs.get(id)
        if r is not None:
            return r()
        return default

    def getId(self, ob):
        try:
            key = IKeyReference(ob)
        except (NotYet, TypeError):
            raise KeyError(ob)

        try:
            return self.ids[key]
        except KeyError:
            raise KeyError(ob)

    def queryId(self, ob, default=None):
        try:
            return self.getId(ob)
        except KeyError:
            return default

    def _generateId(self):
        """Generate an id which is not yet taken.

        This tries to allocate sequential ids so they fall into the
        same BTree bucket, and randomizes if it stumbles upon a
        used one.
        """
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(0, 2**31)
            uid = self._v_nextid
            self._v_nextid += 1
            if uid not in self.refs:
                return uid
            self._v_nextid = None

    def register(self, ob):
        # Note that we'll still need to keep this proxy removal.
        ob = removeSecurityProxy(ob)
        key = IKeyReference(ob)

        if key in self.ids:
            return self.ids[key]
        uid = self._generateId()
        self.refs[uid] = key
        self.ids[key] = uid
        return uid

    def unregister(self, ob):
        # Note that we'll still need to keep this proxy removal.
        ob = removeSecurityProxy(ob)
        key = IKeyReference(ob, None)
        if key is None:
            return

        uid = self.ids[key]
        del self.refs[uid]
        del self.ids[key]


@adapter(ILocation, IObjectRemovedEvent)
def removeIntIdSubscriber(ob, event):
    """A subscriber to ObjectRemovedEvent

    Removes the unique ids registered for the object in all the unique
    id utilities.
    """
    utilities = tuple(getAllUtilitiesRegisteredFor(IIntIds))
    if utilities:
        key = IKeyReference(ob, None)
        # Register only objects that adapt to key reference
        if key is not None:
            # Notify the catalogs that this object is about to be removed.
            notify(IntIdRemovedEvent(ob, event))
            for utility in utilities:
                try:
                    utility.unregister(key)
                except KeyError:
                    pass

@adapter(ILocation, IObjectAddedEvent)
def addIntIdSubscriber(ob, event):
    """A subscriber to ObjectAddedEvent

    Registers the object added in all unique id utilities and fires
    an event for the catalogs.
    """
    utilities = tuple(getAllUtilitiesRegisteredFor(IIntIds))
    if utilities: # assert that there are any utilites
        key = IKeyReference(ob, None)
        # Register only objects that adapt to key reference
        if key is not None:
            for utility in utilities:
                utility.register(key)
            # Notify the catalogs that this object was added.
            notify(IntIdAddedEvent(ob, event))

# BBB
UniqueIdUtility = IntIds
import zope.app.keyreference.persistent
ReferenceToPersistent = (
    zope.app.keyreference.persistent.KeyReferenceToPersistent)
import sys
sys.modules['zope.app.uniqueid'] = sys.modules['zope.app.intid']
del sys

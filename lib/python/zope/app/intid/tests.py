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
"""Tests for the unique id utility.

$Id: tests.py 68719 2006-06-17 21:51:14Z ctheune $
"""
import unittest

from persistent import Persistent
from persistent.interfaces import IPersistent
from ZODB.interfaces import IConnection

from zope.interface import implements
from zope.interface.verify import verifyObject
from zope.location.interfaces import ILocation

from zope.app.testing import setup, ztapi
from zope.app import zapi
from zope.app.component.hooks import setSite

from zope.app.intid.interfaces import IIntIds
from zope.app.intid import IntIds
from zope.app.keyreference.persistent import KeyReferenceToPersistent
from zope.app.keyreference.persistent import connectionOfPersistent
from zope.app.keyreference.interfaces import IKeyReference


class P(Persistent):
    implements(ILocation)


class ConnectionStub(object):
    next = 1

    def db(self):
        return self

    database_name = 'ConnectionStub'
    
    def add(self, ob):
        ob._p_jar = self
        ob._p_oid = self.next
        self.next += 1


class ReferenceSetupMixin(object):
    """Registers adapters ILocation->IConnection and IPersistent->IReference"""
    def setUp(self):
        self.root = setup.placefulSetUp(site=True)
        ztapi.provideAdapter(IPersistent, IConnection, connectionOfPersistent)
        ztapi.provideAdapter(IPersistent, IKeyReference,
                             KeyReferenceToPersistent)

    def tearDown(self):
        setup.placefulTearDown()


class TestIntIds(ReferenceSetupMixin, unittest.TestCase):

    def test_interface(self):
        verifyObject(IIntIds, IntIds())

    def test_non_keyreferences(self):
        u = IntIds()
        obj = object()

        self.assert_(u.queryId(obj) is None)
        self.assert_(u.unregister(obj) is None)
        self.assertRaises(KeyError, u.getId, obj)

    def test(self):
        u = IntIds()
        obj = P()
        
        obj._p_jar = ConnectionStub()

        self.assertRaises(KeyError, u.getId, obj)
        self.assertRaises(KeyError, u.getId, P())

        self.assert_(u.queryId(obj) is None)
        self.assert_(u.queryId(obj, 42) is 42)
        self.assert_(u.queryId(P(), 42) is 42)
        self.assert_(u.queryObject(42) is None)
        self.assert_(u.queryObject(42, obj) is obj)

        uid = u.register(obj)
        self.assert_(u.getObject(uid) is obj)
        self.assert_(u.queryObject(uid) is obj)
        self.assertEquals(u.getId(obj), uid)
        self.assertEquals(u.queryId(obj), uid)

        uid2 = u.register(obj)
        self.assertEquals(uid, uid2)

        u.unregister(obj)
        self.assertRaises(KeyError, u.getObject, uid)
        self.assertRaises(KeyError, u.getId, obj)

    def test_btree_long(self):
        # This is a somewhat arkward test, that *simulates* the border case
        # behaviour of the _generateId method
        u = IntIds()
        u._randrange = lambda x,y:int(2**31-1)

        # The chosen int is exactly the largest number possible that is
        # delivered by the randint call in the code
        obj = P()
        obj._p_jar = ConnectionStub()
        uid = u.register(obj)
        self.assertEquals(2**31-1, uid)
        # Make an explicit tuple here to avoid implicit type casts on 2**31-1
        # by the btree code
        self.failUnless(2**31-1 in tuple(u.refs.keys()))

    def test_len_items(self):
        u = IntIds()
        obj = P()
        obj._p_jar = ConnectionStub()


        self.assertEquals(len(u), 0)
        self.assertEquals(u.items(), [])
        self.assertEquals(list(u), [])

        uid = u.register(obj)
        ref = KeyReferenceToPersistent(obj)
        self.assertEquals(len(u), 1)
        self.assertEquals(u.items(), [(uid, ref)])
        self.assertEquals(list(u), [uid])

        obj2 = P()
        obj2.__parent__ = obj

        uid2 = u.register(obj2)
        ref2 = KeyReferenceToPersistent(obj2)
        self.assertEquals(len(u), 2)
        result = u.items()
        expected = [(uid, ref), (uid2, ref2)]
        result.sort()
        expected.sort()
        self.assertEquals(result, expected)
        result = list(u)
        expected = [uid, uid2]
        result.sort()
        expected.sort()
        self.assertEquals(result, expected)

        u.unregister(obj)
        u.unregister(obj2)
        self.assertEquals(len(u), 0)
        self.assertEquals(u.items(), [])

    def test_getenrateId(self):
        u = IntIds()
        self.assertEquals(u._v_nextid, None)
        id1 = u._generateId()
        self.assert_(u._v_nextid is not None)
        id2 = u._generateId()
        self.assert_(id1 + 1, id2)
        u.refs[id2 + 1] = "Taken"
        id3 = u._generateId()
        self.assertNotEqual(id3, id2 + 1)
        self.assertNotEqual(id3, id2)
        self.assertNotEqual(id3, id1)


class TestSubscribers(ReferenceSetupMixin, unittest.TestCase):

    def setUp(self):
        from zope.app.folder import Folder, rootFolder

        ReferenceSetupMixin.setUp(self)

        sm = zapi.getSiteManager(self.root)
        self.utility = setup.addUtility(sm, '1', IIntIds, IntIds())

        self.root['folder1'] = Folder()
        self.root._p_jar = ConnectionStub()
        self.root['folder1']['folder1_1'] = self.folder1_1 = Folder()
        self.root['folder1']['folder1_1']['folder1_1_1'] = Folder()

        sm1_1 = setup.createSiteManager(self.folder1_1)
        self.utility1 = setup.addUtility(sm1_1, '2', IIntIds, IntIds())

    def test_removeIntIdSubscriber(self):
        from zope.app.intid import removeIntIdSubscriber
        from zope.app.container.contained import ObjectRemovedEvent
        from zope.app.intid.interfaces import IIntIdRemovedEvent
        parent_folder = self.root['folder1']['folder1_1']
        folder = self.root['folder1']['folder1_1']['folder1_1_1']
        id = self.utility.register(folder)
        id1 = self.utility1.register(folder)
        self.assertEquals(self.utility.getObject(id), folder)
        self.assertEquals(self.utility1.getObject(id1), folder)
        setSite(self.folder1_1)

        events = []
        ztapi.subscribe([IIntIdRemovedEvent], None, events.append)

        # This should unregister the object in all utilities, not just the
        # nearest one.
        removeIntIdSubscriber(folder, ObjectRemovedEvent(parent_folder))

        self.assertRaises(KeyError, self.utility.getObject, id)
        self.assertRaises(KeyError, self.utility1.getObject, id1)

        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].object, folder)
        self.assertEquals(events[0].original_event.object, parent_folder)

    def test_addIntIdSubscriber(self):
        from zope.app.intid import addIntIdSubscriber
        from zope.app.container.contained import ObjectAddedEvent
        from zope.app.intid.interfaces import IIntIdAddedEvent
        parent_folder = self.root['folder1']['folder1_1']
        folder = self.root['folder1']['folder1_1']['folder1_1_1']
        setSite(self.folder1_1)

        events = []
        ztapi.subscribe([IIntIdAddedEvent], None, events.append)

        # This should register the object in all utilities, not just the
        # nearest one.
        addIntIdSubscriber(folder, ObjectAddedEvent(parent_folder))

        # Check that the folder got registered
        id = self.utility.getId(folder)
        id1 = self.utility1.getId(folder)

        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].original_event.object, parent_folder)
        self.assertEquals(events[0].object, folder)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIntIds))
    suite.addTest(unittest.makeSuite(TestSubscribers))
    return suite

if __name__ == '__main__':
    unittest.main()

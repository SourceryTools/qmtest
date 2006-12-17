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
"""ZODB Undo-manager tests

$Id: test_zodbundomanager.py 68942 2006-07-02 10:18:06Z philikon $
"""
from time import time
from unittest import TestCase, main, makeSuite
import transaction

import zope.component
from zope.interface import implements
from zope.testing.cleanup import CleanUp
from zope.component import getUtility
from zope.component.registry import Components
from zope.component.testing import PlacelessSetup
from zope.location import Location
from zope.location.traversing import LocationPhysicallyLocatable
from zope.security.interfaces import IPrincipal

from zope.app.security.principalregistry import PrincipalRegistry
from zope.app.component import queryNextUtility
from zope.app.component.hooks import setSite, setHooks
from zope.app.component.interfaces import ISite
from zope.app.component.site import SiteManagerAdapter
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError

from zope.app.undo import ZODBUndoManager
from zope.app.undo.interfaces import UndoError

testdata = [
    dict(id='1', user_name='/ jim', time=time(), description='des 1',
         location=u'/spam\N{CYRILLIC CAPITAL LETTER A}/1'),
    dict(id='2', user_name='/ jim', time=time(), description='des 2',
         location=u'/parrot/2'),
    dict(id='3', user_name='/ anthony', time=time(), description='des 3',
         location=u'/spam\N{CYRILLIC CAPITAL LETTER A}/spam/3'),
    dict(id='4', user_name='/ jim', time=time(), description='des 4',
         location=u'/spam\N{CYRILLIC CAPITAL LETTER A}/parrot/4'),
    dict(id='5', user_name='/ anthony', time=time(), description='des 5'),
    dict(id='6', user_name='/ anthony', time=time(), description='des 6'),
    dict(id='7', user_name='/ jim', time=time(), description='des 7',
         location=u'/spam\N{CYRILLIC CAPITAL LETTER A}/7'),
    dict(id='8', user_name='/ anthony', time=time(), description='des 8'),
    dict(id='9', user_name='/ jim', time=time(), description='des 9'),
    dict(id='10', user_name='/ jim', time=time(), description='des 10'),
    dict(id='11', user_name='/ local.marco', time=time(),
         description='des 11'),
    ]
testdata.reverse()

class StubDB(object):

    def __init__(self):
        self.data = list(testdata)

    def undoInfo(self, first=0, last=-20, specification=None):
        if last < 0:
            last = first - last + 1
        # This code ripped off from zodb.storage.base.BaseStorage.undoInfo
        if specification:
            def filter(desc, spec=specification.items()):
                for k, v in spec:
                    if desc.get(k) != v:
                        return False
                return True
        else:
            filter = None
        if not filter:
            # handle easy case first
            data = self.data[first:last]
        else:
            data = []
            for x in self.data[first:]:
                if filter(x): 
                    data.append(x)
                if len(data) >= last:
                    break
        return data

    def undo(self, id):
        self.data = [d for d in self.data if d['id'] != id]


class StubSite(Location):
    implements(ISite)

    def __init__(self):
        self._sm = Components(bases=(zope.component.getGlobalSiteManager(),))

    def getSiteManager(self):
        return self._sm

class StubPrincipal(object):
    implements(IPrincipal)

    def __init__(self, id, title=u'', description=u''):
        self.id = id
        self.title = title
        self.description = description

class LocalPrincipalRegistry(PrincipalRegistry, Location):

    def getPrincipal(self, id):
        try:
            return super(LocalPrincipalRegistry, self).getPrincipal(id)
        except PrincipalLookupError:
            next = queryNextUtility(self, IAuthentication)
            if next is not None:
                return next.getPrincipal(id)
            raise PrincipalLookupError(id)

class Test(PlacelessSetup, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        zope.component.provideAdapter(LocationPhysicallyLocatable)
        zope.component.provideAdapter(SiteManagerAdapter)

        # define global principals
        from zope.app.security.principalregistry import principalRegistry
        principalRegistry.definePrincipal('jim', 'Jim Fulton', login='jim')
        principalRegistry.definePrincipal('anthony', 'Anthony Baxter',
                                          login='anthony')
        zope.component.provideUtility(principalRegistry, IAuthentication)

        # make a local authentication utility in an active site
        site = StubSite()
        setSite(site)
        setHooks()
        localPrincipalRegistry = LocalPrincipalRegistry()
        localPrincipalRegistry.definePrincipal('local.marco', 'Marco Mariani',
                                               login=u'marco')
        site.getSiteManager().registerUtility(localPrincipalRegistry,
                                              IAuthentication)
        localPrincipalRegistry.__parent__ = site

        self.undo = ZODBUndoManager(StubDB())
        self.data = list(testdata)

    def testGetTransactions(self):
        self.assertEqual(list(self.undo.getTransactions()), self.data)

    def testGetPrincipalTransactions(self):
        self.assertRaises(TypeError, self.undo.getPrincipalTransactions, None)

        jim = getUtility(IAuthentication).getPrincipal('jim')
        expected = [d for d in self.data if d['user_name'] == '/ jim']
        self.assertEqual(list(self.undo.getPrincipalTransactions(jim)),
                         expected)

        # now try with a "local" principal
        marco = getUtility(IAuthentication).getPrincipal('local.marco')
        expected = [d for d in self.data if d['user_name'] == '/ local.marco']
        self.assertEqual(list(self.undo.getPrincipalTransactions(marco)),
                         expected)

    def testGetTransactionsInLocation(self):
        from zope.interface import directlyProvides
        from zope.location import Location
        from zope.traversing.interfaces import IContainmentRoot

        root = Location()
        spam = Location()
        spam.__name__ = u'spam\N{CYRILLIC CAPITAL LETTER A}'
        spam.__parent__ = root
        directlyProvides(root, IContainmentRoot)

        expected = [dict for dict in self.data if 'location' in dict
                    and dict['location'].startswith(
                        u'/spam\N{CYRILLIC CAPITAL LETTER A}')]
        self.assertEqual(list(self.undo.getTransactions(spam)), expected)

        # now test this with getPrincipalTransactions()
        jim = getUtility(IAuthentication).getPrincipal('jim')
        expected = [dict for dict in expected if dict['user_name'] == '/ jim']
        self.assertEqual(list(self.undo.getPrincipalTransactions(jim, spam)),
                         expected)

    def testUndoTransactions(self):
        ids = ('3','4','5')
        self.undo.undoTransactions(ids)
        expected = [d for d in testdata if (d['id'] not in ids)]
        self.assertEqual(list(self.undo.getTransactions()), expected)

        # assert that the transaction has been annotated
        txn = transaction.get()
        self.assert_(txn._extension.has_key('undo'))
        self.assert_(txn._extension['undo'] is True)

    def testUndoPrincipalTransactions(self):
        self.assertRaises(TypeError, self.undo.undoPrincipalTransactions,
                          None, [])
        
        jim = getUtility(IAuthentication).getPrincipal('jim')
        self.assertRaises(UndoError, self.undo.undoPrincipalTransactions,
                          jim, ('1','2','3'))

        ids = ('1', '2', '4')
        self.undo.undoPrincipalTransactions(jim, ids)
        expected = [d for d in testdata if (d['id'] not in ids)]
        self.assertEqual(list(self.undo.getTransactions()), expected)

    def testUndoLocalPrincipalTransactions(self):
        # try the same thing with a "local" principal
        marco = getUtility(IAuthentication).getPrincipal('local.marco')
        self.assertRaises(UndoError, self.undo.undoPrincipalTransactions,
                          marco, ('10','11'))

        ids = ('11',)
        self.undo.undoPrincipalTransactions(marco, ids)
        expected = [d for d in testdata if (d['id'] not in ids)]
        self.assertEqual(list(self.undo.getTransactions()), expected)

    def testUndoStubPrincipalTransactions(self):
        # try it with a "made-up" principal
        anthony = StubPrincipal('anthony')
        ids = ('3', '5', '6', '8')
        self.undo.undoPrincipalTransactions(anthony, ids)
        expected = [d for d in testdata if (d['id'] not in ids)]
        self.assertEqual(list(self.undo.getTransactions()), expected)

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

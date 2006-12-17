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
"""Undo Tests

$Id: test_undoview.py 29143 2005-02-14 22:43:16Z srichter $
"""
from datetime import datetime
from unittest import TestCase, main, makeSuite

from zope.interface import implements
from zope.publisher.browser import TestRequest

from zope.app.testing import ztapi
from zope.app.component.testing import PlacefulSetup
from zope.app.undo.interfaces import IUndoManager
from zope.app.undo.browser import UndoView
from zope.app.security.principalregistry import principalRegistry

class TestIUndoManager(object):
    implements(IUndoManager)

    def __init__(self):
        self.dummy_db = [
            dict(id='1', user_name='monkey', description='thing1',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            dict(id='2', user_name='monkey', description='thing2',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            dict(id='3', user_name='bonobo', description='thing3',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            dict(id='4', user_name='monkey', description='thing4',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            dict(id='5', user_name='bonobo', description='thing5',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            dict(id='6', user_name='bonobo', description='thing6',
                 time='today', datetime=datetime(2001, 01, 01, 12, 00, 00)),
            ]
        self.dummy_db.reverse()

    def getTransactions(self, context=None, first=0, last=-20):
        self.context = context
        list = [dict for dict in self.dummy_db
                if not dict.get('undone', False)]
        return list[first:abs(last)]

    def getPrincipalTransactions(self, principal, context=None,
                                 first=0, last=-20):
        self.principal = principal
        self.context = context
        list = [dict for dict in self.dummy_db
               if dict['user_name'] == principal.id
               and not dict.get('undone', False)]
        return list[first:abs(last)]

    def _emulatePublication(self, request):
        self._user_name = request.principal.id

    def undoTransactions(self, ids):
        # just remove an element for now
        for db_record in self.dummy_db:
            if db_record['id'] in ids:
                db_record['undone'] = True

        self.dummy_db.insert(0, dict(
            id=str(len(self.dummy_db)+1), user_name=self._user_name,
            description='undo', undo=True,
            datetime=datetime(2001, 01, 01, 12, 00, 00)
            ))

    def undoPrincipalTransactions(self, principal, ids):
        self.principal = principal
        self.undoTransactions(ids)

class Test(PlacefulSetup, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        self.request = TestRequest()
        self.undo = TestIUndoManager()
        ztapi.provideUtility(IUndoManager, self.undo)
        principalRegistry.definePrincipal('monkey', 'Monkey Patch',
                                          login='monkey')
        principalRegistry.definePrincipal('bonobo', 'Bonobo Abdul-Fasil',
                                          login='bonobo')

    def testPrincipalLastTransactionIsUndo(self):
        request = self.request
        bonobo = principalRegistry.getPrincipal('bonobo')
        request.setPrincipal(bonobo)

        view = UndoView(self.folder1, request)
        self.failIf(view.principalLastTransactionIsUndo())

        # now undo the last transaction
        self.undo._emulatePublication(request)
        self.undo.undoTransactions(['6'])

        self.assert_(view.principalLastTransactionIsUndo())

    def testUndoPrincipalLastTransaction(self):
        request = self.request
        bonobo = principalRegistry.getPrincipal('bonobo')
        request.setPrincipal(bonobo)

        self.undo._emulatePublication(request)
        view = UndoView(self.folder1, request)
        view.undoPrincipalLastTransaction()

        last_txn = self.undo.getTransactions(None, 0, 1)[0]
        self.assert_(last_txn.has_key('undo'))
        self.assert_(last_txn['undo'])
        self.assertEqual(last_txn['user_name'], bonobo.id)

    def testGetAllTransactions(self):
        request = self.request
        view = UndoView(self.folder1, request)
        expected = self.undo.getTransactions()
        self.assertEqual(view.getAllTransactions(), expected)
        self.assert_(self.undo.context is self.folder1)

        # test showall parameter
        view.getAllTransactions(showall=True)
        self.assert_(self.undo.context is None)

    def testGetPrincipalTransactions(self):
        request = self.request
        bonobo = principalRegistry.getPrincipal('bonobo')
        request.setPrincipal(bonobo)

        view = UndoView(self.folder1, request)
        expected = self.undo.getPrincipalTransactions(bonobo)
        self.assertEqual(view.getPrincipalTransactions(), expected)
        self.assert_(self.undo.context is self.folder1)
        self.assert_(self.undo.principal is bonobo)

        # test showall parameter and principal
        self.undo.principal = None
        view.getPrincipalTransactions(showall=True)
        self.assert_(self.undo.context is None)
        self.assert_(self.undo.principal is bonobo)

    def testUndoPrincipalTransactions(self):
        request = self.request
        bonobo = principalRegistry.getPrincipal('bonobo')
        request.setPrincipal(bonobo)
        view = UndoView(self.folder1, request)

        # Just test whether it accepts the principal.  We know that
        # our undo dummy above "works".
        self.undo._emulatePublication(request)
        view.undoPrincipalTransactions(['6'])
        self.assert_(self.undo.principal is bonobo)

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

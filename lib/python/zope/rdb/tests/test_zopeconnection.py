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
"""Test Zope Connection component

$Id: test_zopeconnection.py 66859 2006-04-11 17:32:49Z jinty $
"""
from unittest import TestCase, main, makeSuite
import transaction
from zope.rdb import ZopeConnection
from zope.rdb.interfaces import IZopeCursor
from zope.rdb.tests.stubs import ConnectionStub, TypeInfoStub

class ZopeConnectionTests(TestCase):

    def test_cursor(self):
        zc = ZopeConnection(ConnectionStub(), TypeInfoStub())
        cursor = zc.cursor()

        self.failUnless(IZopeCursor.providedBy(cursor),
                        "cursor is not what we expected")

    def test_connection_txn_registration(self):
        transaction.begin()

        zc = ZopeConnection(ConnectionStub(), TypeInfoStub())
        cursor = zc.cursor()
        cursor.execute('select * from blah')

        self.assertEqual(zc._txn_registered, True)
        self.assertEqual(len(transaction.get()._resources), 1)

    def test_commit(self):
        transaction.begin()
        zc = ZopeConnection(ConnectionStub(), TypeInfoStub())
        self._txn_registered = True
        zc.commit()
        self.assertEqual(zc._txn_registered, False,
                         "did not forget the transaction")

    def test_rollback(self):
        transaction.begin()
        zc = ZopeConnection(ConnectionStub(), TypeInfoStub())
        self._txn_registered = True
        zc.rollback()
        self.assertEqual(zc._txn_registered, False,
                         "did not forget the transaction")

    def test_getattr(self):
        zc = ZopeConnection(ConnectionStub(), TypeInfoStub())
        cursor = zc.cursor()

        self.assertEqual(zc.answer(), 42)

    def tearDown(self):
        "Abort the transaction"
        transaction.abort()

def test_suite():
    return makeSuite(ZopeConnectionTests)

if __name__=='__main__':
    main(defaultTest='test_suite')

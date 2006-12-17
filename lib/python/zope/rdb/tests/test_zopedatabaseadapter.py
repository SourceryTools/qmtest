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
"""Database adapter stubs for testing.

$Id: test_zopedatabaseadapter.py 66859 2006-04-11 17:32:49Z jinty $
"""
import unittest
from zope.rdb import ZopeDatabaseAdapter
from zope.rdb import ZopeConnection
from threading import Thread

class ConnectionStub(object):

    def close(self):
        pass


class DAStub(ZopeDatabaseAdapter):

    def _connection_factory(self):
        return ConnectionStub()


class TestZopeDatabaseAdapter(unittest.TestCase):

    def setUp(self):
        self._da = DAStub('dbi://test')

    def testSetGetDSN(self):
        da = self._da
        da.setDSN('dbi://foo')
        self.assertEqual('dbi://foo', da.dsn)
        self.assertEqual('dbi://foo', da.getDSN())

    def testConnect(self):
        da = self._da
        da.connect()
        self.assertEqual(ZopeConnection, da._v_connection.__class__)

    def testDisconnect(self):
        da = self._da
        da.disconnect()
        self.assertEqual(None, da._v_connection)
        da.connect()
        da.disconnect()
        self.assertEqual(None, da._v_connection)

    def testIsConnected(self):
        da = self._da
        da.connect()
        self.assertEqual(1, da.isConnected())
        da.disconnect()
        self.assertEqual(0, da.isConnected())

    def testCall(self):
        da = self._da
        conn = da()
        self.assertEqual(ZopeConnection, conn.__class__)

    def testGetConverter(self):
        from zope.rdb import identity
        da = self._da
        conv = da.getConverter('any')
        self.assert_(conv is identity, "default converter is wrong")

    def testThreading(self):
        # Ensure that different threads get distinct connections
        cons = []
        def get_con():
            self._da.connect()
            cons.append(self._da._v_connection)
        get_con()
        t = Thread(target=get_con)
        t.start()
        t.join()
        self.failUnlessEqual(len(cons), 2)
        self.failIfEqual(id(cons[0]), id(cons[1]))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZopeDatabaseAdapter))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

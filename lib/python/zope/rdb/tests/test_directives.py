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
"""Test 'rdb' ZCML Namespace Directives

$Id: test_directives.py 66859 2006-04-11 17:32:49Z jinty $
"""
import unittest
from zope.component.testing import PlacelessSetup
from zope.component import getUtilitiesFor, queryUtility
from zope.configuration import xmlconfig
from zope.rdb.interfaces import IZopeDatabaseAdapter
from zope.rdb.tests.test_zopedatabaseadapter import DAStub
from zope.rdb import ZopeConnection
import zope.rdb.tests

class DirectivesTest(PlacelessSetup, unittest.TestCase):

    def test_provideConnection(self):

        conns = list(getUtilitiesFor(IZopeDatabaseAdapter))
        self.assertEqual(conns, [])
        connectionstub = queryUtility(IZopeDatabaseAdapter, 'stub')
        self.assertEqual(connectionstub, None)

        self.context = xmlconfig.file("rdb.zcml", zope.rdb.tests)
        connectionstub = queryUtility(IZopeDatabaseAdapter, 'stub')
        connection = connectionstub()
        self.assertEqual(connectionstub.__class__, DAStub)
        conns = getUtilitiesFor(IZopeDatabaseAdapter)
           
        self.assertEqual([c[0] for c in conns], ["stub"])
        self.assertEqual(connection.__class__, ZopeConnection)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectivesTest),
        ))

if __name__ == '__main__':
    unittest.main()

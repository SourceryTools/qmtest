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
"""Test 'xmlrpc' ZCML Namespace directives.

$Id: test_directives.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

from zope.configuration import xmlconfig
from zope.configuration.exceptions import ConfigurationError
from zope.app.component.tests.views import Request, IC, V1
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.security.proxy import ProxyFactory
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest

from zope.app import zapi
from zope.app.publisher import xmlrpc
from zope.interface import implements


request = Request(IXMLRPCRequest)

class Ob(object):
    implements(IC)

ob = Ob()

class DirectivesTest(PlacelessSetup, unittest.TestCase):

    def testView(self):
        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name='test'), None)
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        view = zapi.queryMultiAdapter((ob, request), name='test')
        self.assert_(V1 in view.__class__.__bases__)
        self.assert_(xmlrpc.MethodPublisher in view.__class__.__bases__)

    def testInterfaceProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = zapi.getMultiAdapter((ob, request), name='test2')
        v = ProxyFactory(v)
        self.assertEqual(v.index(), 'V1 here')
        self.assertRaises(Exception, getattr, v, 'action')

    def testAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = zapi.getMultiAdapter((ob, request), name='test3')
        v = ProxyFactory(v)
        self.assertEqual(v.action(), 'done')
        self.assertRaises(Exception, getattr, v, 'index')

    def testInterfaceAndAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = zapi.getMultiAdapter((ob, request), name='test4')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testDuplicatedInterfaceAndAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = zapi.getMultiAdapter((ob, request), name='test5')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testIncompleteProtectedView(self):
        self.assertRaises(ConfigurationError, xmlconfig.file,
                          "xmlrpc_error.zcml", xmlrpc.tests)

    def testNoPermission(self):
        self.assertRaises(ConfigurationError, xmlconfig.file,
                          "xmlrpc_noperm.zcml", xmlrpc.tests)

    def test_no_name(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = zapi.getMultiAdapter((ob, request), name='index')
        self.assertEqual(v(), 'V1 here')
        v = zapi.getMultiAdapter((ob, request), name='action')
        self.assertEqual(v(), 'done')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectivesTest),
        ))

if __name__ == '__main__':
    unittest.main()

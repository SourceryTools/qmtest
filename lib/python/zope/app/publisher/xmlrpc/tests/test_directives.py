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

$Id: test_directives.py 78108 2007-07-18 14:06:28Z ctheune $
"""
import unittest

from zope import component
from zope.configuration import xmlconfig
from zope.configuration.exceptions import ConfigurationError
from zope.app.component.tests.views import Request, IC, V1
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.security.proxy import ProxyFactory
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest

from zope.app.publisher import xmlrpc
from zope.interface import implements


request = Request(IXMLRPCRequest)

class Ob(object):
    implements(IC)

ob = Ob()

class DirectivesTest(PlacelessSetup, unittest.TestCase):

    def testView(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'), None)
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        view = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(V1 in view.__class__.__bases__)
        self.assert_(xmlrpc.MethodPublisher in view.__class__.__bases__)

    def testInterfaceProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='test2')
        v = ProxyFactory(v)
        self.assertEqual(v.index(), 'V1 here')
        self.assertRaises(Exception, getattr, v, 'action')

    def testAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='test3')
        v = ProxyFactory(v)
        self.assertEqual(v.action(), 'done')
        self.assertRaises(Exception, getattr, v, 'index')

    def testInterfaceAndAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='test4')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testDuplicatedInterfaceAndAttributeProtectedView(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='test5')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testIncompleteProtectedView(self):
        self.assertRaises(ConfigurationError, xmlconfig.file,
                          "xmlrpc_error.zcml", xmlrpc.tests)

    def testNoPermission(self):
        xmlconfig.file("xmlrpc_noperm.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='index')
        self.assertEqual(v.index(), 'V1 here')

    def test_no_name_no_permission(self):
        self.assertRaises(ConfigurationError, xmlconfig.file,
                          "xmlrpc_nonamenoperm.zcml", xmlrpc.tests)

    def test_no_name(self):
        xmlconfig.file("xmlrpc.zcml", xmlrpc.tests)
        v = component.getMultiAdapter((ob, request), name='index')
        self.assertEqual(v(), 'V1 here')
        v = component.getMultiAdapter((ob, request), name='action')
        self.assertEqual(v(), 'done')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectivesTest),
        ))

if __name__ == '__main__':
    unittest.main()

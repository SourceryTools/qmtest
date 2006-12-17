##############################################################################
#
# Copyright (c) 2003, 2004 Zope Corporation and Contributors.
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
"""Functional Tests for Interface Documentation Module.

$Id: ftests.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.app.testing.functional import BrowserTestCase

class InterfaceModuleTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish(
            '/++apidoc++/Interface/menu.html',
            basic='mgr:mgrpw',
            env = {'name_only': True, 'search_str': 'IDoc'})
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find(
            'zope.app.apidoc.interfaces.IDocumentationModule') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/Interface/menu.html',
                                 basic='mgr:mgrpw')

    def testInterfaceDetailsView(self):
        response = self.publish(
            '/++apidoc++/Interface'
            '/zope.app.apidoc.ifacemodule.ifacemodule.IInterfaceModule'
            '/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Interface API Documentation Module') > 0)
        self.checkForBrokenLinks(
            body,
            '/++apidoc++/Interface'
            '/zope.app.apidoc.ifacemodule.IInterfaceModule'
            '/index.html',
            basic='mgr:mgrpw')



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(InterfaceModuleTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

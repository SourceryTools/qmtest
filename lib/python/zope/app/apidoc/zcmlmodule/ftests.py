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
"""Functional Tests for ZCML Documentation Module.

$Id: ftests.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.app.testing.functional import BrowserTestCase

class ZCMLModuleTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish(
            '/++apidoc++/ZCML/menu.html', 
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('All Namespaces') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/ZCML/menu.html',
                                 basic='mgr:mgrpw')

    def testDirectiveDetailsView(self):
        response = self.publish('/++apidoc++/ZCML/ALL/configure/index.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('<i>all namespaces</i>') > 0)
        self.checkForBrokenLinks(body,
                                 '/++apidoc++/ZCML/ALL/configure/index.html',
                                 basic='mgr:mgrpw')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZCMLModuleTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

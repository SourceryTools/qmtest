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
"""Functional Tests for Code Documentation Module.

$Id: ftests.py 39468 2005-10-15 23:27:58Z srichter $
"""
import unittest

from zope.testing import doctest
from zope.app.testing.functional import BrowserTestCase
from zope.app.testing.functional import FunctionalDocFileSuite

class CodeModuleTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish('/++apidoc++/Code/menu.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Zope Source') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/Code/menu.html',
                                 basic='mgr:mgrpw')

    def testMenuCodeFinder(self):
        response = self.publish('/++apidoc++/Code/menu.html',
                                basic='mgr:mgrpw',
                                form={'path': 'Code', 'SUBMIT': 'Find'})
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(
            body.find('zope.app.apidoc.codemodule.codemodule.CodeModule') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/Code/menu.html',
                                 basic='mgr:mgrpw')

    def testModuleDetailsView(self):
        response = self.publish('/++apidoc++/Code/zope/app/apidoc/apidoc',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Zope 3 API Documentation') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc', basic='mgr:mgrpw')

    def testClassDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/apidoc/APIDocumentation',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Represent the complete API Documentation.') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc/APIDocumentation',
            basic='mgr:mgrpw')

    def testFunctionDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/apidoc/handleNamespace',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('handleNamespace(ob, name)') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc/handleNamesapce',
            basic='mgr:mgrpw')

    def testTextFileDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/README.txt/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/README.txt/index.html',
            basic='mgr:mgrpw')

    def testZCMLFileDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/configure.zcml/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/configure.zcml/index.html',
            basic='mgr:mgrpw')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CodeModuleTests),
        FunctionalDocFileSuite(
            "introspector.txt",
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

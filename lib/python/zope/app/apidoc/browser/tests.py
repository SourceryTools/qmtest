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
"""Functional Tests for API Documentation.

$Id: tests.py 80813 2007-10-11 03:13:44Z srichter $
"""
import re
import unittest

import zope.app.testing.functional
from zope.testing import doctest
from zope.testing import renormalizing
from zope.app.testing.functional import BrowserTestCase, FunctionalNoDevMode
from zope.app.testing.functional import FunctionalDocFileSuite
from zope.app.apidoc.testing import APIDocLayer, APIDocNoDevModeLayer

class APIDocTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish('/++apidoc++/menu.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Click on one of the Documentation') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/menu.html',
                                 basic='mgr:mgrpw')

    def testIndexView(self):
        response = self.publish('/++apidoc++/index.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Zope 3 API Documentation') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/index.html',
                                 basic='mgr:mgrpw')

    def testContentsView(self):
        response = self.publish('/++apidoc++/contents.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('<h1>Zope 3 API Documentation</h1>') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/contents.html',
                                 basic='mgr:mgrpw')

    def testModuleListView(self):
        response = self.publish('/++apidoc++/modulelist.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find(
            '<a href="contents.html" target="main">Zope') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/modulelist.html',
                                 basic='mgr:mgrpw')

checker = renormalizing.RENormalizing([
    (re.compile(r'httperror_seek_wrapper:', re.M), 'HTTPError:'),
    ]) 

def test_suite():
    suite = unittest.TestSuite()
    APIDocTests.layer = APIDocLayer
    suite.addTest(unittest.makeSuite(APIDocTests))
    apidoc_doctest = FunctionalDocFileSuite(
        "README.txt",
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
        checker=checker)
    apidoc_doctest.layer = APIDocLayer
    suite.addTest(
        apidoc_doctest,
        )

    nodevmode = FunctionalDocFileSuite("nodevmode.txt")
    nodevmode.layer = APIDocNoDevModeLayer
    suite.addTest(nodevmode)
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

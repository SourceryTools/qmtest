##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Tests for the Utility Documentation Module

$Id: tests.py 80813 2007-10-11 03:13:44Z srichter $
"""
import unittest
import zope.deprecation
from zope.testing import doctest, doctestunit
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location.traversing import LocationPhysicallyLocatable

from zope.app.apidoc.testing import APIDocLayer
from zope.app.testing import placelesssetup, ztapi
from zope.app.testing.functional import BrowserTestCase
from zope.app.tree.interfaces import IUniqueId
from zope.app.tree.adapters import LocationUniqueId

def setUp(test):
    placelesssetup.setUp()

    ztapi.provideAdapter(None, IUniqueId, LocationUniqueId)
    ztapi.provideAdapter(None, IPhysicallyLocatable,
                         LocationPhysicallyLocatable)


class UtilityModuleTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish(
            '/++apidoc++/Utility/menu.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('IDocumentationModule') > 0)

        # BBB 2006/02/18, to be removed after 12 months
        # this avoids the deprecation warning for the deprecated
        # zope.publisher.interfaces.ILayer interface which get traversed
        # as a utility in this test
        zope.deprecation.__show__.off()
        self.checkForBrokenLinks(body, '/++apidoc++/Utility/menu.html',
                                 basic='mgr:mgrpw')
        zope.deprecation.__show__.on()

    def testUtilityDetailsView(self):
        response = self.publish(
            '/++apidoc++/Utility/'
            'zope.app.apidoc.interfaces.IDocumentationModule/'
            'Utility/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(
            body.find(
               'zope.app.apidoc.utilitymodule.utilitymodule.UtilityModule') > 0)
        self.checkForBrokenLinks(
            body,
            '/++apidoc++/Utility/'
            'zope.app.apidoc.interfaces.IDocumentationModule/'
            'Utility/index.html',
            basic='mgr:mgrpw')


def test_suite():
    UtilityModuleTests.layer = APIDocLayer
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE|
                                         doctest.ELLIPSIS),
        doctest.DocFileSuite('browser.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        unittest.makeSuite(UtilityModuleTests),
        ))

if __name__ == '__main__':
    unittest.main(default="test_suite")

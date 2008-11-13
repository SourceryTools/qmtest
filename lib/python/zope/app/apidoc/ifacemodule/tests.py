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
"""Tests for the Interface Documentation Module

$Id: tests.py 80813 2007-10-11 03:13:44Z srichter $
"""
import unittest

from zope.component.interfaces import IFactory
from zope.interface.interfaces import IInterface
from zope.testing import doctest, doctestunit

from zope.app.apidoc.testing import APIDocLayer
from zope.app.renderer.rest import ReStructuredTextSourceFactory
from zope.app.renderer.rest import IReStructuredTextSource
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer
from zope.app.testing import placelesssetup, ztapi, setup
from zope.app.testing.functional import BrowserTestCase
from zope.app.tree.interfaces import IUniqueId
from zope.app.tree.adapters import LocationUniqueId

def setUp(test):
    placelesssetup.setUp()
    setup.setUpTraversal()

    ztapi.provideAdapter(IInterface, IUniqueId, LocationUniqueId)

    # Register Renderer Components
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.rest')
    ztapi.browserView(IReStructuredTextSource, '',
                      ReStructuredTextToHTMLRenderer)
    # Cheat and register the ReST factory for STX as well
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.stx')


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
    InterfaceModuleTests.layer = APIDocLayer
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('browser.txt',
                             setUp=setUp, tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        unittest.makeSuite(InterfaceModuleTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

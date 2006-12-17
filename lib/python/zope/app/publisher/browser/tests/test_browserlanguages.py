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
"""Test Modifiable Browser Languages detector

$Id: test_browserlanguages.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

import zope.component
from zope.interface import directlyProvides
from zope.publisher.browser import BrowserLanguages
from zope.publisher.tests.test_browserlanguages import TestRequest
from zope.publisher.tests.test_browserlanguages import BrowserLanguagesTest
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.publisher.browser import CacheableBrowserLanguages
from zope.app.publisher.browser import ModifiableBrowserLanguages
from zope.app.publisher.browser import NotCompatibleAdapterError


class CacheableBrowserLanguagesTests(PlacelessSetup, BrowserLanguagesTest):

    def setUp(self):
        super(CacheableBrowserLanguagesTests, self).setUp()
        zope.component.provideAdapter(AttributeAnnotations)

    def factory(self, request):
        directlyProvides(request, IAttributeAnnotatable)
        return CacheableBrowserLanguages(request)

    def test_cached_languages(self):
        eq = self.failUnlessEqual
        request = TestRequest("da, en, pt")
        browser_languages = self.factory(request)
        eq(list(browser_languages.getPreferredLanguages()), ["da", "en", "pt"])
        request["HTTP_ACCEPT_LANGUAGE"] = "ru, en"
        eq(list(browser_languages.getPreferredLanguages()), ["da", "en", "pt"])

class ModifiableBrowserLanguagesTests(CacheableBrowserLanguagesTests):

    def factory(self, request):
        directlyProvides(request, IAttributeAnnotatable)
        return ModifiableBrowserLanguages(request)

    def test_setPreferredLanguages(self):
        eq = self.failUnlessEqual
        request = TestRequest("da, en, pt")
        browser_languages = self.factory(request)
        eq(list(browser_languages.getPreferredLanguages()), ["da", "en", "pt"])
        browser_languages.setPreferredLanguages(["ru", "en"])
        self.failUnless(request.localized)
        eq(list(browser_languages.getPreferredLanguages()), ["ru", "en"])

    def test_conflicting_adapters(self):
        request = TestRequest("da, en, pt")
        not_compatible_browser_languages = BrowserLanguages(request)
        browser_languages = self.factory(request)
        self.assertRaises(NotCompatibleAdapterError,
            browser_languages.setPreferredLanguages, ["ru", "en"])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CacheableBrowserLanguagesTests))
    suite.addTest(unittest.makeSuite(ModifiableBrowserLanguagesTests))
    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

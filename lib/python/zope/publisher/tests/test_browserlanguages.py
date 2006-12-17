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
"""Test Browser Languages detector

$Id: test_browserlanguages.py 39906 2005-11-05 12:16:38Z hdima $
"""
import unittest

from zope.publisher.browser import BrowserLanguages


# Note: The expected output is in order of preference,
# empty 'q=' means 'q=1', and if theres more than one
# empty, we assume they are in order of preference.
data = [
    ('da, en, pt', ['da', 'en', 'pt']),
    ('da, en;q=.9, en-gb;q=1.0, en-us', ['da', 'en-gb', 'en-us', 'en']),
    ('pt_BR; q=0.6, pt_PT; q = .7, en-gb', ['en-gb', 'pt-pt', 'pt-br']),
    ('en-us, en_GB;q=0.9, en, pt_BR; q=1.0', ['en-us', 'en', 'pt-br', 'en-gb']),
    ('ro,en-us;q=0.8,es;q=0.5,fr;q=0.3', ['ro', 'en-us', 'es', 'fr']),
    ('ro,en-us;q=0,es;q=0.5,fr;q=0,ru;q=1,it', ['ro', 'ru', 'it', 'es'])
    ]

class TestRequest(dict):

    def __init__(self, languages):
        self.annotations = {}
        self.localized = False
        self["HTTP_ACCEPT_LANGUAGE"] = languages

    def setupLocale(self):
        self.localized = True

class BrowserLanguagesTest(unittest.TestCase):

    def factory(self, request):
        return BrowserLanguages(request)

    def test_browser_language_handling(self):
        for req, expected in data:
            request = TestRequest(req)
            browser_languages = self.factory(request)
            self.assertEqual(list(browser_languages.getPreferredLanguages()),
                             expected)


def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(BrowserLanguagesTest)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

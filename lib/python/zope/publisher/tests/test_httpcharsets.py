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
"""Retrieval of HTTP character set information.

$Id: test_httpcharsets.py 89074 2008-07-31 07:29:29Z andreasjung $
"""
import unittest

from zope.publisher.http import HTTPCharsets


class HTTPCharsetTest(unittest.TestCase):

    def testGetPreferredCharset(self):
        request = {'HTTP_ACCEPT_CHARSET':
                   'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['utf-8', 'iso-8859-1', 'utf-16'])

    def testGetPreferredCharsetOrdering(self):
        # test that the charsets are returned sorted according to
        # their "quality value"
        request = {'HTTP_ACCEPT_CHARSET':
                   'ISO-8859-1, UTF-16;Q=0.33, UTF-8;q=0.66'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['utf-8', 'iso-8859-1', 'utf-16'])

    def testGetPreferredCharsetBogusQuality(self):
        # test that handling of bogus "quality values" and non-quality
        # parameters is reasonable
        request = {'HTTP_ACCEPT_CHARSET':
                   'ISO-8859-1;x, UTF-16;Q=0.33, UTF-8;q=foo'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['iso-8859-1', 'utf-16'])

    def testNoStar(self):
        request = {'HTTP_ACCEPT_CHARSET': 'utf-16;q=0.66'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['iso-8859-1', 'utf-16'])

    def testStarNoUtf8(self):
        # If '*' is in HTTP_ACCEPT_CHARSET, but 'utf-8' isn't, we insert
        # utf-8 in the list, since we prefer that over any other #
        # charset.
        request = {'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, *'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['utf-8', 'iso-8859-1', '*'])

    def testStarAndUtf8(self):
        # If '*' and 'utf-8' are in HTTP_ACCEPT_CHARSET, we won't insert
        # an extra 'utf-8'.
        request = {'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, utf-8, *'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['utf-8', 'iso-8859-1', '*'])

    def testNoHTTP_ACCEPT_CHARSET(self):
        # If the client doesn't provide a HTTP_ACCEPT_CHARSET, it should
        # accept any charset
        request = {}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         [])

    def testTrivialHTTP_ACCEPT_CHARSET(self):
        # If the client provides a trivial HTTP_ACCEPT_CHARSET, it should
        # accept any charset (this test is aimed at Zope 2's handling
        # of request queries for entries starting with HTTP_
        # See: https://bugs.launchpad.net/zope2/+bug/143873
        request = {'HTTP_ACCEPT_CHARSET': ''}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         [])

    def testMalformedHTTP_ACCEPT_CHARSET(self):
        """ Test for Launchpad #253362 """
        request = {'HTTP_ACCEPT_CHARSET': 'utf-8;q=0.7,iso-8859-1;q=0.2*;q=0.1'}
        browser_charsets = HTTPCharsets(request)
        self.assertEqual(list(browser_charsets.getPreferredCharsets()),
                         ['utf-8', 'iso-8859-1'])

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(HTTPCharsetTest)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

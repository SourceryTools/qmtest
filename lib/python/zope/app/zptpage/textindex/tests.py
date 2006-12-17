##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Basic tests for Page Templates used in content-space.

$Id: tests.py 29143 2005-02-14 22:43:16Z srichter $
"""

from zope.index.text.interfaces import ISearchableText
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.zptpage.interfaces import IZPTPage
from zope.app.zptpage.textindex.zptpage import SearchableText
from zope.app.zptpage.zptpage import ZPTPage
import unittest

class ZPTPageTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(ZPTPageTests, self).setUp()
        ztapi.provideAdapter(IZPTPage, ISearchableText, SearchableText)

    def testSearchableText(self):
        page = ZPTPage()
        searchableText = ISearchableText(page)

        utext = u'another test\n' # The source will grow a newline if ommited
        html = u"<html><body>%s</body></html>\n" % (utext, )

        page.setSource(utext)
        self.failUnlessEqual(searchableText.getSearchableText(), [utext])

        page.setSource(html, content_type='text/html')
        self.assertEqual(searchableText.getSearchableText(), [utext+'\n'])

        page.setSource(html, content_type='text/plain')
        self.assertEqual(searchableText.getSearchableText(), [html])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZPTPageTests),
        ))

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

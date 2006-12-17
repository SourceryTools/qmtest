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
"""Session functional tests.

$Id: tests.py 26427 2004-07-12 16:05:02Z Zen $
"""
import unittest
from zope.component import provideHandler, getGlobalSiteManager
from zope.app.folder import Folder
from zope.app.publication.interfaces import IBeforeTraverseEvent
from zope.app.testing.functional import BrowserTestCase
from zope.app.zptpage.zptpage import ZPTPage

from interfaces import ISession

class ZPTSessionTest(BrowserTestCase):
    content = u'''
        <div tal:define="
                 session request/session:products.foo;
                 dummy python:session.__setitem__(
                        'count',
                        session.get('count', 0) + 1)
                 " tal:omit-tag="">
            <span tal:replace="session/count" />
        </div>
        '''

    def setUp(self):
        BrowserTestCase.setUp(self)
        page = ZPTPage()
        page.source = self.content
        page.evaluateInlineCode = True
        root = self.getRootFolder()
        root['page'] = page
        self.commit()

    def tearDown(self):
        root = self.getRootFolder()
        del root['page']
        BrowserTestCase.tearDown(self)

    def fetch(self, page='/page'):
        response = self.publish(page)
        self.failUnlessEqual(response.getStatus(), 200)
        return response.getBody().strip()

    def test(self):
        response1 = self.fetch()
        self.failUnlessEqual(response1, u'1')
        response2 = self.fetch()
        self.failUnlessEqual(response2, u'2')
        response3 = self.fetch()
        self.failUnlessEqual(response3, u'3')

class VirtualHostSessionTest(BrowserTestCase):
    def setUp(self):
        super(VirtualHostSessionTest, self).setUp()
        page = ZPTPage()
        page.source = (u'<div '
                       u'tal:define="session request/session:products.foo"/>')
        page.evaluateInlineCode = True
        root = self.getRootFolder()
        root['folder'] = Folder()
        root['folder']['page'] = page
        self.commit()
        
        provideHandler(self.accessSessionOnTraverse, (IBeforeTraverseEvent,))
        
    def tearDown(self):
        getGlobalSiteManager().unregisterHandler(self.accessSessionOnTraverse,
                                                 (IBeforeTraverseEvent,))
        
    def accessSessionOnTraverse(self, event):
        session = ISession(event.request)
        
    def assertCookiePath(self, path):
        cookie = self.cookies.values()[0]
        self.assertEqual(cookie['path'], path)
    
    def testShortendPath(self):
        self.publish(
            '/++skin++Rotterdam/folder/++vh++http:localhost:80/++/page')
        self.assertCookiePath('/')
        
    def testLongerPath(self):
        self.publish(
            '/folder/++vh++http:localhost:80/foo/bar/++/page')
        self.assertCookiePath('/foo/bar')
        
    def testDifferentHostname(self):
        self.publish(
            '/folder/++vh++http:foo.bar:80/++/page')
        self.assertCookiePath('/')
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZPTSessionTest),
        unittest.makeSuite(VirtualHostSessionTest),
        ))

if __name__ == '__main__':
    unittest.main()

# vim: set filetype=python ts=4 sw=4 et si


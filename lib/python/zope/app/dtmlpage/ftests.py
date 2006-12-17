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
"""Functional tests for DTML Page.

$Id: ftests.py 25177 2004-06-02 13:17:31Z jim $
"""
import unittest
from zope.app.testing.functional import BrowserTestCase
from zope.app.dtmlpage.dtmlpage import DTMLPage
from xml.sax.saxutils import escape

class DTMLPageTest(BrowserTestCase):

    content = u'<html><body><dtml-var "REQUEST.URL[1]"></body></html>' 

    def addDTMLPage(self):
        dtmlpage = DTMLPage(self.content)
        root = self.getRootFolder()
        root['dtmlpage'] = dtmlpage
        self.commit()

    def testAddForm(self):
        response = self.publish(
            '/+/zope.app.dtmlpage.DTMLPage=',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Add a DTML Page' in body)
        self.assert_('Source' in body)
        self.assert_('Object Name' in body)
        self.assert_('"Add"' in body)
        self.checkForBrokenLinks(body, '/+/zope.app.dtmlpage.DTMLPage=',
                                 'mgr:mgrpw')

    def testAdd(self):
        response = self.publish(
            '/+/zope.app.dtmlpage.DTMLPage=',
            form={'type_name': u'zope.app.dtmlpage.DTMLPage',
                  'field.source': u'<h1>A DTML Page</h1>',
                  'add_input_name': u'dtmlpage',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('dtmlpage' in root)
        dtmlpage = root['dtmlpage']
        self.assertEqual(dtmlpage.source, '<h1>A DTML Page</h1>')

    def testEditForm(self):
        self.addDTMLPage()
        response = self.publish(
            '/dtmlpage/@@edit.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Edit a DTML page' in body)
        self.assert_('Source' in body)
        self.assert_(escape(self.content) in body)
        self.checkForBrokenLinks(body, '/dtmlpage/@@edit.html', 'mgr:mgrpw')

    def testEdit(self):
        self.addDTMLPage()
        response = self.publish(
            '/dtmlpage/@@edit.html',
            form={'field.source': u'<h1>A DTML Page</h1>',
                  'UPDATE_SUBMIT': u'Edit'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Edit a DTML page' in body)
        self.assert_('Source' in body)
        self.assert_(escape(u'<h1>A DTML Page</h1>') in body)
        root = self.getRootFolder()
        dtmlpage = root['dtmlpage']
        self.assertEqual(dtmlpage.source, '<h1>A DTML Page</h1>')
        
    def testIndex(self):
        self.addDTMLPage()
        response = self.publish(
            '/dtmlpage/@@index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assertEqual(
            body,
            '<html><body>http://localhost/dtmlpage</body></html>')
        self.checkForBrokenLinks(body, '/dtmlpage/@@index.html', 'mgr:mgrpw')

    def testPreview(self):
        self.addDTMLPage()
        response = self.publish(
            '/dtmlpage/@@preview.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('<iframe src="."' in body)
        self.checkForBrokenLinks(body, '/dtmlpage/@@preview.html', 'mgr:mgrpw')


def test_suite():
    from zope.app.testing import functional
    return unittest.TestSuite((
        unittest.makeSuite(DTMLPageTest),
        functional.FunctionalDocFileSuite('url.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


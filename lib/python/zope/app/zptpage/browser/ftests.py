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
"""Functional tests for ZPT Page.

$Id: ftests.py 25177 2004-06-02 13:17:31Z jim $
"""
import unittest
from zope.app.testing.functional import BrowserTestCase
from zope.app.zptpage.zptpage import ZPTPage
from xml.sax.saxutils import escape

class ZPTPageTest(BrowserTestCase):

    content = u'<html><body><h1 tal:content="request/URL/1" /></body></html>' 

    def addZPTPage(self):
        zptpage = ZPTPage()
        zptpage.source = self.content
        root = self.getRootFolder()
        root['zptpage'] = zptpage
        self.commit()


    def testAddForm(self):
        response = self.publish(
            '/+/zope.app.zptpage.ZPTPage=',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Add a ZPT Page' in body)
        self.assert_('Source' in body)
        self.assert_('Expand macros' in body)
        self.assert_('Evaluate Inline Code' in body)
        self.assert_('Object Name' in body)
        self.assert_('"Add"' in body)
        self.checkForBrokenLinks(body, '/+/zope.app.zptpage.ZPTPage=',
                                 'mgr:mgrpw')


    def testAdd(self):
        response = self.publish(
            '/+/zope.app.zptpage.ZPTPage=',
            form={'type_name': u'zope.app.zptpage.ZPTPage',
                  'field.source': u'<h1>A ZPT Page</h1>',
                  'field.expand.used': u'',
                  'field.evaluateInlineCode.used': u'',
                  'add_input_name': u'zptpage',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('zptpage' in root)
        zptpage = root['zptpage']
        self.assertEqual(zptpage.source, '<h1>A ZPT Page</h1>')
        self.assertEqual(zptpage.expand, False)
        self.assertEqual(zptpage.evaluateInlineCode, False)

        response = self.publish(
            '/+/zope.app.zptpage.ZPTPage=',
            form={'type_name': u'zope.app.zptpage.ZPTPage',
                  'field.source': u'<h1>A ZPT Page</h1>\n',
                  'field.expand.used': u'',
                  'field.expand': u'on',
                  'field.evaluateInlineCode.used': u'',
                  'field.evaluateInlineCode': u'on',
                  'add_input_name': u'zptpage1',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        root = self.getRootFolder()
        zptpage = root['zptpage1']
        self.assertEqual(zptpage.source, '<h1>A ZPT Page</h1>\n')
        self.assertEqual(zptpage.expand, True)
        self.assertEqual(zptpage.evaluateInlineCode, True)


    def testEditForm(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@edit.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Source' in body)
        self.assert_('Expand macros' in body)
        self.assert_(escape(self.content) in body)
        self.checkForBrokenLinks(body, '/zptpage/@@edit.html', 'mgr:mgrpw')


    def testEdit(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@edit.html',
            form={'form.source': u'<h1>A ZPT Page</h1>\n',
                  'form.expand.used': u'',
                  'form.expand': u'on',
                  'form.actions.apply': u'Apply'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Source' in body)
        self.assert_(escape(u'<h1>A ZPT Page</h1>') in body)
        root = self.getRootFolder()
        zptpage = root['zptpage']
        self.assertEqual(zptpage.source, '<h1>A ZPT Page</h1>\n')
        self.assertEqual(zptpage.expand, True)

    def testIssue199(self):
        # This is a test to protect us against issue 199 in the future
        self.addZPTPage()
        source = u"""<html metal:use-macro="container/@@standard_macros/page">
         <body>
           <div metal:fill-slot="body">
            write this in the body slot.
           </div>
         </body>
         </html>"""

        response = self.publish(
            '/zptpage/@@edit.html',
            form={'form.source': source,
                  'form.expand.used': u'',
                  'form.expand': u'on',
                  'form.actions.apply': u'Apply'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        # Check for a string from the default template
        self.assert_(escape(u'Z3 UI') in body) 
        self.failIf(u"Macro expansion failed" in body)
        
    def testIndex(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBase(), '')
        body = response.getBody()
        self.assertEqual(
            body,
            '<html><body><h1>http://localhost/zptpage</h1></body></html>\n')
        self.checkForBrokenLinks(body, '/zptpage/@@index.html', 'mgr:mgrpw')

    def testPreview(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@preview.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('<iframe src="."' in body)
        self.checkForBrokenLinks(body, '/zptpage/@@preview.html', 'mgr:mgrpw')

    def testSource(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@source.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assertEqual(body, self.content)

    def testInlineCode(self):
        self.addZPTPage()
        response = self.publish(
            '/zptpage/@@inlineCode.html',
            form={'field.evaluateInlineCode.used': u'',
                  'field.evaluateInlineCode': u'on',
                  'UPDATE_SUBMIT': u'Edit'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Inline Code' in body)
        self.assert_('Evaluate Inline Code' in body)
        self.checkForBrokenLinks(body, '/zptpage/@@edit.html', 'mgr:mgrpw')

        response = self.publish(
            '/zptpage/@@inlineCode.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        root = self.getRootFolder()
        zptpage = root['zptpage']
        self.assertEqual(zptpage.evaluateInlineCode, True)


def test_suite():
    from zope.app.testing.functional import FunctionalDocFileSuite
    return unittest.TestSuite((
        unittest.makeSuite(ZPTPageTest),
        FunctionalDocFileSuite('collector266.txt', 'collector269.txt'),
        FunctionalDocFileSuite('url.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

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
"""Functional tests for File and Image.

$Id: ftests.py 25177 2004-06-02 13:17:31Z jim $
"""
import unittest
from xml.sax.saxutils import escape
from StringIO import StringIO

from zope.app.testing.functional import BrowserTestCase
from zope.app.file.file import File
from zope.app.file.image import Image
from zope.app.file.tests.test_image import zptlogo

class FileTest(BrowserTestCase):

    content = u'File <Data>'

    def addFile(self):
        file = File(self.content)
        root = self.getRootFolder()
        root['file'] = file
        self.commit()

    def testAddForm(self):
        response = self.publish(
            '/+/zope.app.file.File=',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Add a File' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_('Object Name' in body)
        self.assert_('"Add"' in body)
        self.checkForBrokenLinks(body, '/+/zope.app.file.File=',
                                 'mgr:mgrpw')

    def testAdd(self):
        response = self.publish(
            '/+/zope.app.file.File=',
            form={'type_name': u'zope.app.file.File',
                  'field.data': StringIO('A file'),
                  'field.data.used': '',
                  'add_input_name': u'file',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('file' in root)
        file = root['file']
        self.assertEqual(file.data, 'A file')

    def testAddWithoutName(self):
        data = StringIO('File Contents')
        data.filename="test.txt"
        response = self.publish(
            '/+/zope.app.file.File=',
            form={'type_name': u'zope.app.file.File',
                  'field.data': data,
                  'field.data.used': '',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('test.txt' in root)
        file = root['test.txt']
        self.assertEqual(file.data, 'File Contents')

    def testEditForm(self):
        self.addFile()
        response = self.publish(
            '/file/@@edit.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Change a file' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_(escape(self.content) in body)
        self.checkForBrokenLinks(body, '/file/@@edit.html', 'mgr:mgrpw')

    def testEdit(self):
        self.addFile()
        response = self.publish(
            '/file/@@edit.html',
            form={'field.data': u'<h1>A File</h1>',
                  'field.data.used': '',
                  'field.contentType': u'text/plain',
                  'UPDATE_SUBMIT': u'Edit'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Change a file' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_(escape(u'<h1>A File</h1>') in body)
        root = self.getRootFolder()
        file = root['file']
        self.assertEqual(file.data, '<h1>A File</h1>')
        self.assertEqual(file.contentType, 'text/plain')

    def testUploadForm(self):
        self.addFile()
        response = self.publish(
            '/file/@@upload.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Upload a file' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.failIf(escape(self.content) in body)
        self.checkForBrokenLinks(body, '/file/@@upload.html', 'mgr:mgrpw')

    def testUpload(self):
        self.addFile()
        response = self.publish(
            '/file/@@upload.html',
            form={'field.data': StringIO('<h1>A file</h1>'),
                  'field.data.used': '',
                  'field.contentType': u'text/plain',
                  'UPDATE_SUBMIT': u'Change'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Upload a file' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.failIf(escape(u'<h1>A File</h1>') in body)
        root = self.getRootFolder()
        file = root['file']
        self.assertEqual(file.data, '<h1>A file</h1>')
        self.assertEqual(file.contentType, 'text/plain')

    def testIndex(self):
        self.addFile()
        response = self.publish(
            '/file/@@index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assertEqual(body, self.content)
        self.checkForBrokenLinks(body, '/file/@@index.html', 'mgr:mgrpw')

    def testPreview(self):
        self.addFile()
        response = self.publish(
            '/file/@@preview.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('<iframe src="."' in body)
        self.checkForBrokenLinks(body, '/file/@@preview.html', 'mgr:mgrpw')


class ImageTest(BrowserTestCase):

    content = zptlogo

    def addImage(self):
        image = Image(self.content)
        root = self.getRootFolder()
        root['image'] = image
        self.commit()

    def testAddForm(self):
        response = self.publish(
            '/+/zope.app.file.Image=',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Add an Image' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_('Object Name' in body)
        self.assert_('"Add"' in body)
        self.checkForBrokenLinks(body, '/+/zope.app.file.Image=',
                                 'mgr:mgrpw')

    def testAdd(self):
        response = self.publish(
            '/+/zope.app.file.Image=',
            form={'type_name': u'zope.app.image.Image',
                  'field.data': StringIO(self.content),
                  'field.data.used': '',
                  'add_input_name': u'image',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('image' in root)
        image = root['image']
        self.assertEqual(image.data, self.content)

    def testAddWithoutName(self):
        data = StringIO(self.content)
        data.filename="test.gif"
        response = self.publish(
            '/+/zope.app.file.Image=',
            form={'type_name': u'zope.app.image.Image',
                  'field.data': data,
                  'field.data.used': '',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('test.gif' in root)
        image = root['test.gif']
        self.assertEqual(image.data, self.content)



    def testUploadForm(self):
        self.addImage()
        response = self.publish(
            '/image/@@upload.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Upload an image' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_('1 KB 16x16' in body)
        self.checkForBrokenLinks(body, '/image/@@upload.html', 'mgr:mgrpw')

    def testUpload(self):
        self.addImage()
        response = self.publish(
            '/image/@@upload.html',
            form={'field.data': StringIO(''),
                  'field.data.used': '',
                  'UPDATE_SUBMIT': u'Change'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Upload an image' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_('0 KB ?x?' in body)
        root = self.getRootFolder()
        image = root['image']
        self.assertEqual(image.data, '')
        self.assertEqual(image.contentType, 'image/gif')

    def testUpload_only_change_content_type(self):
        self.addImage()
        response = self.publish(
            '/image/@@upload.html',
            form={'field.contentType': 'image/png',
                  'UPDATE_SUBMIT': u'Change'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Upload an image' in body)
        self.assert_('Content Type' in body)
        self.assert_('Data' in body)
        self.assert_('1 KB 16x16' in body)
        root = self.getRootFolder()
        image = root['image']
        self.assertEqual(image.data, self.content)
        self.assertEqual(image.contentType, 'image/png')

    def testIndex(self):
        self.addImage()
        response = self.publish(
            '/image/@@index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assertEqual(body, self.content)
        self.checkForBrokenLinks(body, '/image/@@index.html', 'mgr:mgrpw')

    def testPreview(self):
        self.addImage()
        response = self.publish(
            '/image/@@preview.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('<iframe src="."' in body)
        self.checkForBrokenLinks(body, '/image/@@preview.html', 'mgr:mgrpw')

def test_suite():
    from zope.app.testing import functional
    return unittest.TestSuite((
        unittest.makeSuite(FileTest),
        unittest.makeSuite(ImageTest),
        functional.FunctionalDocFileSuite('url.txt'),
        functional.FunctionalDocFileSuite('file.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

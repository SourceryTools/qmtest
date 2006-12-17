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
"""File-based browser resource tests.

$Id: test_fileresource.py 29143 2005-02-14 22:43:16Z srichter $
"""
import os
from unittest import TestCase, main, makeSuite

from zope.publisher.interfaces import NotFound
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.security.proxy import removeSecurityProxy
from zope.security.checker import NamesChecker

from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.testing import ztapi

from zope.publisher.http import IHTTPRequest
from zope.publisher.http import HTTPCharsets
from zope.publisher.browser import TestRequest

from zope.app.publisher.browser.fileresource import FileResourceFactory
from zope.app.publisher.browser.fileresource import ImageResourceFactory
import zope.app.publisher.browser.tests as p

checker = NamesChecker(
    ('__call__', 'HEAD', 'request', 'publishTraverse', 'GET')
    )

test_directory = os.path.dirname(p.__file__)

class Test(PlacelessSetup, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        ztapi.provideAdapter(IHTTPRequest, IUserPreferredCharsets,
                             HTTPCharsets)

    def testNoTraversal(self):

        path = os.path.join(test_directory, 'testfiles', 'test.txt')
        factory = FileResourceFactory(path, checker, 'test.txt')
        resource = factory(TestRequest())
        self.assertRaises(NotFound,
                          resource.publishTraverse,
                          resource.request,
                          '_testData')

    def testFileGET(self):

        path = os.path.join(test_directory, 'testfiles', 'test.txt')

        factory = FileResourceFactory(path, checker, 'test.txt')
        resource = factory(TestRequest())
        self.assertEqual(resource.GET(), open(path, 'rb').read())

        response = removeSecurityProxy(resource.request).response
        self.assertEqual(response.getHeader('Content-Type'), 'text/plain')

    def testFileHEAD(self):

        path = os.path.join(test_directory, 'testfiles', 'test.txt')
        factory = FileResourceFactory(path, checker, 'test.txt')
        resource = factory(TestRequest())

        self.assertEqual(resource.HEAD(), '')

        response = removeSecurityProxy(resource.request).response
        self.assertEqual(response.getHeader('Content-Type'), 'text/plain')

    def testImageGET(self):

        path = os.path.join(test_directory, 'testfiles', 'test.gif')

        factory = ImageResourceFactory(path, checker, 'test.gif')
        resource = factory(TestRequest())

        self.assertEqual(resource.GET(), open(path, 'rb').read())

        response = removeSecurityProxy(resource.request).response
        self.assertEqual(response.getHeader('Content-Type'), 'image/gif')

    def testImageHEAD(self):

        path = os.path.join(test_directory, 'testfiles', 'test.gif')
        factory = ImageResourceFactory(path, checker, 'test.gif')
        resource = factory(TestRequest())

        self.assertEqual(resource.HEAD(), '')

        response = removeSecurityProxy(resource.request).response
        self.assertEqual(response.getHeader('Content-Type'), 'image/gif')



def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

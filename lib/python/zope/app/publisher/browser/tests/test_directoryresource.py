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
"""Directory-based resources test

$Id: test_directoryresource.py 69635 2006-08-18 09:47:04Z philikon $
"""
import os
from unittest import TestCase, main, makeSuite

from zope.publisher.interfaces import NotFound
from zope.proxy import isProxy
from zope.security.proxy import removeSecurityProxy
from zope.publisher.browser import TestRequest
from zope.security.checker import NamesChecker, ProxyFactory
from zope.interface import implements

from zope.app import zapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.publisher.browser.directoryresource import \
     DirectoryResourceFactory, DirectoryResource
from zope.app.container.contained import Contained
from zope.app.publisher.browser.fileresource import FileResource
from zope.app.publisher.browser.pagetemplateresource import \
     PageTemplateResource
import zope.app.publisher.browser.tests as p
from zope.app.publisher.browser.tests import support

test_directory = os.path.dirname(p.__file__)

checker = NamesChecker(
    ('get', '__getitem__', 'request', 'publishTraverse')
    )

class Ob(Contained): pass

ob = Ob()

class Test(support.SiteHandler, PlacelessSetup, TestCase):

    def testNotFound(self):
        path = os.path.join(test_directory, 'testfiles')
        request = TestRequest()
        factory = DirectoryResourceFactory(path, checker, 'testfiles')
        resource = factory(request)
        self.assertRaises(NotFound, resource.publishTraverse,
                          resource.request, 'doesnotexist')
        self.assertRaises(NotFound, resource.get, 'doesnotexist')

    def testGetitem(self):
        path = os.path.join(test_directory, 'testfiles')
        request = TestRequest()
        factory = DirectoryResourceFactory(path, checker, 'testfiles')
        resource = factory(request)
        self.assertRaises(KeyError, resource.__getitem__, 'doesnotexist')
        file = resource['test.txt']

    def testProxy(self):
        path = os.path.join(test_directory, 'testfiles')
        request = TestRequest()
        factory = DirectoryResourceFactory(path, checker, 'testfiles')
        resource = factory(request)
        file = ProxyFactory(resource['test.txt'])
        self.assert_(isProxy(file))

    def testURL(self):
        request = TestRequest()
        request._vh_root = support.site
        path = os.path.join(test_directory, 'testfiles')
        files = DirectoryResourceFactory(path, checker, 'test_files')(request)
        files.__parent__ = support.site
        file = files['test.gif']
        self.assertEquals(file(), 'http://127.0.0.1/@@/test_files/test.gif')

    def testURL2Level(self):
        request = TestRequest()
        request._vh_root = support.site
        ob.__parent__ = support.site
        ob.__name__ = 'ob'
        path = os.path.join(test_directory, 'testfiles')
        files = DirectoryResourceFactory(path, checker, 'test_files')(request)
        files.__parent__ = ob
        file = files['test.gif']
        self.assertEquals(file(), 'http://127.0.0.1/@@/test_files/test.gif')

    def testURL3Level(self):
        request = TestRequest()
        request._vh_root = support.site
        ob.__parent__ = support.site
        ob.__name__ = 'ob'
        path = os.path.join(test_directory, 'testfiles')
        files = DirectoryResourceFactory(path, checker, 'test_files')(request)
        files.__parent__ = ob
        file = files['test.gif']
        self.assertEquals(file(), 'http://127.0.0.1/@@/test_files/test.gif')
        subdir = files['subdir']
        self.assert_(zapi.isinstance(subdir, DirectoryResource))
        file = subdir['test.gif']
        self.assertEquals(file(),
                          'http://127.0.0.1/@@/test_files/subdir/test.gif')

    def testCorrectFactories(self):
        path = os.path.join(test_directory, 'testfiles')
        request = TestRequest()
        resource = DirectoryResourceFactory(path, checker, 'files')(request)

        image = resource['test.gif']
        self.assert_(zapi.isinstance(image, FileResource))
        template = resource['test.pt']
        self.assert_(zapi.isinstance(template, PageTemplateResource))
        file = resource['test.txt']
        self.assert_(zapi.isinstance(file, FileResource))
        file = resource['png']
        self.assert_(zapi.isinstance(file, FileResource))

def test_suite():
    return makeSuite(Test)

if __name__ == '__main__':
    main(defaultTest='test_suite')

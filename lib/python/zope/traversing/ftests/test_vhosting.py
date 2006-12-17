##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Functional tests for virtual hosting.

$Id: test_vhosting.py 66546 2006-04-05 14:53:20Z philikon $
"""
import unittest
import transaction
from zope.traversing.api import traverse
from zope.traversing.browser.tests import browserResource
from zope.security.checker import defineChecker, NamesChecker, NoProxy
from zope.security.checker import _checkers, undefineChecker

from zope.app.testing import functional
from zope.app.folder import Folder
from zope.app.publisher.browser.resource import Resource
from zope.app.container.contained import Contained
from zope.app.zptpage.zptpage import ZPTPage

class MyObj(Contained):
    def __getitem__(self, key):
        return traverse(self, '/foo/bar/' + key)


class TestVirtualHosting(functional.BrowserTestCase):

    def setUp(self):
        functional.BrowserTestCase.setUp(self)
        defineChecker(MyObj, NoProxy)

    def tearDown(self):
        functional.BrowserTestCase.tearDown(self)
        undefineChecker(MyObj)

    def test_request_url(self):
        self.addPage('/pt', u'<span tal:replace="request/URL"/>')
        self.verify('/pt', 'http://localhost/pt\n')
        self.verify('/++vh++/++/pt',
                    'http://localhost/pt\n')
        self.verify('/++vh++https:otherhost:443/++/pt',
                    'https://otherhost/pt\n')
        self.verify('/++vh++https:otherhost:443/fake/folders/++/pt',
                    'https://otherhost/fake/folders/pt\n')

        self.addPage('/foo/bar/pt', u'<span tal:replace="request/URL"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar/pt\n')
        self.verify('/foo/bar/++vh++/++/pt',
                    'http://localhost/pt\n')
        self.verify('/foo/bar/++vh++https:otherhost:443/++/pt',
                    'https://otherhost/pt\n')
        self.verify('/foo/++vh++https:otherhost:443/fake/folders/++/bar/pt',
                    'https://otherhost/fake/folders/bar/pt\n')

    def test_request_base(self):
        self.addPage('/pt', u'<head></head>')
        self.verify('/pt/',
                    '<head>\n<base href="http://localhost/pt" />\n'
                    '</head>\n')
        self.verify('/++vh++/++/pt/',
                    '<head>\n<base href="http://localhost/pt" />\n'
                    '</head>\n')
        self.verify('/++vh++https:otherhost:443/++/pt/',
                    '<head>\n'
                    '<base href="https://otherhost/pt" />'
                    '\n</head>\n')
        self.verify('/++vh++https:otherhost:443/fake/folders/++/pt/',
                    '<head>\n<base href='
                    '"https://otherhost/fake/folders/pt" />'
                    '\n</head>\n')

        self.addPage('/foo/bar/pt', u'<head></head>')
        self.verify('/foo/bar/pt/',
                    '<head>\n<base '
                    'href="http://localhost/foo/bar/pt" />\n'
                    '</head>\n')
        self.verify('/foo/bar/++vh++/++/pt/',
                    '<head>\n<base href="http://localhost/pt" />\n'
                    '</head>\n')
        self.verify('/foo/bar/++vh++https:otherhost:443/++/pt/',
                    '<head>\n'
                    '<base href="https://otherhost/pt" />'
                    '\n</head>\n')
        self.verify('/foo/++vh++https:otherhost:443/fake/folders/++/bar/pt/',
                    '<head>\n<base href='
                    '"https://otherhost/fake/folders/bar/pt" />'
                    '\n</head>\n')

    def test_request_redirect(self):
        self.addPage('/foo/index.html', u'Spam')
        self.verifyRedirect('/foo', 'http://localhost/foo/index.html')
        self.verifyRedirect('/++vh++https:otherhost:443/++/foo',
                            'https://otherhost/foo/index.html')
        self.verifyRedirect('/foo/++vh++https:otherhost:443/bar/++',
                            'https://otherhost/bar/index.html')

    def test_absolute_url(self):
        self.addPage('/pt', u'<span tal:replace="template/@@absolute_url"/>')
        self.verify('/pt', 'http://localhost/pt\n')
        self.verify('/++vh++/++/pt',
                    'http://localhost/pt\n')
        self.verify('/++vh++https:otherhost:443/++/pt',
                    'https://otherhost/pt\n')
        self.verify('/++vh++https:otherhost:443/fake/folders/++/pt',
                    'https://otherhost/fake/folders/pt\n')

        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="template/@@absolute_url"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar/pt\n')
        self.verify('/foo/bar/++vh++/++/pt',
                    'http://localhost/pt\n')
        self.verify('/foo/bar/++vh++https:otherhost:443/++/pt',
                    'https://otherhost/pt\n')
        self.verify('/foo/++vh++https:otherhost:443/fake/folders/++/bar/pt',
                    'https://otherhost/fake/folders/bar/pt\n')

    def test_absolute_url_absolute_traverse(self):
        self.createObject('/foo/bar/obj', MyObj())
        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="container/obj/pt/@@absolute_url"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar/pt\n')
        self.verify('/foo/++vh++https:otherhost:443/++/bar/pt',
                    'https://otherhost/bar/pt\n')

    def test_resources(self):
        browserResource('quux', Resource)
        # Only register the checker once, so that multiple test runs pass.
        if Resource not in _checkers:
            defineChecker(Resource, NamesChecker(['__call__']))
        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="context/++resource++quux" />')
        self.verify('/foo/bar/pt', 'http://localhost/@@/quux\n')
        self.verify('/foo/++vh++https:otherhost:443/fake/folders/++/bar/pt',
                    'https://otherhost/fake/folders/@@/quux\n')

    def createFolders(self, path):
        """addFolders('/a/b/c/d') would traverse and/or create three nested
        folders (a, b, c) and return a tuple (c, 'd') where c is a Folder
        instance at /a/b/c."""
        folder = self.getRootFolder()
        if path[0] == '/':
            path = path[1:]
        path = path.split('/')
        for id in path[:-1]:
            try:
                folder = folder[id]
            except KeyError:
                folder[id] = Folder()
                folder = folder[id]
        return folder, path[-1]

    def createObject(self, path, obj):
        folder, id = self.createFolders(path)
        folder[id] = obj
        transaction.commit()

    def addPage(self, path, content):
        page = ZPTPage()
        page.source = content
        self.createObject(path, page)

    def verify(self, path, content):
        result = self.publish(path)
        self.assertEquals(result.getStatus(), 200)
        self.assertEquals(result.getBody(), content)

    def verifyRedirect(self, path, location):
        result = self.publish(path)
        self.assertEquals(result.getStatus(), 302)
        self.assertEquals(result.getHeader('Location'), location)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestVirtualHosting))
    return suite


if __name__ == '__main__':
    unittest.main()

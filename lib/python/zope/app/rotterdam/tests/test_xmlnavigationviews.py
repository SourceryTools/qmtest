# -*- coding: utf-8 -*-
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
"""XML Navigation Tree Tests

$Id: test_xmlnavigationviews.py 67630 2006-04-27 00:54:03Z jim $
"""
from unittest import TestCase, TestLoader, TextTestRunner

from zope.interface import implements
from zope.pagetemplate.tests.util import check_xml
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces import NotFound
from zope.traversing.api import traverse

from zope.app.testing import ztapi
from zope.app.container.interfaces import IReadContainer
from zope.app.component.site import LocalSiteManager
from zope.app.component.testing import PlacefulSetup
from zope.app.folder.folder import Folder

from zope.app.rotterdam.tests import util
from zope.app.rotterdam.xmlobject import ReadContainerXmlObjectView
from zope.app.rotterdam.xmlobject import XmlObjectView



class File(object):
    pass

class TestXmlObject(PlacefulSetup, TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self, site=True)

    def testXMLTreeViews(self):
        rcxov = ReadContainerXmlObjectView
        treeView = rcxov(self.folder1, TestRequest()).singleBranchTree
        check_xml(treeView(), util.read_output('test1.xml'))

        treeView = rcxov(self.folder1, TestRequest()).children
        check_xml(treeView(), util.read_output('test2.xml'))

        treeView = rcxov(self.folder1_1_1, TestRequest()).children
        check_xml(treeView(), util.read_output('test3.xml'))

        treeView = rcxov(self.rootFolder, TestRequest()).children
        check_xml(treeView(), util.read_output('test4.xml'))

        file1 = File()
        self.folder1_1_1["file1"] = file1
        self.file1 = traverse(self.rootFolder,
                              '/folder1/folder1_1/folder1_1_1/file1')

        class ReadContainerView(ReadContainerXmlObjectView):
            implements(IBrowserPublisher)
            def browserDefault(self, request):
                return self, ()
            def publishTraverse(self, request, name):
                raise NotFound(self, name, request)
            def __call__(self):
                return self.singleBranchTree()

        ztapi.browserView(IReadContainer, 'singleBranchTree.xml',
                          ReadContainerView)

        treeView = rcxov(self.folder1_1_1, TestRequest()).singleBranchTree
        check_xml(treeView(), util.read_output('test5.xml'))

        treeView = XmlObjectView(self.file1, TestRequest()).singleBranchTree
        check_xml(treeView(), util.read_output('test5.xml'))

    def test_virtualhost_support(self):

        # we have to add a virtual host subsite
        folder1 = self.rootFolder['folder1']
        subsite = Folder()
        sm = LocalSiteManager(folder1)
        subsite.setSiteManager(sm)
        folder1['subsite'] = subsite

        # add some more folder to the subsite
        subfolder1 = Folder()
        subsite['subfolder1'] = subfolder1
        subfolder2 = Folder()
        subfolder2_1 = Folder()
        subfolder2['subfolder2_1'] = subfolder2_1
        subsite['subfolder2'] = subfolder2

        # set the virtualhost on the request
        request = TestRequest()
        request._vh_root = subsite

        # test virtual host root
        vh = request.getVirtualHostRoot()
        self.assertEquals(vh, subsite)

        rcxov = ReadContainerXmlObjectView
        treeView = rcxov(subsite, request).singleBranchTree
        check_xml(treeView(), util.read_output('test6.xml'))

        rcxov = ReadContainerXmlObjectView
        treeView = rcxov(subfolder1, request).singleBranchTree
        check_xml(treeView(), util.read_output('test7.xml'))

        rcxov = ReadContainerXmlObjectView
        treeView = rcxov(subfolder2_1, request).singleBranchTree
        check_xml(treeView(), util.read_output('test8.xml'))




def test_suite():
    loader = TestLoader()
    return loader.loadTestsFromTestCase(TestXmlObject)

if __name__=='__main__':
    TextTestRunner().run(test_suite())

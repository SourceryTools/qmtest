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
"""Folder content component tests

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""

from unittest import TestCase, TestSuite, main, makeSuite

import zope.component
from zope.testing.doctestunit import DocTestSuite
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter

from zope.app.folder.interfaces import IFolder
from zope.app.component.testing import PlacefulSetup
from zope.app.component.tests.test_site import BaseTestSiteManagerContainer
from zope.app.container.tests.test_icontainer import BaseTestIContainer
from zope.app.container.tests.test_icontainer import DefaultTestData


class Test(BaseTestIContainer, BaseTestSiteManagerContainer, TestCase):

    def makeTestObject(self):
        from zope.app.folder import Folder
        return Folder()

    def makeTestData(self):
        return DefaultTestData()

    def getUnknownKey(self):
        return '10'

    def getBadKeyTypes(self):
        return [None, ['foo'], 1, '\xf3abc']


class FolderMetaDataTest(PlacefulSetup, TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)
        PlacefulSetup.buildFolders(self)
        zope.component.provideAdapter(ZDCAnnotatableAdapter, (IFolder,),
                                      IZopeDublinCore)

def test_suite():
    from zope.testing.doctestunit import DocTestSuite
    from zope.app.testing.placelesssetup import setUp, tearDown
    return TestSuite((
        makeSuite(Test),
        makeSuite(FolderMetaDataTest),
        DocTestSuite('zope.app.folder.folder',
                     setUp=setUp, tearDown=tearDown),
        ))    

if __name__=='__main__':
    main(defaultTest='test_suite')

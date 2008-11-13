##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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
"""Local sitemanager tests.

$Id: test_localsitemanager.py 73163 2007-03-14 06:16:38Z yusei $
"""
import unittest

from zope.interface import Interface
from zope.copypastemove import ObjectCopier
from zope.app.component import site
from zope.app.folder import Folder
from zope.app.testing.placelesssetup import PlacelessSetup

class I1(Interface):pass

class TestLocalSiteManager(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(TestLocalSiteManager, self).setUp()

        self.util = object()
        self.root = Folder()
        self.root['site'] = Folder()
        subfolder  = self.root['site']
        subfolder.setSiteManager(site.LocalSiteManager(subfolder))
        subfolder.getSiteManager().registerUtility(self.util, I1)

    def testCopy(self):
        self.assert_(self.root['site'].getSiteManager().getUtility(I1) is self.util)

        copier = ObjectCopier(self.root['site'])
        copier.copyTo(self.root, 'copied_site')

        self.assert_(self.root['copied_site'].getSiteManager().getUtility(I1) is not self.util)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLocalSiteManager),
        ))

if __name__ == '__main__':
    unittest.main()

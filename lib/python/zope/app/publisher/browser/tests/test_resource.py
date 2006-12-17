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
"""Unit tests for Resource

$Id: test_resource.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest

from zope.publisher.browser import TestRequest

from zope.app.publisher.browser.resource import Resource
from zope.app.publisher.browser.tests import support
from zope.app.testing.placelesssetup import PlacelessSetup


class TestResource(support.SiteHandler, PlacelessSetup, unittest.TestCase):

    def testGlobal(self):
        req = TestRequest()
        r = Resource(req)
        req._vh_root = support.site
        r.__parent__ = support.site
        r.__name__ = 'foo'
        self.assertEquals(r(), 'http://127.0.0.1/@@/foo')
        r.__name__ = '++resource++foo'
        self.assertEquals(r(), 'http://127.0.0.1/@@/foo')

    def testGlobalInVirtualHost(self):
        req = TestRequest()
        req.setVirtualHostRoot(['x', 'y'])
        r = Resource(req)
        req._vh_root = support.site
        r.__parent__ = support.site
        r.__name__ = 'foo'
        self.assertEquals(r(), 'http://127.0.0.1/x/y/@@/foo')


def test_suite():
    return unittest.makeSuite(TestResource)

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

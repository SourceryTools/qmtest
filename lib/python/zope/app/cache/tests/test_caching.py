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
"""Unit tests for caching helpers.

$Id: test_caching.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.interface import implements
from zope.annotation.interfaces import IAnnotatable, IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from zope.app.cache.interfaces import ICacheable, ICache
from zope.app.cache.caching import getCacheForObject
from zope.app.cache.annotationcacheable import AnnotationCacheable
from zope.app.testing import ztapi, placelesssetup

class ObjectStub(object):
    implements(IAttributeAnnotatable)

class CacheStub(object):
    implements(ICache)

class Test(placelesssetup.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        ztapi.provideAdapter(IAttributeAnnotatable, IAnnotations,
                             AttributeAnnotations)
        ztapi.provideAdapter(IAnnotatable, ICacheable,
                             AnnotationCacheable)
        self._cache = CacheStub()
        ztapi.provideUtility(ICache, self._cache, "my_cache")

    def testGetCacheForObj(self):
        obj = ObjectStub()
        self.assertEquals(getCacheForObject(obj), None)
        ICacheable(obj).setCacheId("my_cache")
        self.assertEquals(getCacheForObject(obj), self._cache)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

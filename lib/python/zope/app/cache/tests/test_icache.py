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
"""Unit tests for ICache interface

$Id: test_icache.py 26551 2004-07-15 07:06:37Z srichter $
"""
from unittest import TestSuite, main
from zope.interface.verify import verifyObject
from zope.app.cache.interfaces import ICache


class BaseICacheTest(object):
    """Base class for ICache unit tests.  Subclasses should provide a
    _Test__new() method that returns a new empty cache object.
    """

    def testVerifyICache(self):
        # Verify that the object implements ICache
        verifyObject(ICache, self._Test__new())

    def testCaching(self):
        # Verify basic caching
        cache = self._Test__new()
        ob = "obj"
        data = "data"
        marker = []
        self.failIf(cache.query(ob, None, default=marker) is not marker,
                    "empty cache should not contain anything")

        cache.set(data, ob, key={'id': 35})
        self.assertEquals(cache.query(ob, {'id': 35}), data,
                    "should return cached result")
        self.failIf(cache.query(ob, {'id': 33}, default=marker) is not marker,
                    "should not return cached result for a different key")

        cache.invalidate(ob, {"id": 33})
        self.assertEquals(cache.query(ob, {'id': 35}), data,
                          "should return cached result")
        self.failIf(cache.query(ob, {'id': 33}, default=marker) is not marker,
                    "should not return cached result after invalidate")

    def testInvalidateAll(self):
        cache = self._Test__new()
        ob1 = object()
        ob2 = object()
        cache.set("data1", ob1)
        cache.set("data2", ob2, key={'foo': 1})
        cache.set("data3", ob2, key={'foo': 2})
        cache.invalidateAll()
        marker = []
        self.failIf(cache.query(ob1, default=marker) is not marker,
                    "should not return cached result after invalidateAll")
        self.failIf(cache.query(ob2, {'foo': 1}, default=marker) is not marker,
                    "should not return cached result after invalidateAll")
        self.failIf(cache.query(ob2, {'foo': 2}, default=marker) is not marker,
                    "should not return cached result after invalidateAll")


def test_suite():
    return TestSuite((
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

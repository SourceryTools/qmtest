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
"""Find functionality tests

$Id: test_find.py 38178 2005-08-30 21:50:19Z mj $
"""
from unittest import TestCase, main, makeSuite
from zope.app.container.interfaces import IReadContainer
from zope.app.container.interfaces import IObjectFindFilter
from zope.app.container.find import FindAdapter, SimpleIdFindFilter
from zope.interface import implements

class FakeContainer(object):
    implements(IReadContainer)

    def __init__(self, id, objects):
        self._id = id
        self._objects = objects

    def keys(self):
        return [object._id for object in self._objects]

    def values(self):
        return self._objects

    def items(self):
        return [(object._id, object) for object in self._objects]

    def __getitem__(self, id):
        for object in self._objects:
            if object._id == id:
                return object
        raise KeyError("Could not find %s" % id)

    def get(self, id, default=None):
        for object in self._objects:
            if object._id == id:
                return object

        return default

    def __contains__(self, id):
        for object in self._objects:
            if object.id == id:
                return True
        return False

    def __len__(self):
        return len(self._objects)

class TestObjectFindFilter(object):
    implements(IObjectFindFilter)

    def __init__(self, count):
        self._count = count

    def matches(self, object):
        if IReadContainer.providedBy(object):
            return len(object) == self._count
        else:
            return False

class Test(TestCase):
    def test_idFind(self):
        alpha = FakeContainer('alpha', [])
        delta = FakeContainer('delta', [])
        beta = FakeContainer('beta', [delta])
        gamma = FakeContainer('gamma', [])
        tree = FakeContainer(
            'tree',
            [alpha, beta, gamma])
        find = FindAdapter(tree)
        # some simple searches
        result = find.find([SimpleIdFindFilter(['beta'])])
        self.assertEquals([beta], result)
        result = find.find([SimpleIdFindFilter(['gamma'])])
        self.assertEquals([gamma], result)
        result = find.find([SimpleIdFindFilter(['delta'])])
        self.assertEquals([delta], result)
        # we should not find the container we search on
        result = find.find([SimpleIdFindFilter(['tree'])])
        self.assertEquals([], result)
        # search for multiple ids
        result = find.find([SimpleIdFindFilter(['alpha', 'beta'])])
        self.assertEquals([alpha, beta], result)
        result = find.find([SimpleIdFindFilter(['beta', 'delta'])])
        self.assertEquals([beta, delta], result)
        # search without any filters, find everything
        result = find.find([])
        self.assertEquals([alpha, beta, delta, gamma], result)
        # search for something that doesn't exist
        result = find.find([SimpleIdFindFilter(['foo'])])
        self.assertEquals([], result)
        # find for something that has two ids at the same time,
        # can't ever be the case
        result = find.find([SimpleIdFindFilter(['alpha']),
                            SimpleIdFindFilter(['beta'])])
        self.assertEquals([], result)

    def test_objectFind(self):
        alpha = FakeContainer('alpha', [])
        delta = FakeContainer('delta', [])
        beta = FakeContainer('beta', [delta])
        gamma = FakeContainer('gamma', [])
        tree = FakeContainer(
            'tree',
            [alpha, beta, gamma])
        find = FindAdapter(tree)
        result = find.find(object_filters=[TestObjectFindFilter(0)])
        self.assertEquals([alpha, delta, gamma], result)
        result = find.find(object_filters=[TestObjectFindFilter(1)])
        self.assertEquals([beta], result)
        result = find.find(object_filters=[TestObjectFindFilter(2)])
        self.assertEquals([], result)

    def test_combinedFind(self):
        alpha = FakeContainer('alpha', [])
        delta = FakeContainer('delta', [])
        beta = FakeContainer('beta', [delta])
        gamma = FakeContainer('gamma', [])
        tree = FakeContainer(
            'tree',
            [alpha, beta, gamma])
        find = FindAdapter(tree)
        result = find.find(id_filters=[SimpleIdFindFilter(['alpha'])],
                           object_filters=[TestObjectFindFilter(0)])
        self.assertEquals([alpha], result)

        result = find.find(id_filters=[SimpleIdFindFilter(['alpha'])],
                           object_filters=[TestObjectFindFilter(1)])
        self.assertEquals([], result)

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

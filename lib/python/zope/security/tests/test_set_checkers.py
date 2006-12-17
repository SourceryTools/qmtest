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
"""Test checkers for standard types

This is a test of the assertions made in
zope.security.checkers._default_checkers.

$Id: test_set_checkers.py 69148 2006-07-16 17:10:19Z jim $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.security.checker import ProxyFactory
from zope.security.interfaces import ForbiddenAttribute
import sets

def check_forbidden_get(object, attr):
    try:
        return getattr(object, attr)
    except ForbiddenAttribute, e:
        return 'ForbiddenAttribute: %s' % e[0]

def test_set():
    """Test that we can do everything we expect to be able to do

    with proxied sets.

    >>> us = set((1, 2))
    >>> s = ProxyFactory(us)

    >>> check_forbidden_get(s, 'add') # Verify that we are protected
    'ForbiddenAttribute: add'
    >>> check_forbidden_get(s, 'remove') # Verify that we are protected
    'ForbiddenAttribute: remove'
    >>> check_forbidden_get(s, 'discard') # Verify that we are protected
    'ForbiddenAttribute: discard'
    >>> check_forbidden_get(s, 'pop') # Verify that we are protected
    'ForbiddenAttribute: pop'
    >>> check_forbidden_get(s, 'clear') # Verify that we are protected
    'ForbiddenAttribute: clear'

    >>> len(s)
    2

    >>> 1 in s
    True

    >>> 1 not in s
    False

    >>> s.issubset(set((1,2,3)))
    True

    >>> s.issuperset(set((1,2,3)))
    False

    >>> c = s.union(set((2, 3)))
    >>> sorted(c)
    [1, 2, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s | set((2, 3))
    >>> sorted(c)
    [1, 2, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s | ProxyFactory(set((2, 3)))
    >>> sorted(c)
    [1, 2, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = set((2, 3)) | s
    >>> sorted(c)
    [1, 2, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s.intersection(set((2, 3)))
    >>> sorted(c)
    [2]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s & set((2, 3))
    >>> sorted(c)
    [2]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s & ProxyFactory(set((2, 3)))
    >>> sorted(c)
    [2]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = set((2, 3)) & s
    >>> sorted(c)
    [2]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s.difference(set((2, 3)))
    >>> sorted(c)
    [1]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s - ProxyFactory(set((2, 3)))
    >>> sorted(c)
    [1]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s - set((2, 3))
    >>> sorted(c)
    [1]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = set((2, 3)) - s
    >>> sorted(c)
    [3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s.symmetric_difference(set((2, 3)))
    >>> sorted(c)
    [1, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s ^ set((2, 3))
    >>> sorted(c)
    [1, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s ^ ProxyFactory(set((2, 3)))
    >>> sorted(c)
    [1, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = set((2, 3)) ^ s
    >>> sorted(c)
    [1, 3]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> c = s.copy()
    >>> sorted(c)
    [1, 2]
    >>> check_forbidden_get(c, 'add')
    'ForbiddenAttribute: add'

    >>> str(s) == str(us)
    True
    
    >>> repr(s) == repr(us)
    True

    Always available:

    >>> s < us
    False
    >>> s > us
    False
    >>> s <= us
    True
    >>> s >= us
    True
    >>> s == us
    True
    >>> s != us
    False

    Note that you can't compare proxied sets with other proxied sets
    due a limitaion in the set comparison functions which won't work
    with any kind of proxy.
    
    >>> bool(s)
    True
    >>> s.__class__ == set
    True
    """

def setUpFrozenSet(test):
    test.globs['set'] = frozenset

def setUpSet(test):
    test.globs['set'] = sets.Set

def setUpImmutableSet(test):
    test.globs['set'] = sets.ImmutableSet

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        DocTestSuite(setUp=setUpFrozenSet),
        DocTestSuite(setUp=setUpSet),
        DocTestSuite(setUp=setUpImmutableSet),
        ))

if __name__ == '__main__':
    import unittest
    unittest.main()

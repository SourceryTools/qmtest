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

$Id: test_standard_checkers.py 37535 2005-07-28 22:37:32Z garrett $
"""
from zope.security.checker import ProxyFactory, NamesChecker
from zope.security.interfaces import ForbiddenAttribute


def check_forbidden_get(object, attr):
    try:
        return getattr(object, attr)
    except ForbiddenAttribute, e:
        return 'ForbiddenAttribute: %s' % e[0]


def check_forbidden_setitem(object, item, value):
    try:
        object[item] = value
    except ForbiddenAttribute, e:
        return 'ForbiddenAttribute: %s' % e[0]


def check_forbidden_delitem(object, item):
    try:
        del object[item]
    except ForbiddenAttribute, e:
        return 'ForbiddenAttribute: %s' % e[0]


def check_forbidden_call(callable, *args):
    try:
        return callable(*args)
    except ForbiddenAttribute, e:
        return 'ForbiddenAttribute: %s' % e[0]


def test_dict():
    """Test that we can do everything we expect to be able to do

    with proxied dicts.

    >>> d = ProxyFactory({'a': 1, 'b': 2})

    >>> check_forbidden_get(d, 'clear') # Verify that we are protected
    'ForbiddenAttribute: clear'
    >>> check_forbidden_setitem(d, 3, 4) # Verify that we are protected
    'ForbiddenAttribute: __setitem__'

    >>> d['a']
    1
    >>> len(d)
    2
    >>> list(d)
    ['a', 'b']
    >>> d.get('a')
    1
    >>> int(d.has_key('a'))
    1

    >>> c = d.copy()
    >>> check_forbidden_get(c, 'clear')
    'ForbiddenAttribute: clear'
    >>> int(str(c) in ("{'a': 1, 'b': 2}", "{'b': 2, 'a': 1}"))
    1

    >>> int(`c` in ("{'a': 1, 'b': 2}", "{'b': 2, 'a': 1}"))
    1


    >>> def sorted(x):
    ...    x = list(x)
    ...    x.sort()
    ...    return x

    >>> sorted(d.keys())
    ['a', 'b']
    >>> sorted(d.values())
    [1, 2]
    >>> sorted(d.items())
    [('a', 1), ('b', 2)]

    >>> sorted(d.iterkeys())
    ['a', 'b']
    >>> sorted(d.itervalues())
    [1, 2]
    >>> sorted(d.iteritems())
    [('a', 1), ('b', 2)]

    Always available:

    >>> int(d < d)
    0
    >>> int(d > d)
    0
    >>> int(d <= d)
    1
    >>> int(d >= d)
    1
    >>> int(d == d)
    1
    >>> int(d != d)
    0
    >>> int(bool(d))
    1
    >>> int(d.__class__ == dict)
    1

    """

def test_list():
    """Test that we can do everything we expect to be able to do

    with proxied lists.

    >>> l = ProxyFactory([1, 2])
    >>> check_forbidden_delitem(l, 0)
    'ForbiddenAttribute: __delitem__'
    >>> check_forbidden_setitem(l, 0, 3)
    'ForbiddenAttribute: __setitem__'
    >>> l[0]
    1
    >>> l[0:1]
    [1]
    >>> check_forbidden_setitem(l[:1], 0, 2)
    'ForbiddenAttribute: __setitem__'
    >>> len(l)
    2
    >>> tuple(l)
    (1, 2)
    >>> int(1 in l)
    1
    >>> l.index(2)
    1
    >>> l.count(2)
    1
    >>> str(l)
    '[1, 2]'
    >>> `l`
    '[1, 2]'
    >>> l + l
    [1, 2, 1, 2]

    Always available:

    >>> int(l < l)
    0
    >>> int(l > l)
    0
    >>> int(l <= l)
    1
    >>> int(l >= l)
    1
    >>> int(l == l)
    1
    >>> int(l != l)
    0
    >>> int(bool(l))
    1
    >>> int(l.__class__ == list)
    1


    """

def test_tuple():
    """Test that we can do everything we expect to be able to do

    with proxied lists.

    >>> l = ProxyFactory((1, 2))
    >>> l[0]
    1
    >>> l[0:1]
    (1,)
    >>> len(l)
    2
    >>> list(l)
    [1, 2]
    >>> int(1 in l)
    1
    >>> str(l)
    '(1, 2)'
    >>> `l`
    '(1, 2)'
    >>> l + l
    (1, 2, 1, 2)

    Always available:

    >>> int(l < l)
    0
    >>> int(l > l)
    0
    >>> int(l <= l)
    1
    >>> int(l >= l)
    1
    >>> int(l == l)
    1
    >>> int(l != l)
    0
    >>> int(bool(l))
    1
    >>> int(l.__class__ == tuple)
    1

    """

def test_iter():
    """
    >>> list(ProxyFactory(iter([1, 2])))
    [1, 2]
    >>> list(ProxyFactory(iter((1, 2))))
    [1, 2]
    >>> list(ProxyFactory(iter({1:1, 2:2})))
    [1, 2]
    >>> def f():
    ...     for i in 1, 2:
    ...             yield i
    ...
    >>> list(ProxyFactory(f()))
    [1, 2]
    >>> list(ProxyFactory(f)())
    [1, 2]
    """

def test_new_class():
    """

    >>> class C(object):
    ...    x = 1
    >>> C = ProxyFactory(C)
    >>> check_forbidden_call(C)
    'ForbiddenAttribute: __call__'
    >>> check_forbidden_get(C, '__dict__')
    'ForbiddenAttribute: __dict__'
    >>> s = str(C)
    >>> s = `C`
    >>> int(C.__module__ == __name__)
    1
    >>> len(C.__bases__)
    1
    >>> len(C.__mro__)
    2

    Always available:

    >>> int(C < C)
    0
    >>> int(C > C)
    0
    >>> int(C <= C)
    1
    >>> int(C >= C)
    1
    >>> int(C == C)
    1
    >>> int(C != C)
    0
    >>> int(bool(C))
    1
    >>> int(C.__class__ == type)
    1

    """

def test_new_instance():
    """

    >>> class C(object):
    ...    x, y = 1, 2
    >>> c = ProxyFactory(C(), NamesChecker(['x']))
    >>> check_forbidden_get(c, 'y')
    'ForbiddenAttribute: y'
    >>> check_forbidden_get(c, 'z')
    'ForbiddenAttribute: z'
    >>> c.x
    1
    >>> int(c.__class__ == C)
    1

    Always available:

    >>> int(c < c)
    0
    >>> int(c > c)
    0
    >>> int(c <= c)
    1
    >>> int(c >= c)
    1
    >>> int(c == c)
    1
    >>> int(c != c)
    0
    >>> int(bool(c))
    1
    >>> int(c.__class__ == C)
    1

    """

def test_classic_class():
    """

    >>> class C:
    ...    x = 1
    >>> C = ProxyFactory(C)
    >>> check_forbidden_call(C)
    'ForbiddenAttribute: __call__'
    >>> check_forbidden_get(C, '__dict__')
    'ForbiddenAttribute: __dict__'
    >>> s = str(C)
    >>> s = `C`
    >>> int(C.__module__ == __name__)
    1
    >>> len(C.__bases__)
    0

    Always available:

    >>> int(C < C)
    0
    >>> int(C > C)
    0
    >>> int(C <= C)
    1
    >>> int(C >= C)
    1
    >>> int(C == C)
    1
    >>> int(C != C)
    0
    >>> int(bool(C))
    1

    """

def test_classic_instance():
    """

    >>> class C(object):
    ...    x, y = 1, 2
    >>> c = ProxyFactory(C(), NamesChecker(['x']))
    >>> check_forbidden_get(c, 'y')
    'ForbiddenAttribute: y'
    >>> check_forbidden_get(c, 'z')
    'ForbiddenAttribute: z'
    >>> c.x
    1
    >>> int(c.__class__ == C)
    1

    Always available:

    >>> int(c < c)
    0
    >>> int(c > c)
    0
    >>> int(c <= c)
    1
    >>> int(c >= c)
    1
    >>> int(c == c)
    1
    >>> int(c != c)
    0
    >>> int(bool(c))
    1
    >>> int(c.__class__ == C)
    1

    """

def test_rocks():
    """
    >>> int(type(ProxyFactory(  object()  )) is object)
    1
    >>> int(type(ProxyFactory(  1  )) is int)
    1
    >>> int(type(ProxyFactory(  1.0  )) is float)
    1
    >>> int(type(ProxyFactory(  1l  )) is long)
    1
    >>> int(type(ProxyFactory(  1j  )) is complex)
    1
    >>> int(type(ProxyFactory(  None  )) is type(None))
    1
    >>> int(type(ProxyFactory(  'xxx'  )) is str)
    1
    >>> int(type(ProxyFactory(  u'xxx'  )) is unicode)
    1
    >>> int(type(ProxyFactory(  True  )) is type(True))
    1

    >>> from datetime import timedelta, datetime, date, time, tzinfo
    >>> int(type(ProxyFactory(  timedelta(1)  )) is timedelta)
    1
    >>> int(type(ProxyFactory(  datetime(2000, 1, 1)  )) is datetime)
    1
    >>> int(type(ProxyFactory(  date(2000, 1, 1)  )) is date)
    1
    >>> int(type(ProxyFactory(  time()  )) is time)
    1
    >>> int(type(ProxyFactory(  tzinfo() )) is tzinfo)
    1

    >>> from pytz import UTC
    >>> int(type(ProxyFactory(  UTC )) is type(UTC))
    1
    """

def test_iter_of_sequences():
    """
    >>> class X(object):
    ...   d = 1, 2, 3
    ...   def __getitem__(self, i):
    ...      return self.d[i]
    ...
    >>> x = X()

    We can iterate over sequences

    >>> list(x)
    [1, 2, 3]
    >>> c = NamesChecker(['__getitem__'])
    >>> p = ProxyFactory(x, c)

    Even if they are proxied

    >>> list(p)
    [1, 2, 3]

    But if the class has an iter:

    >>> X.__iter__ = lambda self: iter(self.d)
    >>> list(x)
    [1, 2, 3]

    We shouldn't be able to iterate if we don't have an assertion:

    >>> check_forbidden_call(list, p)
    'ForbiddenAttribute: __iter__'
    """

def test_interfaces_and_declarations():
    """Test that we can still use interfaces though proxies

    >>> import zope.interface
    >>> class I(zope.interface.Interface):
    ...     pass
    >>> class IN(zope.interface.Interface):
    ...     pass
    >>> class II(zope.interface.Interface):
    ...     pass
    >>> class N(object):
    ...     zope.interface.implements(I)
    ...     zope.interface.classProvides(IN)
    >>> n = N()
    >>> zope.interface.directlyProvides(n, II)
    >>> from zope.security.checker import ProxyFactory
    >>> N = ProxyFactory(N)
    >>> n = ProxyFactory(n)
    >>> I.implementedBy(N)
    True
    >>> IN.providedBy(N)
    True
    >>> I.providedBy(n)
    True
    >>> II.providedBy(n)
    True
    """


from zope.testing.doctestunit import DocTestSuite

def test_suite():
    return DocTestSuite()

if __name__ == '__main__':
    import unittest
    unittest.main()

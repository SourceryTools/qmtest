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
"""Security proxy tests

$Id$
"""

import unittest
from zope.security.proxy import getChecker, ProxyFactory, removeSecurityProxy
from zope.proxy import ProxyBase as proxy

class Checker(object):

    ok = 1

    unproxied_types = str,

    def check_getattr(self, object, name):
        if name not in ("foo", "next", "__class__", "__name__", "__module__"):
            raise RuntimeError

    def check_setattr(self, object, name):
        if name != "foo":
            raise RuntimeError

    def check(self, object, opname):
        if not self.ok:
            raise RuntimeError

    def proxy(self, value):
        if type(value) in self.unproxied_types:
            return value
        return ProxyFactory(value, self)


class Something:
    def __init__(self):
        self.foo = [1,2,3]
    def __getitem__(self, key):
        return self.foo[key]
    def __setitem__(self, key, value):
        self.foo[key] = value
    def __delitem__(self, key):
        del self.foo[key]
    def __call__(self, arg):
        return 42
    def __eq__(self, other):
        return self is other
    def __hash__(self):
        return 42
    def __iter__(self):
        return self
    def next(self):
        return 42 # Infinite sequence
    def __len__(self):
        return 42
    def __nonzero__(self):
        return 1
    def __getslice__(self, i, j):
        return [42]
    def __setslice__(self, i, j, value):
        if value != [42]:
            raise ValueError
    def __contains__(self, x):
        return x == 42


class ProxyTests(unittest.TestCase):

    def setUp(self):
        self.x = Something()
        self.c = Checker()
        self.p = ProxyFactory(self.x, self.c)

    def shouldFail(self, *args):
        self.c.ok = 0
        self.assertRaises(RuntimeError, *args)
        self.c.ok = 1

    def testDerivation(self):
        self.assert_(isinstance(self.p, proxy))

    def testStr(self):
        self.assertEqual(str(self.p), str(self.x))

        x = Something()
        c = Checker()
        c.ok = 0
        p = ProxyFactory(x, c)
        s = str(p)
        self.failUnless(s.startswith(
            "<security proxied %s.%s instance at"
            % (x.__class__.__module__, x.__class__.__name__)),
                        s)


    def testRepr(self):
        self.assertEqual(repr(self.p), repr(self.x))

        x = Something()
        c = Checker()
        c.ok = 0
        p = ProxyFactory(x, c)
        s = repr(p)
        self.failUnless(s.startswith(
            "<security proxied %s.%s instance at"
            % (x.__class__.__module__, x.__class__.__name__)),
                        s)

    def testGetAttrOK(self):
        self.assertEqual(removeSecurityProxy(self.p.foo), [1,2,3])

    def testGetAttrFail(self):
        self.assertRaises(RuntimeError, lambda: self.p.bar)

    def testSetAttrOK(self):
        self.p.foo = 42
        self.assertEqual(self.p.foo, 42)

    def testSetAttrFail(self):
        def doit(): self.p.bar = 42
        self.assertRaises(RuntimeError, doit)

    def testGetItemOK(self):
        self.assertEqual(self.p[0], 1)

    def testGetItemFail(self):
        self.shouldFail(lambda: self.p[10])

    def testSetItemOK(self):
        self.p[0] = 42
        self.assertEqual(self.p[0], 42)

    def testSetItemFail(self):
        def doit(): del self.p[0]
        self.shouldFail(doit)

    def testDelItemOK(self):
        self.p[0] = 42
        self.assertEqual(self.p[0], 42)
        del self.p[0]
        self.shouldFail(lambda: self.p[0])

    def testDelItemFail(self):
        def doit(): self.p[10] = 42
        self.shouldFail(doit)

    def testCallOK(self):
        self.assertEqual(self.p(None), 42)

    def testCallFail(self):
        self.shouldFail(self.p, None)

    def testRichCompareOK(self):
        self.failUnless(self.p == self.x)

##     def testRichCompareFail(self):
##         self.shouldFail(lambda: self.p == self.x)

    def testIterOK(self):
        self.assertEqual(removeSecurityProxy(iter(self.p)), self.x)

    def testIterFail(self):
        self.shouldFail(iter, self.p)

    def testNextOK(self):
        self.assertEqual(self.p.next(), 42)

    def testNextFail(self):
        self.shouldFail(self.p.next)

    def testCompareOK(self):
        self.assertEqual(cmp(self.p, self.x), 0)

##     def testCompareFail(self):
##         self.shouldFail(cmp, self.p, self.x)

    def testHashOK(self):
        self.assertEqual(hash(self.p), hash(self.x))

##     def testHashFail(self):
##         self.shouldFail(hash, self.p)

    def testNonzeroOK(self):
        self.assertEqual(not self.p, 0)

##     def testNonzeroFail(self):
##         self.shouldFail(lambda: not self.p)

    def testLenOK(self):
        self.assertEqual(len(self.p), 42)

    def testLenFail(self):
        self.shouldFail(len, self.p)

    def testSliceOK(self):
        self.assertEqual(removeSecurityProxy(self.p[:]), [42])

    def testSliceFail(self):
        self.shouldFail(lambda: self.p[:])

    def testSetSliceOK(self):
        self.p[:] = [42]

    def testSetSliceFail(self):
        def doit(): self.p[:] = [42]
        self.shouldFail(doit)

    def testContainsOK(self):
        self.failUnless(42 in self.p)

    def testContainsFail(self):
        self.shouldFail(lambda: 42 in self.p)

    def testGetObject(self):
        self.assertEqual(self.x, removeSecurityProxy(self.p))

    def testGetChecker(self):
        self.assertEqual(self.c, getChecker(self.p))

    def testProxiedClassicClassAsDictKey(self):
        class C(object):
            pass
        d = {C: C()}
        pC = ProxyFactory(C, self.c)
        self.assertEqual(d[pC], d[C])

    def testProxiedNewClassAsDictKey(self):
        class C(object):
            pass
        d = {C: C()}
        pC = ProxyFactory(C, self.c)
        self.assertEqual(d[pC], d[C])

    unops = [
        "-x", "+x", "abs(x)", "~x",
        "int(x)", "long(x)", "float(x)",
        ]

    def test_unops(self):
        # We want the starting value of the expressions to be a proxy,
        # but we don't want to create new proxies as a result of
        # evaluation, so we have to extend the list of types that
        # aren't proxied.
        self.c.unproxied_types = str, int, long, float
        for expr in self.unops:
            x = 1
            y = eval(expr)
            # Make sure 'x' is a proxy always:
            x = ProxyFactory(1, self.c)
            z = eval(expr)
            self.assertEqual(removeSecurityProxy(z), y,
                             "x=%r; expr=%r" % (x, expr))
            self.shouldFail(lambda x: eval(expr), x)

    def test_odd_unops(self):
        # unops that don't return a proxy
        P = self.c.proxy
        for func in (
            hex, oct,
            # lambda x: not x,
            ):
            self.assertEqual(func(P(100)), func(100))
            self.shouldFail(func, P(100))

    binops = [
        "x+y", "x-y", "x*y", "x/y", "divmod(x, y)", "x**y", "x//y",
        "x<<y", "x>>y", "x&y", "x|y", "x^y",
        ]

    def test_binops(self):
        P = self.c.proxy
        for expr in self.binops:
            first = 1
            for x in [1, P(1)]:
                for y in [2, P(2)]:
                    if first:
                        z = eval(expr)
                        first = 0
                    else:
                        self.assertEqual(removeSecurityProxy(eval(expr)), z,
                                         "x=%r; y=%r; expr=%r" % (x, y, expr))
                        self.shouldFail(lambda x, y: eval(expr), x, y)

    def test_inplace(self):
        # TODO: should test all inplace operators...
        P = self.c.proxy

        pa = P(1)
        pa += 2
        self.assertEqual(removeSecurityProxy(pa), 3)

        a = [1, 2, 3]
        pa = qa = P(a)
        pa += [4, 5, 6]
        self.failUnless(pa is qa)
        self.assertEqual(a, [1, 2, 3, 4, 5, 6])

        def doit():
            pa = P(1)
            pa += 2
        self.shouldFail(doit)

        pa = P(2)
        pa **= 2
        self.assertEqual(removeSecurityProxy(pa), 4)

        def doit():
            pa = P(2)
            pa **= 2
        self.shouldFail(doit)

    def test_coerce(self):
        P = self.c.proxy

        # Before 2.3, coerce() of two proxies returns them unchanged
        import sys
        fixed_coerce = sys.version_info >= (2, 3, 0)

        x = P(1)
        y = P(2)
        a, b = coerce(x, y)
        self.failUnless(a is x and b is y)

        x = P(1)
        y = P(2.1)
        a, b = coerce(x, y)
        self.failUnless(removeSecurityProxy(a) == 1.0 and b is y)
        if fixed_coerce:
            self.failUnless(type(removeSecurityProxy(a)) is float and b is y)

        x = P(1.1)
        y = P(2)
        a, b = coerce(x, y)
        self.failUnless(a is x and removeSecurityProxy(b) == 2.0)
        if fixed_coerce:
            self.failUnless(a is x and type(removeSecurityProxy(b)) is float)

        x = P(1)
        y = 2
        a, b = coerce(x, y)
        self.failUnless(a is x and b is y)

        x = P(1)
        y = 2.1
        a, b = coerce(x, y)
        self.failUnless(type(removeSecurityProxy(a)) is float and b is y)

        x = P(1.1)
        y = 2
        a, b = coerce(x, y)
        self.failUnless(a is x and type(removeSecurityProxy(b)) is float)

        x = 1
        y = P(2)
        a, b = coerce(x, y)
        self.failUnless(a is x and b is y)

        x = 1.1
        y = P(2)
        a, b = coerce(x, y)
        self.failUnless(a is x and type(removeSecurityProxy(b)) is float)

        x = 1
        y = P(2.1)
        a, b = coerce(x, y)
        self.failUnless(type(removeSecurityProxy(a)) is float and b is y)

def test_using_mapping_slots_hack():
    """The security proxy will use mapping slots, on the checker to go faster

    If a checker implements normally, a checkers's check and
    check_getattr methods are used to check operator and attribute
    access:

      >>> class Checker(object):
      ...     def check(self, object, name):
      ...         print 'check', name
      ...     def check_getattr(self, object, name):
      ...         print 'check_getattr', name
      ...     def proxy(self, object):
      ...         return 1
      >>> def f():
      ...     pass
      >>> p = ProxyFactory(f, Checker())
      >>> p.__name__
      check_getattr __name__
      1
      >>> p()
      check __call__
      1

    But, if the checker has a __setitem__ method:

      >>> def __setitem__(self, object, name):
      ...     print '__setitem__', name
      >>> Checker.__setitem__ = __setitem__

    It will be used rather than either check or check_getattr:

      >>> p.__name__
      __setitem__ __name__
      1
      >>> p()
      __setitem__ __call__
      1

    If a checker has a __getitem__ method:

      >>> def __getitem__(self, object):
      ...     return 2
      >>> Checker.__getitem__ = __getitem__

    It will be used rather than it's proxy method:

      >>> p.__name__
      __setitem__ __name__
      2
      >>> p()
      __setitem__ __call__
      2

    """



def test_suite():
    suite = unittest.makeSuite(ProxyTests)
    from doctest import DocTestSuite
    suite.addTest(DocTestSuite())
    suite.addTest(DocTestSuite('zope.security.proxy'))
    return suite

if __name__=='__main__':
    from unittest import main
    main(defaultTest='test_suite')

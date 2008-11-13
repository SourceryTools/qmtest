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
"""Test mapply() function

$Id: test_mapply.py 70826 2006-10-20 03:41:16Z baijum $
"""
import unittest

from zope.publisher.publish import mapply


class MapplyTests(unittest.TestCase):
    def testMethod(self):
        def compute(a,b,c=4):
            return '%d%d%d' % (a, b, c)
        values = {'a':2, 'b':3, 'c':5}
        v = mapply(compute, (), values)
        self.failUnlessEqual(v, '235')

        v = mapply(compute, (7,), values)
        self.failUnlessEqual(v, '735')

    def testClass(self):
        values = {'a':2, 'b':3, 'c':5}
        class c(object):
            a = 3
            def __call__(self, b, c=4):
                return '%d%d%d' % (self.a, b, c)
            compute = __call__
        cc = c()
        v = mapply(cc, (), values)
        self.failUnlessEqual(v, '335')

        del values['c']
        v = mapply(cc.compute, (), values)
        self.failUnlessEqual(v, '334')

        class c2:
            """Must be a classic class."""
            
        c2inst = c2()
        c2inst.__call__ = cc
        v = mapply(c2inst, (), values)
        self.failUnlessEqual(v, '334')

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(MapplyTests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

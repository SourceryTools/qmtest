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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Zope Python Expression Tests

$Id: test_zopepythonexpr.py 26787 2004-07-27 14:00:42Z jim $
"""
from unittest import TestCase, main, makeSuite
from zope.testing.cleanup import CleanUp

class Engine(object):

    def getTypes(self):
        return {}

class Context(object):

    _engine = Engine()

    def __init__(self, **kw):
        self.vars = kw

class Test(CleanUp, TestCase):

    def test(self):
        from zope.app.pagetemplate.engine import ZopePythonExpr
        from zope.security.interfaces import Forbidden

        expr = ZopePythonExpr('python', 'max(a,b)', Engine())
        self.assertEqual(expr(Context(a=1, b=2)), 2)
        expr = ZopePythonExpr(
            'python', '__import__("sys").__name__', Engine())
        self.assertEqual(expr(Context()), 'sys')
        expr = ZopePythonExpr('python', '__import__("sys").exit',
                              Engine())
        self.assertRaises(Forbidden, expr, Context())
        expr = ZopePythonExpr('python', 'open("x", "w")', Engine())
        self.assertRaises(NameError, expr, Context())

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

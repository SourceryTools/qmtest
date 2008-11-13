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
"""Unit tests for Dependable class.

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""
from unittest import TestCase, TestSuite, main, makeSuite
from zope.annotation.attribute import AttributeAnnotations
from zope.app.testing.placelesssetup import PlacelessSetup

class C(object):
    pass

class Test(PlacelessSetup, TestCase):

    def factory(self):
        from zope.app.dependable import Dependable
        return Dependable(AttributeAnnotations(C()))

    def testVerifyInterface(self):
        from zope.interface.verify import verifyObject
        from zope.app.dependable.interfaces import IDependable
        object = self.factory()
        verifyObject(IDependable, object)

    def testBasic(self):
        dependable = self.factory()
        self.failIf(dependable.dependents())
        dependable.addDependent('/a/b')
        dependable.addDependent('/c/d')
        dependable.addDependent('/c/e')
        dependable.addDependent('/c/d')
        dependents = list(dependable.dependents())
        dependents.sort()
        self.assertEqual(dependents, ['/a/b', '/c/d', '/c/e'])
        dependable.removeDependent('/c/d')
        dependents = list(dependable.dependents())
        dependents.sort()
        self.assertEqual(dependents, ['/a/b', '/c/e'])
        dependable.removeDependent('/c/d')
        dependents = list(dependable.dependents())
        dependents.sort()
        self.assertEqual(dependents, ['/a/b', '/c/e'])

    def testRelativeAbsolute(self):
        obj = self.factory()
        # Hack the object to have a parent path
        obj.pp = "/a/"
        obj.pplen = len(obj.pp)
        obj.addDependent("foo")
        self.assertEqual(obj.dependents(), ("/a/foo",))
        obj.removeDependent("/a/foo")
        self.assertEqual(obj.dependents(), ())
        obj.addDependent("/a/bar")
        self.assertEqual(obj.dependents(), ("/a/bar",))
        obj.removeDependent("bar")
        self.assertEqual(obj.dependents(), ())

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

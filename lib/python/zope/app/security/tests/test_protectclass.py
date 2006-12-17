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
"""Test handler for 'protectClass' directive

$Id: test_protectclass.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.interface import implements
from zope.security.checker import selectChecker
from zope.security.permission import Permission
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup

from zope.app.security.interfaces import IPermission
from zope.app.security.protectclass import protectName, protectLikeUnto
from zope.app.security.protectclass import protectSetAttribute
from zope.app.security.tests.modulehookup import *

NOTSET = []

P1 = "extravagant"
P2 = "paltry"

class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()

        ztapi.provideUtility(IPermission, Permission(P1), P1)
        ztapi.provideUtility(IPermission, Permission(P2), P2)

        class B(object):
            def m1(self):
                return "m1"
            def m2(self):
                return "m2"

        class C(B):
            implements(I)
            def m3(self):
                return "m3"
            def m4(self):
                return "m4"

        TestModule.test_base = B
        TestModule.test_class = C
        TestModule.test_instance = C()
        self.assertState()

    def tearDown(self):
        super(Test, self).tearDown()
        TestModule.test_class = None

    def assertState(self, m1P=NOTSET, m2P=NOTSET, m3P=NOTSET):
        "Verify that class, instance, and methods have expected permissions."
        checker = selectChecker(TestModule.test_instance)
        self.assertEqual(checker.permission_id('m1'), (m1P or None))
        self.assertEqual(checker.permission_id('m2'), (m2P or None))
        self.assertEqual(checker.permission_id('m3'), (m3P or None))

    def assertSetattrState(self, m1P=NOTSET, m2P=NOTSET, m3P=NOTSET):
        "Verify that class, instance, and methods have expected permissions."
        checker = selectChecker(TestModule.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), (m1P or None))
        self.assertEqual(checker.setattr_permission_id('m2'), (m2P or None))
        self.assertEqual(checker.setattr_permission_id('m3'), (m3P or None))

    # "testSimple*" exercises tags that do NOT have children.  This mode
    # inherently sets the instances as well as the class attributes.

    def testSimpleMethodsPlural(self):
        protectName(TestModule.test_class, 'm1', P1)
        protectName(TestModule.test_class, 'm3', P1)
        self.assertState(m1P=P1, m3P=P1)

    def testLikeUntoOnly(self):
        protectName(TestModule.test_base, 'm1', P1)
        protectName(TestModule.test_base, 'm2', P1)
        protectSetAttribute(TestModule.test_base, 'm1', P1)
        protectSetAttribute(TestModule.test_base, 'm2', P1)
        protectLikeUnto(TestModule.test_class, TestModule.test_base)
        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertState(m1P=P1, m2P=P1)
        self.assertSetattrState(m1P=P1, m2P=P1)

    def assertSetattrState(self, m1P=NOTSET, m2P=NOTSET, m3P=NOTSET):
        "Verify that class, instance, and methods have expected permissions."
        checker = selectChecker(TestModule.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), (m1P or None))
        self.assertEqual(checker.setattr_permission_id('m2'), (m2P or None))
        self.assertEqual(checker.setattr_permission_id("m3"), (m3P or None))

    def testSetattr(self):
        protectSetAttribute(TestModule.test_class, 'm1', P1)
        protectSetAttribute(TestModule.test_class, 'm3', P1)
        self.assertSetattrState(m1P=P1, m3P=P1)

    def testLikeUntoAsDefault(self):
        protectName(TestModule.test_base, 'm1', P1)
        protectName(TestModule.test_base, 'm2', P1)
        protectSetAttribute(TestModule.test_base, 'm1', P1)
        protectSetAttribute(TestModule.test_base, 'm2', P1)
        protectLikeUnto(TestModule.test_class, TestModule.test_base)
        protectName(TestModule.test_class, 'm2', P2)
        protectName(TestModule.test_class, 'm3', P2)
        protectSetAttribute(TestModule.test_class, 'm2', P2)
        protectSetAttribute(TestModule.test_class, 'm3', P2)
        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertState(m1P=P1, m2P=P2, m3P=P2)
        self.assertSetattrState(m1P=P1, m2P=P2, m3P=P2)

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

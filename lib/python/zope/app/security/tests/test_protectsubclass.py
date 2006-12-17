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
"""Test proper protection of inherited methods

$Id: test_protectsubclass.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.security.checker import selectChecker
from zope.security.permission import Permission
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup

from zope.app.security.interfaces import IPermission
from zope.app.security.protectclass import protectName

class Test(PlacelessSetup, unittest.TestCase):

    def testInherited(self):

        class B1(object):
            def g(self): return 'B1.g'

        class B2(object):
            def h(self): return 'B2.h'

        class S(B1, B2):
            pass

        ztapi.provideUtility(IPermission, Permission('B1', ''), 'B1')
        ztapi.provideUtility(IPermission, Permission('S', ''), 'S')
        protectName(B1, 'g', 'B1')
        protectName(S, 'g', 'S')
        protectName(S, 'h', 'S')

        self.assertEqual(selectChecker(B1()).permission_id('g'), 'B1')
        self.assertEqual(selectChecker(B2()).permission_id('h'), None)
        self.assertEqual(selectChecker(S()).permission_id('g'), 'S')
        self.assertEqual(selectChecker(S()).permission_id('h'), 'S')

        self.assertEqual(S().g(), 'B1.g')
        self.assertEqual(S().h(), 'B2.h')


def test_suite():
    return unittest.makeSuite(Test)

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

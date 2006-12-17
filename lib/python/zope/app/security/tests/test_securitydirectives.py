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
"""Security Directives Tests

$Id: test_securitydirectives.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.configuration.config import ConfigurationConflictError
from zope.configuration import xmlconfig

from zope.app import zapi
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup

from zope.app.security.interfaces import IAuthentication, IPermission
from zope.app.security.principalregistry import principalRegistry
from zope.app.security.settings import Allow
import zope.app.security.tests


class TestBase(PlacelessSetup):

    def setUp(self):
        super(TestBase, self).setUp()
        ztapi.provideUtility(IAuthentication, principalRegistry)


class TestPrincipalDirective(TestBase, unittest.TestCase):

    def testRegister(self):
        context = xmlconfig.file("principal.zcml", zope.app.security.tests)
        reg=principalRegistry

        p = reg.getPrincipal('zope.p1')
        self.assertEqual(p.id, 'zope.p1')
        self.assertEqual(p.title, 'Sir Tim Peters')
        self.assertEqual(p.description, 'Tim Peters')
        p = reg.getPrincipal('zope.p2')
        self.assertEqual(p.id, 'zope.p2')
        self.assertEqual(p.title, 'Sir Jim Fulton')
        self.assertEqual(p.description, 'Jim Fulton')

        self.assertEqual(len(reg.getPrincipals('')), 2)


class TestPermissionDirective(TestBase, unittest.TestCase):

    def testRegister(self):
        context = xmlconfig.file("perm.zcml", zope.app.security.tests)
        perm = zapi.getUtility(IPermission, "Can.Do.It")
        self.failUnless(perm.id.endswith('Can.Do.It'))
        self.assertEqual(perm.title, 'A Permissive Permission')
        self.assertEqual(perm.description,
                         'This permission lets you do anything')

    def testDuplicationRegistration(self):
        self.assertRaises(ConfigurationConflictError, xmlconfig.file,
                          "perm_duplicate.zcml", zope.app.security.tests)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPrincipalDirective),
        unittest.makeSuite(TestPermissionDirective),
        ))

if __name__ == '__main__':
    unittest.main()

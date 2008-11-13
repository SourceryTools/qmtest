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

$Id: test_securitydirectives.py 80107 2007-09-26 14:58:39Z rogerineichen $
"""
import unittest

import zope.component
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationConflictError
from zope.security.interfaces import IPermission
from zope.security.permission import Permission

from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.security.interfaces import IAuthentication
from zope.app.security.principalregistry import principalRegistry

from zope.securitypolicy.role import Role
from zope.securitypolicy.interfaces import Allow
from zope.securitypolicy.interfaces import IRole
from zope.securitypolicy.rolepermission import \
    rolePermissionManager as role_perm_mgr
from zope.securitypolicy.principalpermission import \
    principalPermissionManager as principal_perm_mgr
from zope.securitypolicy.principalrole import \
    principalRoleManager as principal_role_mgr
import zope.securitypolicy.tests


def defineRole(id, title=None, description=None):
    role = Role(id, title, description)
    ztapi.provideUtility(IRole, role, name=role.id)
    return role


class TestBase(PlacelessSetup):

    def setUp(self):
        super(TestBase, self).setUp()
        ztapi.provideUtility(IAuthentication, principalRegistry)


class TestRoleDirective(TestBase, unittest.TestCase):

    def testRegister(self):
        context = xmlconfig.file("role.zcml", zope.securitypolicy.tests)

        role = zope.component.getUtility(IRole, "zope.Everyperson")
        self.failUnless(role.id.endswith('Everyperson'))
        self.assertEqual(role.title, 'Tout le monde')
        self.assertEqual(role.description,
                         'The common man, woman, person, or thing')

    def testDuplicationRegistration(self):
        self.assertRaises(ConfigurationConflictError, xmlconfig.file,
                          "role_duplicate.zcml", zope.securitypolicy.tests)


class TestSecurityMapping(TestBase, unittest.TestCase):

    def setUp(self):
        super(TestSecurityMapping, self).setUp()
        ztapi.provideUtility(IPermission, Permission('zope.Foo', ''),
                             name='zope.Foo')
        defineRole("zope.Bar", '', '')
        principalRegistry.definePrincipal("zope.Blah", '', '')
        self.context = xmlconfig.file("mapping.zcml", zope.securitypolicy.tests)

    def test_PermRoleMap(self):
        roles = role_perm_mgr.getRolesForPermission("zope.Foo")
        perms = role_perm_mgr.getPermissionsForRole("zope.Bar")

        self.assertEqual(len(roles), 1)
        self.failUnless(("zope.Bar",Allow) in roles)

        self.assertEqual(len(perms), 1)
        self.failUnless(("zope.Foo",Allow) in perms)

    def test_PermPrincipalMap(self):
        principals = principal_perm_mgr.getPrincipalsForPermission("zope.Foo")
        perms = principal_perm_mgr.getPermissionsForPrincipal("zope.Blah")

        self.assertEqual(len(principals), 1)
        self.failUnless(("zope.Blah", Allow) in principals)

        self.assertEqual(len(perms), 1)
        self.failUnless(("zope.Foo", Allow) in perms)

    def test_RolePrincipalMap(self):
        principals = principal_role_mgr.getPrincipalsForRole("zope.Bar")
        roles = principal_role_mgr.getRolesForPrincipal("zope.Blah")

        self.assertEqual(len(principals), 1)
        self.failUnless(("zope.Blah", Allow) in principals)

        self.assertEqual(len(roles), 1)
        self.failUnless(("zope.Bar", Allow) in roles)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRoleDirective),
        unittest.makeSuite(TestSecurityMapping),
        ))

if __name__ == '__main__':
    unittest.main()

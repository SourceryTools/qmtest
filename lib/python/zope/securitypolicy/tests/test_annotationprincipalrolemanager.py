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
"""Test handler for PrincipalRoleManager module.

$Id: test_annotationprincipalrolemanager.py 80107 2007-09-26 14:58:39Z rogerineichen $
"""
import unittest
import zope.component
from zope.interface import implements
from zope.annotation.interfaces import IAttributeAnnotatable

from zope.app.security.principalregistry import principalRegistry
from zope.app.component.testing import PlacefulSetup

from zope.securitypolicy.principalrole import AnnotationPrincipalRoleManager
from zope.securitypolicy.interfaces import Allow, Deny
from zope.securitypolicy.interfaces import IRole
from zope.securitypolicy.role import Role

class Manageable(object):
    implements(IAttributeAnnotatable)

def defineRole(id, title=None, description=None):
    role = Role(id, title, description)
    zope.component.provideUtility(role, IRole, name=role.id)
    return role

class Test(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)

    def _make_principal(self, id=None, title=None):
        p = principalRegistry.definePrincipal(
            id or 'APrincipal',
            title or 'A Principal',
            login = id or 'APrincipal')
        return p.id

    def _make_roleManager(self, obj=None):
        if obj is None:
            obj = Manageable()
        return AnnotationPrincipalRoleManager(obj)

    def testUnboundPrincipalRole(self):
        principalRoleManager = self._make_roleManager()
        role = defineRole('ARole', 'A Role').id
        principal = self._make_principal()
        self.assertEqual(
            principalRoleManager.getPrincipalsForRole(role), [])
        self.assertEqual(
            principalRoleManager.getRolesForPrincipal(principal), [])

    def testPrincipalRoleAllow(self):
        principalRoleManager = self._make_roleManager()
        role = defineRole('ARole', 'A Role').id
        principal = self._make_principal()
        principalRoleManager.assignRoleToPrincipal(role, principal)
        self.assertEqual(principalRoleManager.getPrincipalsForRole(role),
                         [(principal, Allow)])
        self.assertEqual(principalRoleManager.getRolesForPrincipal(principal),
                         [(role, Allow)])

    def testPrincipalRoleDeny(self):
        principalRoleManager = self._make_roleManager()
        role = defineRole('ARole', 'A Role').id
        principal = self._make_principal()
        principalRoleManager.removeRoleFromPrincipal(role, principal)
        self.assertEqual(principalRoleManager.getPrincipalsForRole(role),
                         [(principal, Deny)])
        self.assertEqual(principalRoleManager.getRolesForPrincipal(principal),
                         [(role, Deny)])

    def testPrincipalRoleUnset(self):
        principalRoleManager = self._make_roleManager()
        role = defineRole('ARole', 'A Role').id
        principal = self._make_principal()
        principalRoleManager.removeRoleFromPrincipal(role, principal)
        principalRoleManager.unsetRoleForPrincipal(role, principal)
        self.assertEqual(principalRoleManager.getPrincipalsForRole(role),
                         [])
        self.assertEqual(principalRoleManager.getRolesForPrincipal(principal),
                         [])

    def testManyRolesOnePrincipal(self):
        principalRoleManager = self._make_roleManager()
        role1 = defineRole('Role One', 'Role #1').id
        role2 = defineRole('Role Two', 'Role #2').id
        prin1 = self._make_principal()
        principalRoleManager.assignRoleToPrincipal(role1, prin1)
        principalRoleManager.assignRoleToPrincipal(role2, prin1)
        roles = principalRoleManager.getRolesForPrincipal(prin1)
        self.assertEqual(len(roles), 2)
        self.failUnless((role1, Allow) in roles)
        self.failUnless((role2, Allow) in roles)

    def testManyPrincipalsOneRole(self):
        principalRoleManager = self._make_roleManager()
        role1 = defineRole('Role One', 'Role #1').id
        prin1 = self._make_principal()
        prin2 = self._make_principal('Principal 2', 'Principal Two')
        principalRoleManager.assignRoleToPrincipal(role1, prin1)
        principalRoleManager.assignRoleToPrincipal(role1, prin2)
        principals = principalRoleManager.getPrincipalsForRole(role1)
        self.assertEqual(len(principals), 2)
        self.failUnless((prin1, Allow) in principals)
        self.failUnless((prin2, Allow) in principals)

    def testPrincipalsAndRoles(self):
        principalRoleManager = self._make_roleManager()
        principalsAndRoles = principalRoleManager.getPrincipalsAndRoles()
        self.assertEqual(len(principalsAndRoles), 0)
        role1 = defineRole('Role One', 'Role #1').id
        role2 = defineRole('Role Two', 'Role #2').id
        prin1 = self._make_principal()
        prin2 = self._make_principal('Principal 2', 'Principal Two')
        principalRoleManager.assignRoleToPrincipal(role1, prin1)
        principalRoleManager.assignRoleToPrincipal(role1, prin2)
        principalRoleManager.assignRoleToPrincipal(role2, prin1)
        principalsAndRoles = principalRoleManager.getPrincipalsAndRoles()
        self.assertEqual(len(principalsAndRoles), 3)
        self.failUnless((role1, prin1, Allow) in principalsAndRoles)
        self.failUnless((role1, prin2, Allow) in principalsAndRoles)
        self.failUnless((role2, prin1, Allow) in principalsAndRoles)

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

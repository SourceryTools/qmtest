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
"""Role-Permission View Tests

$Id: test_rolepermissionview.py 80149 2007-09-26 22:00:18Z rogerineichen $
"""
import unittest

import zope.interface
from zope.i18n.interfaces import ITranslationDomain
from zope.i18nmessageid import Message
from zope.publisher.browser import TestRequest, BrowserView
from zope.exceptions.interfaces import UserError
from zope.security.permission import Permission
from zope.security.interfaces import IPermission

from zope.app.testing import ztapi
from zope.app.component.testing import PlacefulSetup

from zope.securitypolicy.role import Role
from zope.securitypolicy.interfaces import IRole

from zope.app.securitypolicy.browser.tests.rolepermissionmanager import \
     RolePermissionManager
from zope.app.securitypolicy.browser.rolepermissionview import \
     RolePermissionView

class RolePermissionView(RolePermissionView, BrowserView):
    """Adding BrowserView to Utilities; this is usually done by ZCML."""

class TranslationDomain:
    zope.interface.implements(ITranslationDomain)

    def __init__(self, **translations):
        self.translations = translations

    def translate(self, msgid, *ignored, **also_ignored):
        return self.translations.get(msgid, msgid)


def defineRole(id, title=None, description=None):
    role = Role(id, title, description)
    ztapi.provideUtility(IRole, role, name=role.id)
    return role

def definePermission(id, title=None, description=None):
    permission = Permission(id, title, description)
    ztapi.provideUtility(IPermission, permission, name=permission.id)
    return permission

class FakeSiteManager:

    def __init__(self, site):
        self.__parent__ = site

class Test(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)
        defineRole('manager', Message('Manager', 'testdomain'))
        defineRole('member',  Message('Member', 'testdomain'))
        definePermission('read', Message('Read', 'testdomain'))
        definePermission('write', Message('Write', 'testdomain'))
        site = RolePermissionManager()
        self.view = RolePermissionView(FakeSiteManager(site), None)
        ztapi.provideUtility(ITranslationDomain,
                             TranslationDomain(Member="A Member",
                                               Write="A Write",
                                               ),
                             'testdomain')

    def testRoles(self):
        self.assertEqual([role.title for role in self.view.roles()],
                         ["Member", "Manager"])

    def testPermisssions(self):
        self.assertEqual([role.title for role in self.view.permissions()],
                         ["Write", "Read"])

    def testMatrix(self):
        roles = self.view.roles()
        permissions = self.view.permissions()

        #         manager  member
        # read       +
        # write      .       -
        env = {
            'p0': 'read', 'p1': 'write',
            'r0': 'manager', 'r1': 'member',
            'p0r0': 'Allow',
            'p1r0': 'Unset', 'p1r1': 'Deny',
            'SUBMIT': 1
            }
        self.view.request = TestRequest(environ=env)
        self.view.update()
        permissionRoles = self.view.permissionRoles()
        for ip in range(len(permissionRoles)):
            permissionRole = permissionRoles[ip]
            rset = permissionRole.roleSettings()
            for ir in range(len(rset)):
                setting = rset[ir]
                r = roles[ir].id
                p = permissions[ip].id
                if setting == 'Allow':
                    self.failUnless(r == 'manager' and p == 'read')
                elif setting == 'Deny':
                    self.failUnless(r == 'member' and p == 'write')
                else:
                    self.failUnless(setting == 'Unset')

        #         manager  member
        # read       -
        # write      +
        env = {
            'p0': 'read', 'p1': 'write',
            'r0': 'manager', 'r1': 'member',
            'p0r0': 'Deny',
            'p1r0': 'Allow', 'p1r1': 'Unset',
            'SUBMIT': 1
            }
        self.view.request = TestRequest(environ=env)
        self.view.update()
        permissionRoles = self.view.permissionRoles()
        for ip in range(len(permissionRoles)):
            permissionRole = permissionRoles[ip]
            rset = permissionRole.roleSettings()
            for ir in range(len(rset)):
                setting = rset[ir]
                r = roles[ir].id
                p = permissions[ip].id
                if setting == 'Allow':
                    self.failUnless(r == 'manager' and p == 'write')
                elif setting == 'Deny':
                    self.failUnless(r == 'manager' and p == 'read')
                else:
                    self.failUnless(setting == 'Unset')

    def testPermissionRoles(self):
        env={'permission_id': 'write',
             'settings': ['Allow', 'Unset'],
             'SUBMIT_PERMS': 1}
        self.view.request = TestRequest(environ=env)
        self.view.update()
        permission = self.view.permissionForID('write')
        settings = permission.roleSettings()
        self.assertEquals(settings, ['Allow', 'Unset'])


        env={'permission_id': 'write',
             'settings': ['Unset', 'Deny'],
             'SUBMIT_PERMS': 1}
        self.view.request = TestRequest(environ=env)
        self.view.update()
        permission = self.view.permissionForID('write')
        settings = permission.roleSettings()
        self.assertEquals(settings, ['Unset', 'Deny'])

        env={'permission_id': 'write',
             'settings': ['Unset', 'foo'],
             'SUBMIT_PERMS': 1}
        self.view.request = TestRequest(environ=env)
        self.assertRaises(ValueError, self.view.update)

    def testRolePermissions(self):
        env={'Allow': ['read'],
             'Deny': ['write'],
             'SUBMIT_ROLE': 1,
             'role_id': 'member'}
        self.view.request = TestRequest(environ=env)
        self.view.update(1)
        role = self.view.roleForID('member')
        pinfos = role.permissionsInfo()
        for pinfo in pinfos:
            pid = pinfo['id']
            if pid == 'read':
                self.assertEquals(pinfo['setting'], 'Allow')
            if pid == 'write':
                self.assertEquals(pinfo['setting'], 'Deny')

        env={'Allow': [],
             'Deny': ['read'],
             'SUBMIT_ROLE': 1,
             'role_id': 'member'}
        self.view.request = TestRequest(environ=env)
        self.view.update()
        role = self.view.roleForID('member')
        pinfos = role.permissionsInfo()
        for pinfo in pinfos:
            pid = pinfo['id']
            if pid == 'read':
                self.assertEquals(pinfo['setting'], 'Deny')
            if pid == 'write':
                self.assertEquals(pinfo['setting'], 'Unset')


    def testRolePermissions_UserError(self):
        env={'Allow': ['read'],
             'Deny': ['read'],
             'SUBMIT_ROLE': 1,
             'role_id': 'member'}
        self.view.request = TestRequest(environ=env)
        self.assertRaises(UserError, self.view.update, 1)


def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

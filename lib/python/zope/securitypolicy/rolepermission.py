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
"""Permission to Roles Manager (Adapter)

$Id: rolepermission.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""
from zope.interface import implements

from zope.security.permission import allPermissions
from zope.securitypolicy.role import checkRole
from zope.securitypolicy.interfaces import Allow, Deny, Unset
from zope.securitypolicy.interfaces import IRolePermissionManager
from zope.securitypolicy.interfaces import IRolePermissionMap
from zope.securitypolicy.securitymap import AnnotationSecurityMap
from zope.securitypolicy.securitymap import SecurityMap


class AnnotationRolePermissionManager(AnnotationSecurityMap):
    """Provide adapter that manages role permission data in an object attribute
    """

    # the annotation key is a holdover from this module's old
    # location, but cannot change without breaking existing databases
    key = 'zope.app.security.AnnotationRolePermissionManager'

    implements(IRolePermissionManager)

    def grantPermissionToRole(self, permission_id, role_id):
        AnnotationSecurityMap.addCell(self, permission_id, role_id, Allow)

    def denyPermissionToRole(self, permission_id, role_id):
        AnnotationSecurityMap.addCell(self, permission_id, role_id, Deny)

    unsetPermissionFromRole = AnnotationSecurityMap.delCell
    getRolesForPermission = AnnotationSecurityMap.getRow
    getPermissionsForRole = AnnotationSecurityMap.getCol
    getRolesAndPermissions = AnnotationSecurityMap.getAllCells

    def getSetting(self, permission_id, role_id):
        return AnnotationSecurityMap.queryCell(
            self, permission_id, role_id, default=Unset)


class RolePermissionManager(SecurityMap):
    """Mappings between roles and permissions."""

    implements(IRolePermissionManager)

    def grantPermissionToRole(self, permission_id, role_id, check=True):
        '''See interface IRolePermissionMap'''

        if check:
            checkRole(None, role_id)

        self.addCell(permission_id, role_id, Allow)

    def grantAllPermissionsToRole(self, role_id):
        for permission_id in allPermissions(None):
            self.grantPermissionToRole(permission_id, role_id, False)

    def denyPermissionToRole(self, permission_id, role_id, check=True):
        '''See interface IRolePermissionMap'''

        if check:
            checkRole(None, role_id)

        self.addCell(permission_id, role_id, Deny)

    def unsetPermissionFromRole(self, permission_id, role_id):
        '''See interface IRolePermissionMap'''

        # Don't check validity intentionally.
        # After all, we certianly want to unset invalid ids.

        self.delCell(permission_id, role_id)

    def getRolesForPermission(self, permission_id):
        '''See interface IRolePermissionMap'''
        return self.getRow(permission_id)

    def getPermissionsForRole(self, role_id):
        '''See interface IRolePermissionMap'''
        return self.getCol(role_id)

    def getSetting(self, permission_id, role_id):
        '''See interface IRolePermissionMap'''
        return self.queryCell(permission_id, role_id)

    def getRolesAndPermissions(self):
        '''See interface IRolePermissionMap'''
        return self.getAllCells()

# Permissions are our rows, and roles are our columns
rolePermissionManager = RolePermissionManager()


# Register our cleanup with Testing.CleanUp to make writing unit tests
# simpler.
try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    pass
else:
    addCleanUp(rolePermissionManager._clear)
    del addCleanUp

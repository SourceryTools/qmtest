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
"""Mappings between principals and permissions, stored in an object locally.

$Id: principalpermission.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""

from zope.interface import implements
from zope.security.permission import allPermissions

from zope.securitypolicy.interfaces import Allow, Deny, Unset
from zope.securitypolicy.interfaces import IPrincipalPermissionManager
from zope.securitypolicy.securitymap import SecurityMap
from zope.securitypolicy.securitymap import AnnotationSecurityMap

from zope.app.security.principal import checkPrincipal


class AnnotationPrincipalPermissionManager(AnnotationSecurityMap):
    """Mappings between principals and permissions."""

    # the annotation key is a holdover from this module's old
    # location, but cannot change without breaking existing databases
    # It is also is misspelled, but that's OK. It just has to be unique.
    # we'll keep it as is, to prevent breaking old data:
    key = 'zopel.app.security.AnnotationPrincipalPermissionManager'

    implements(IPrincipalPermissionManager)

    def grantPermissionToPrincipal(self, permission_id, principal_id):
        AnnotationSecurityMap.addCell(self, permission_id, principal_id, Allow)

    def denyPermissionToPrincipal(self, permission_id, principal_id):
        AnnotationSecurityMap.addCell(self, permission_id, principal_id, Deny)

    unsetPermissionForPrincipal = AnnotationSecurityMap.delCell
    getPrincipalsForPermission = AnnotationSecurityMap.getRow
    getPermissionsForPrincipal = AnnotationSecurityMap.getCol

    def getSetting(self, permission_id, principal_id, default=Unset):
        return AnnotationSecurityMap.queryCell(
            self, permission_id, principal_id, default)
       
    getPrincipalsAndPermissions = AnnotationSecurityMap.getAllCells


class PrincipalPermissionManager(SecurityMap):
    """Mappings between principals and permissions."""

    implements(IPrincipalPermissionManager)

    def grantPermissionToPrincipal(self, permission_id, principal_id,
                                   check=True):
        ''' See the interface IPrincipalPermissionManager '''

        if check:
            checkPrincipal(None, principal_id)

        self.addCell(permission_id, principal_id, Allow)

    def grantAllPermissionsToPrincipal(self, principal_id):
        ''' See the interface IPrincipalPermissionManager '''

        for permission_id in allPermissions(None):
            self.grantPermissionToPrincipal(permission_id, principal_id, False)

    def denyPermissionToPrincipal(self, permission_id, principal_id,
                                  check=True):
        ''' See the interface IPrincipalPermissionManager '''

        if check:
            checkPrincipal(None, principal_id)

        self.addCell(permission_id, principal_id, Deny)

    def unsetPermissionForPrincipal(self, permission_id, principal_id):
        ''' See the interface IPrincipalPermissionManager '''

        # Don't check validity intentionally.
        # After all, we certianly want to unset invalid ids.

        self.delCell(permission_id, principal_id)

    def getPrincipalsForPermission(self, permission_id):
        ''' See the interface IPrincipalPermissionManager '''
        return self.getRow(permission_id)

    def getPermissionsForPrincipal(self, principal_id):
        ''' See the interface IPrincipalPermissionManager '''
        return self.getCol(principal_id)

    def getSetting(self, permission_id, principal_id, default=Unset):
        ''' See the interface IPrincipalPermissionManager '''
        return self.queryCell(permission_id, principal_id, default)

    def getPrincipalsAndPermissions(self):
        ''' See the interface IPrincipalPermissionManager '''
        return self.getAllCells()


# Permissions are our rows, and principals are our columns
principalPermissionManager = PrincipalPermissionManager()


# Register our cleanup with Testing.CleanUp to make writing unit tests
# simpler.
try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    pass
else:
    addCleanUp(principalPermissionManager._clear)
    del addCleanUp

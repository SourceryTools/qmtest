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
"""Mappings between principals and roles, stored in an object locally.

$Id: principalrole.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""
from zope.interface import implements

from zope.securitypolicy.interfaces import Allow, Deny, Unset
from zope.securitypolicy.interfaces import IPrincipalRoleManager
from zope.securitypolicy.securitymap import SecurityMap
from zope.securitypolicy.securitymap import AnnotationSecurityMap
from zope.securitypolicy.role import checkRole
from zope.app.security.principal import checkPrincipal


class AnnotationPrincipalRoleManager(AnnotationSecurityMap):
    """Mappings between principals and roles."""

    # the annotation key is a holdover from this module's old
    # location, but cannot change without breaking existing databases
    key = 'zope.app.security.AnnotationPrincipalRoleManager'

    implements(IPrincipalRoleManager)

    def assignRoleToPrincipal(self, role_id, principal_id):
        AnnotationSecurityMap.addCell(self, role_id, principal_id, Allow)

    def removeRoleFromPrincipal(self, role_id, principal_id):
        AnnotationSecurityMap.addCell(self, role_id, principal_id, Deny)

    unsetRoleForPrincipal = AnnotationSecurityMap.delCell
    getPrincipalsForRole = AnnotationSecurityMap.getRow
    getRolesForPrincipal = AnnotationSecurityMap.getCol
    
    def getSetting(self, role_id, principal_id):
        return AnnotationSecurityMap.queryCell(
            self, role_id, principal_id, default=Unset)

    getPrincipalsAndRoles = AnnotationSecurityMap.getAllCells


class PrincipalRoleManager(SecurityMap):
    """Mappings between principals and roles."""

    implements(IPrincipalRoleManager)

    def assignRoleToPrincipal(self, role_id, principal_id, check=True):
        ''' See the interface IPrincipalRoleManager '''

        if check:
            checkPrincipal(None, principal_id)
            checkRole(None, role_id)

        self.addCell(role_id, principal_id, Allow)

    def removeRoleFromPrincipal(self, role_id, principal_id, check=True):
        ''' See the interface IPrincipalRoleManager '''

        if check:
            checkPrincipal(None, principal_id)
            checkRole(None, role_id)

        self.addCell(role_id, principal_id, Deny)

    def unsetRoleForPrincipal(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleManager '''

        # Don't check validity intentionally.
        # After all, we certainly want to unset invalid ids.

        self.delCell(role_id, principal_id)

    def getPrincipalsForRole(self, role_id):
        ''' See the interface IPrincipalRoleMap '''
        return self.getRow(role_id)

    def getRolesForPrincipal(self, principal_id):
        ''' See the interface IPrincipalRoleMap '''
        return self.getCol(principal_id)

    def getSetting(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleMap '''
        return self.queryCell(role_id, principal_id, default=Unset)

    def getPrincipalsAndRoles(self):
        ''' See the interface IPrincipalRoleMap '''
        return self.getAllCells()

# Roles are our rows, and principals are our columns
principalRoleManager = PrincipalRoleManager()

# Register our cleanup with Testing.CleanUp to make writing unit tests
# simpler.
try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    pass
else:
    addCleanUp(principalRoleManager._clear)
    del addCleanUp

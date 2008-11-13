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
"""Security map to hold matrix-like relationships.

In all cases, 'setting' values are one of the defined constants
`Allow`, `Deny`, or `Unset`.

$Id: interfaces.py 70228 2006-09-19 16:31:47Z fdrake $
"""
from zope.interface import Interface
from zope.schema import TextLine, Text


# These are the "setting" values returned by several methods defined
# in these interfaces.  The implementation may move to another
# location in the future, so this should be the preferred module to
# import these from.
#
from zope.app.security.settings import Allow, Deny, Unset


class IRole(Interface):
    """A role object."""

    id = TextLine(
        title=u"Id",
        description=u"Id as which this role will be known and used.",
        readonly=True,
        required=True)

    title = TextLine(
        title=u"Title",
        description=u"Provides a title for the role.",
        required=True)

    description = Text(
        title=u"Description",
        description=u"Provides a description for the role.",
        required=False)



class IPrincipalRoleMap(Interface):
    """Mappings between principals and roles."""

    def getPrincipalsForRole(role_id):
        """Get the principals that have been granted a role.

        Return the list of (principal id, setting) who have been assigned or
        removed from a role.

        If no principals have been assigned this role,
        then the empty list is returned.
        """

    def getRolesForPrincipal(principal_id):
        """Get the roles granted to a principal.

        Return the list of (role id, setting) assigned or removed from
        this principal.

        If no roles have been assigned to
        this principal, then the empty list is returned.
        """

    def getSetting(role_id, principal_id):
        """Return the setting for this principal, role combination
        """

    def getPrincipalsAndRoles():
        """Get all settings.

        Return all the principal/role combinations along with the
        setting for each combination as a sequence of tuples with the
        role id, principal id, and setting, in that order.
        """


class IPrincipalRoleManager(IPrincipalRoleMap):
    """Management interface for mappings between principals and roles."""

    def assignRoleToPrincipal(role_id, principal_id):
        """Assign the role to the principal."""

    def removeRoleFromPrincipal(role_id, principal_id):
        """Remove a role from the principal."""

    def unsetRoleForPrincipal(role_id, principal_id):
        """Unset the role for the principal."""


class IRolePermissionMap(Interface):
    """Mappings between roles and permissions."""

    def getPermissionsForRole(role_id):
        """Get the premissions granted to a role.

        Return a sequence of (permission id, setting) tuples for the given
        role.

        If no permissions have been granted to this
        role, then the empty list is returned.
        """

    def getRolesForPermission(permission_id):
        """Get the roles that have a permission.

        Return a sequence of (role id, setting) tuples for the given
        permission.

        If no roles have been granted this permission, then the empty list is
        returned.
        """

    def getSetting(permission_id, role_id):
        """Return the setting for the given permission id and role id

        If there is no setting, Unset is returned
        """

    def getRolesAndPermissions():
        """Return a sequence of (permission_id, role_id, setting) here.

        The settings are returned as a sequence of permission, role,
        setting tuples.

        If no principal/role assertions have been made here, then the empty
        list is returned.
        """


class IRolePermissionManager(IRolePermissionMap):
    """Management interface for mappings between roles and permissions."""

    def grantPermissionToRole(permission_id, role_id):
        """Bind the permission to the role.
        """

    def denyPermissionToRole(permission_id, role_id):
        """Deny the permission to the role
        """

    def unsetPermissionFromRole(permission_id, role_id):
        """Clear the setting of the permission to the role.
        """


class IPrincipalPermissionMap(Interface):
    """Mappings between principals and permissions."""

    def getPrincipalsForPermission(permission_id):
        """Get the principas that have a permission.

        Return the list of (principal_id, setting) tuples that describe
        security assertions for this permission.

        If no principals have been set for this permission, then the empty
        list is returned.
        """

    def getPermissionsForPrincipal(principal_id):
        """Get the permissions granted to a principal.

        Return the list of (permission, setting) tuples that describe
        security assertions for this principal.

        If no permissions have been set for this principal, then the empty
        list is returned.
        """

    def getSetting(permission_id, principal_id):
        """Get the setting for a permission and principal.

        Get the setting (Allow/Deny/Unset) for a given permission and
        principal.
        """

    def getPrincipalsAndPermissions():
        """Get all principal permission settings.

        Get the principal security assertions here in the form
        of a list of three tuple containing
        (permission id, principal id, setting)
        """


class IPrincipalPermissionManager(IPrincipalPermissionMap):
    """Management interface for mappings between principals and permissions."""

    def grantPermissionToPrincipal(permission_id, principal_id):
        """Assert that the permission is allowed for the principal.
        """

    def denyPermissionToPrincipal(permission_id, principal_id):
        """Assert that the permission is denied to the principal.
        """

    def unsetPermissionForPrincipal(permission_id, principal_id):
        """Remove the permission (either denied or allowed) from the
        principal.
        """

class IGrantInfo(Interface):
    """Get grant info needed for checking access
    """

    def principalPermissionGrant(principal, permission):
        """Return the principal-permission grant if any

        The return value is one of Allow, Deny, or Unset
        """

    def getRolesForPermission(permission):
        """Return the role grants for the permission

        The role grants are an iterable of role, setting tuples, where
        setting is either Allow or Deny.
        """

    def getRolesForPrincipal(principal):
        """Return the role grants for the principal

        The role grants are an iterable of role, setting tuples, where
        setting is either Allow or Deny.
        """

class IGrantVocabulary(Interface):
    """Marker interface for register the RadioWidget."""

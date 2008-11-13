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
""" Register security related configuration directives.

$Id: metaconfigure.py 80108 2007-09-26 15:02:36Z rogerineichen $
"""
from zope.configuration.exceptions import ConfigurationError
from zope.component.zcml import utility

from zope.securitypolicy.interfaces import IRole 
from zope.securitypolicy.role import Role 
from zope.securitypolicy.rolepermission import \
     rolePermissionManager as role_perm_mgr
from zope.securitypolicy.principalpermission import \
     principalPermissionManager as principal_perm_mgr
from zope.securitypolicy.principalrole import \
     principalRoleManager as principal_role_mgr


def grant(_context, principal=None, role=None, permission=None):
    nspecified = ((principal is not None)
                  + (role is not None)
                  + (permission is not None)
                  )

    if nspecified != 2:
        raise ConfigurationError(
            "Exactly two of the principal, role, and permission attributes "
            "must be specified")

    if principal:
        if role:
            _context.action(
                discriminator = ('grantRoleToPrincipal', role, principal),
                callable = principal_role_mgr.assignRoleToPrincipal,
                args = (role, principal)
                )
        else:
            _context.action(
                discriminator = ('grantPermissionToPrincipal',
                                 permission,
                                 principal),
                callable = principal_perm_mgr.grantPermissionToPrincipal,
                args = (permission, principal)
                )
    else:
        _context.action(
            discriminator = ('grantPermissionToRole', permission, role),
            callable = role_perm_mgr.grantPermissionToRole,
            args = (permission, role)
            )

def grantAll(_context, principal=None, role=None):
    """Grant all permissions to a role or principal
    """
    nspecified = ((principal is not None)
                  + (role is not None)
                  )

    if nspecified != 1:
        raise ConfigurationError(
            "Exactly one of the principal and role attributes "
            "must be specified")

    if principal:
        _context.action(
            discriminator = ('grantAllPermissionsToPrincipal',
                             principal),
            callable =
            principal_perm_mgr.grantAllPermissionsToPrincipal,
            args = (principal, )
            )
    else:
        _context.action(
            discriminator = ('grantAllPermissionsToRole', role),
            callable = role_perm_mgr.grantAllPermissionsToRole,
            args = (role, )
            )


def defineRole(_context, id, title, description=''):
    role = Role(id, title, description)
    utility(_context, IRole, role, name=id)


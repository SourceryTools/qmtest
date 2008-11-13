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

$Id: interfaces.py 80149 2007-09-26 22:00:18Z rogerineichen $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.interfaces  This reference will be "
    "removed somedays",
    IRole = 'zope.securitypolicy.interfaces:IRole',
    IPrincipalRoleMap = 'zope.securitypolicy.interfaces:IPrincipalRoleMap',
    IPrincipalRoleManager = 'zope.securitypolicy.interfaces:IPrincipalRoleManager',
    IRolePermissionMap = 'zope.securitypolicy.interfaces:IRolePermissionMap',
    IRolePermissionManager = 'zope.securitypolicy.interfaces:IRolePermissionManager',
    IPrincipalPermissionMap = 'zope.securitypolicy.interfaces:IPrincipalPermissionMap',
    IPrincipalPermissionManager = 'zope.securitypolicy.interfaces:IPrincipalPermissionManager',
    IGrantInfo = 'zope.securitypolicy.interfaces:IGrantInfo',
    IGrantVocabulary = 'zope.securitypolicy.interfaces:IGrantVocabulary',
    )

zope.deferredimport.deprecated(
    "It has moved to zope.app.security.settings  This reference will be "
    "removed somedays",
    Allow = 'zope.app.security.settings:Allow',
    Deny = 'zope.app.security.settings:Deny',
    Unset = 'zope.app.security.settings:Unset',
    )

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

$Id: rolepermission.py 80467 2007-10-02 08:39:01Z regebro $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.rolepermission  This reference will be "
    "removed somedays",
    AnnotationRolePermissionManager = 'zope.securitypolicy.rolepermission:AnnotationRolePermissionManager',
    RolePermissionManager = 'zope.securitypolicy.rolepermission:RolePermissionManager',
    rolePermissionManager = 'zope.securitypolicy.rolepermission:rolePermissionManager',
    )

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

$Id: principalrole.py 80467 2007-10-02 08:39:01Z regebro $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.principalrole  This reference will be "
    "removed somedays",
    AnnotationPrincipalRoleManager = 'zope.securitypolicy.principalrole:AnnotationPrincipalRoleManager',
    PrincipalRoleManager = 'zope.securitypolicy.principalrole:PrincipalRoleManager',
    principalRoleManager = 'zope.securitypolicy.principalrole:principalRoleManager',
    )

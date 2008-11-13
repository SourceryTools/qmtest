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
"""Role implementation

$Id: role.py 80149 2007-09-26 22:00:18Z rogerineichen $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.role  This reference will be "
    "removed somedays",
    NULL_ID = 'zope.securitypolicy.role:NULL_ID',
    Role = 'zope.securitypolicy.role:Role',
    LocalRole = 'zope.securitypolicy.role:LocalRole',
    setIdOnActivation = 'zope.securitypolicy.role:setIdOnActivation',
    unsetIdOnDeactivation = 'zope.securitypolicy.role:unsetIdOnDeactivation',
    checkRole = 'zope.securitypolicy.role:checkRole',
    )

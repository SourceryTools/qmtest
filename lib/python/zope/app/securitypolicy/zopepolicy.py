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
"""Define Zope's default security policy

$Id: zopepolicy.py 80149 2007-09-26 22:00:18Z rogerineichen $
"""

import zope.deferredimport

zope.deferredimport.deprecated(
    "It has moved to zope.securitypolicy.zopepolicy  This reference will be "
    "removed somedays",
    globalPrincipalPermissionSetting = 'zope.securitypolicy.zopepolicy:globalPrincipalPermissionSetting',
    globalRolesForPermission = 'zope.securitypolicy.zopepolicy:globalRolesForPermission',
    globalRolesForPrincipal = 'zope.securitypolicy.zopepolicy:globalRolesForPrincipal',
    SettingAsBoolean = 'zope.securitypolicy.zopepolicy:SettingAsBoolean',
    CacheEntry = 'zope.securitypolicy.zopepolicy:CacheEntry',
    ZopeSecurityPolicy = 'zope.securitypolicy.zopepolicy:ZopeSecurityPolicy',
    settingsForObject = 'zope.securitypolicy.zopepolicy:settingsForObject',
    )

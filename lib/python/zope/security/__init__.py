##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Base security system

$Id: __init__.py 78815 2007-08-14 17:52:16Z jim $

"""

import zope.deferredimport

zope.deferredimport.define(
    checkPermission = 'zope.security.management:checkPermission',
    canWrite = 'zope.security.checker:canWrite',
    canAccess = 'zope.security.checker:canAccess',
    )

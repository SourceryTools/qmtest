##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Common definitions to avoid circular imports
"""

import threading

import zope.interface

import zope.security.interfaces

thread_local = threading.local()

class system_user(object):
    zope.interface.classProvides(zope.security.interfaces.IPrincipal)
    id = u'zope.security.management.system_user'
    title = u'Special System User that typically has all permissions'
    description = u''

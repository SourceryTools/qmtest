##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Principals.

$Id: principal.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.component import getUtility
from zope.app.security.interfaces import PrincipalLookupError
from zope.app.security.interfaces import IAuthentication

def checkPrincipal(context, principal_id):
    auth = getUtility(IAuthentication, context=context)
    try:
        if auth.getPrincipal(principal_id):
            return
    except PrincipalLookupError:
        pass

    raise ValueError("Undefined principal id", principal_id)

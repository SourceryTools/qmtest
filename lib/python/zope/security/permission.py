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
"""Permissions

$Id: permission.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.interface import implements
from zope.component import queryUtility, getUtilitiesFor
from zope.security.checker import CheckerPublic
from zope.security.interfaces import IPermission

class Permission(object):
    implements(IPermission)

    def __init__(self, id, title="", description=""):
        self.id = id
        self.title = title
        self.description = description

def checkPermission(context, permission_id):
    """Check whether a given permission exists in the provided context.

    >>> from zope.component import provideUtility
    >>> provideUtility(Permission('x'), IPermission, 'x')

    >>> checkPermission(None, 'x')
    >>> checkPermission(None, 'y')
    Traceback (most recent call last):
    ...
    ValueError: ('Undefined permission id', 'y')
    """
    if permission_id is CheckerPublic:
        return
    if not queryUtility(IPermission, permission_id, context=context):
        raise ValueError("Undefined permission id", permission_id)

def allPermissions(context=None):
    """Get the ids of all defined permissions

    >>> from zope.component import provideUtility
    >>> provideUtility(Permission('x'), IPermission, 'x')
    >>> provideUtility(Permission('y'), IPermission, 'y')

    >>> ids = list(allPermissions(None))
    >>> ids.sort()
    >>> ids
    [u'x', u'y']
    """
    for id, permission in getUtilitiesFor(IPermission, context):
        if id != u'zope.Public':
            yield id

##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Evolve the ZODB from Zope 3.1 to a Zope 3.2 compatible format.

$Id: evolve2.py 39886 2005-11-04 12:17:03Z hdima $
"""
__docformat__ = "reStructuredText"

from zope.app.authentication.principalfolder import IInternalPrincipal
from zope.app.component.interfaces import ISite
from zope.app.zopeappgenerations import getRootFolder

from zope.app.generations.utility import findObjectsProviding


generation = 2

def evolve(context):
    """Evolve the ZODB from a Zope 3.1 to a 3.2 compatible format.

    - Converts all internal principals to use new password managers.
    """
    root = getRootFolder(context)

    for site in findObjectsProviding(root, ISite):
        sm = site.getSiteManager()
        for principal in findObjectsProviding(sm, IInternalPrincipal):
            if not hasattr(principal, "_passwordManagerName"):
                principal._passwordManagerName = "Plain Text"
            if not hasattr(principal, "_password"):
                principal._password = principal.__dict__["password"]
                del principal.__dict__["password"]

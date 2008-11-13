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
"""Testing support code

This module provides some helper/stub objects for setting up interactions.

$Id: testing.py 40639 2005-12-07 21:49:15Z srichter $
"""

from zope import interface
from zope.security import interfaces

class Principal:

    interface.implements(interfaces.IPrincipal)

    def __init__(self, id, title=None, description='', groups=None):
        self.id = id
        self.title = title or id
        self.description = description
        if groups is not None:
            self.groups = groups
            interface.directlyProvides(self, interfaces.IGroupAwarePrincipal)

class Participation:

    interface.implements(interfaces.IParticipation)

    def __init__(self, principal):
        self.principal = principal
        self.interaction = None

##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""General exceptions

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface, implements

##############################################################################
# BBB 2006/04/03 - to be removed after 12 months

import zope.deferredimport
zope.deferredimport.deprecated(
    "UserError has been moved to zope.exceptions.interfaces. This "
    "reference will be removed in Zope 3.5.",
    UserError = 'zope.exceptions.interfaces:UserError',
    IUserError = 'zope.exceptions.interfaces:IUserError',
    )

#
##############################################################################

class ISystemErrorView(Interface):
    """Error views that can classify their contexts as system errors
    """

    def isSystemError():
        """Return a boolean indicating whether the error is a system errror
        """

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
"""System error indicator

$Id: systemerror.py 28280 2004-10-28 22:56:34Z jim $
"""

import zope.interface
import zope.app.exception.interfaces

class SystemErrorView:
    zope.interface.implements(zope.app.exception.interfaces.ISystemErrorView)

    def isSystemError(self):
        return True
    

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
"""Default service names

$Id: __init__.py 68856 2006-06-26 20:37:13Z tseaver $
"""
import warnings
warnings.warn("This module is deprecated and will go away in Zope 3.5.",
              DeprecationWarning, 2)

from zope.component.servicenames import *

Authentication = 'Authentication'
BrowserMenu = 'BrowserMenu'
ErrorLogging = 'ErrorLogging'
PrincipalAnnotation = 'PrincipalAnnotation'

##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Basic skin

$Id: __init__.py 65511 2006-02-27 05:24:24Z philikon $
"""
__docformat__ = 'restructuredtext'
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

class IBasicSkin(IDefaultBrowserLayer):
    """Basic skin that simply only contains the default layer and
    nothing else"""

# BBB 2006/02/18, to be removed after 12 months
import zope.app.skins
zope.app.skins.set('Basic', IBasicSkin)

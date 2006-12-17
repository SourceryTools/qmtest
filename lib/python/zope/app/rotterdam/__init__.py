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
"""``Rotterdam`` skin package.

$Id: __init__.py 65511 2006-02-27 05:24:24Z philikon $
"""
__docformat__ = "reStructuredText"
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

class rotterdam(IBrowserRequest):
    """Layer for registering Rotterdam-specific macros."""

class Rotterdam(rotterdam, IDefaultBrowserLayer):
    """The ``Rotterdam`` skin.

    It is available via ``++skin++Rotterdam``.
    """

# BBB 2006/02/18, to be removed after 12 months
import zope.app.skins
zope.app.skins.set('Rotterdam', Rotterdam)

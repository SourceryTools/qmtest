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
"""Deprecation Package

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = "reStructuredText"

from zope.deprecation.deprecation import deprecated, deprecate, ShowSwitch
from zope.deprecation.deprecation import moved

# This attribute can be used to temporarly deactivate deprecation
# warnings, so that backward-compatibility code can import other
# backward-compatiblity components without warnings being produced.

__show__ = ShowSwitch()

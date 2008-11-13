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
"""Convenience module to access registered layers

This module solely exists for backward compatibility reasons.  It is
to be removed by Zope 3.5.  The now deprecated browser:layers
directive puts a reference to the created interfaces in this module.

BBB 2006/02/18, to be removed after 12 months

$Id: __init__.py 68852 2006-06-26 20:01:24Z tseaver $
"""
import zope.deprecation

def set(name, obj):
    globals()[name] = obj
    zope.deprecation.deprecated(name, "The zope.app.layers module has "
                                "been deprecated and will be removed in "
                                "Zope 3.5.")

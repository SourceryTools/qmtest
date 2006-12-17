##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""API Documentation macros

$Id: macros.py 25177 2004-06-02 13:17:31Z jim $
"""
from zope.app.basicskin.standardmacros import StandardMacros

class InterfaceDetailsMacros(StandardMacros):
    """Page Template METAL macros for Interfaces"""
    macro_pages = ('iface_macros', 'component_macros', 'presentation_macros')

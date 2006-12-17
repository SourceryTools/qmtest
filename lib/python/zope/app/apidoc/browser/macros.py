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

$Id: macros.py 38994 2005-10-09 10:00:47Z amorat $
"""
from zope.app.basicskin.standardmacros import StandardMacros

BaseMacros = StandardMacros

class APIDocumentationMacros(BaseMacros):
    """Page Template METAL macros for API Documentation"""
    macro_pages = ('menu_macros', 'details_macros','static_menu_macros')

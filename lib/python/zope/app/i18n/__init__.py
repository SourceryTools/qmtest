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
"""Customization of zope.i18n for the Zope application server

$Id: __init__.py 80025 2007-09-25 16:27:41Z rogerineichen $
"""
__docformat__ = 'restructuredtext'

import zope.deferredimport


zope.deferredimport.deprecated(
    "It has moved to zope.i18nmessageid  This reference will be gone "
    "in Zope 3.6",
    ZopeMessageFactory = 'zope.i18nmessageid:ZopeMessageFactory',
    )

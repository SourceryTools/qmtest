#############################################################################
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
"""Component-related fields

This module will be gone in Zope 3.5.

$Id: fields.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

# BBB 2006/02/18, to be removed after 12 months
import zope.deferredimport
zope.deferredimport.deprecated(
    "It will no longer be available in Zope 3.5.  Layers are just simple "
    "interfaces now; use the GlobalInterface field instead.",
    LayerField = 'zope.app.component.back35:LayerField',
    )

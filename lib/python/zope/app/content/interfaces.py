##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Content-related interfaces.

$Id: interfaces.py 30516 2005-05-26 19:00:11Z fdrake $
"""
__docformat__ = 'restructuredtext'

from zope.interface.interfaces import IInterface

class IContentType(IInterface):
    """This interface represents a content type.

    If an **interface** provides this interface type, then all objects
    providing the **interface** are considered content objects.
    """

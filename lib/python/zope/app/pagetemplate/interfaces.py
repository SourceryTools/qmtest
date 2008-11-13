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
"""Interfaces for apis to make available to TALES

$Id: interfaces.py 28653 2004-12-20 18:17:18Z fdrake $
"""
__docformat__ = 'restructuredtext'

import zope.interface


class IURLQuote(zope.interface.Interface):

    def quote():
        """Return the objects URL quote representation."""

    def quote_plus():
        """Return the objects URL quote_plus representation."""

    def unquote():
        """Return the objects URL unquote representation."""

    def unquote_plus():
        """Return the objects URL unquote_plus  representation."""

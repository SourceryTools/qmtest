##############################################################################
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
"""Configuration handlers for 'tool' directive.

$Id: metaconfigure.py 67630 2006-04-27 00:54:03Z jim $
"""

import warnings


def tool(_context, interface, title, description=None,
         folder="tools", unique=False):
    warnings.warn("Tools are deprecated and no-longer used. "
                  "The tool directive will go away in Zope 3.5",
                  DeprecationWarning)

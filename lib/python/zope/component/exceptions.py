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
"""
$Id: exceptions.py 67630 2006-04-27 00:54:03Z jim $
"""

import warnings

warnings.warn("This module is deprecated and will go away in Zope 3.5. "
              "Use zope.component.interfaces instead.",
              DeprecationWarning, 2)

from zope.component.interfaces import ComponentLookupError
from zope.component.interfaces import Invalid, Misused


__all__ = ["ComponentLookupError",
           "Invalid",
           "Misused"]

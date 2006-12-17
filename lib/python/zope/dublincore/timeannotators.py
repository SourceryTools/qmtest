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
"""Objects that take care of annotating dublin core meta data times

$Id: timeannotators.py 66902 2006-04-12 20:16:30Z philikon $
"""
__docformat__ = 'restructuredtext'

from datetime import datetime
import pytz
from zope.dublincore.interfaces import IZopeDublinCore
from zope.security.proxy import removeSecurityProxy


def ModifiedAnnotator(event):
    dc = IZopeDublinCore(event.object, None)
    if dc is not None:
        # Principals that can modify objects do not necessary have permissions
        # to arbitrarily modify DC data, see issue 373
        dc = removeSecurityProxy(dc)
        dc.modified = datetime.now(pytz.utc)


def CreatedAnnotator(event):
    dc = IZopeDublinCore(event.object, None)
    if dc is not None:
        # Principals that can create objects do not necessary have permissions
        # to arbitrarily modify DC data, see issue 373
        dc = removeSecurityProxy(dc)
        now = datetime.now(pytz.utc)
        dc.created = now
        dc.modified = now

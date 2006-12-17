##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Filesystem synchronization support.

$Id: adapter.py 26731 2004-07-23 21:27:21Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.fssync.server.entryadapter import ObjectEntryAdapter
from zope.fssync.server.interfaces import IObjectFile

class DTMLPageAdapter(ObjectEntryAdapter):
    implements(IObjectFile)

    def getBody(self):
        return self.context.getSource()

    def setBody(self, data):
        self.context.setSource(data)

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
"""Filesystem synchronization support.

$Id: adapter.py 29695 2005-03-28 17:11:17Z fdrake $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.fssync.server.entryadapter import ObjectEntryAdapter, AttrMapping
from zope.fssync.server.interfaces import IObjectFile

class FileAdapter(ObjectEntryAdapter):
    """ObjectFile adapter for file objects.
    """
    implements(IObjectFile)

    def getBody(self):
        return self.context.data

    def setBody(self, data):
        self.context.data = data

    def extra(self):
        return AttrMapping(self.context, ('contentType',))

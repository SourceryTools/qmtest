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
"""Filesystem synchronization support for zope.dublincore.

$Id$
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.fssync.server.entryadapter import ObjectEntryAdapter
from zope.fssync.server.interfaces import IObjectFile

class ZDCAnnotationDataAdapter(ObjectEntryAdapter):

    implements(IObjectFile)

    def getBody(self):
        return dumps(self.context.data)

    def setBody(self, data):
        data = loads(data)
        self.context.clear()
        self.context.update(data)

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
""" Server Control View

$Id: zodbcontrol.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from ZODB.FileStorage.FileStorage import FileStorageError
from zope.app.i18n import ZopeMessageFactory as _
from zope.size import byteDisplay


class ZODBControlView(object):

    def getName(self):
        """Get the database name."""
        return self.request.publication.db.getName()

    def getSize(self):
        """Get the database size in a human readable format."""
        size = self.request.publication.db.getSize()
        if not isinstance(size, (int, long, float)):
            return str(size)
        return byteDisplay(size)

    def pack(self):
        """Do the packing!"""
        days = int(self.request.form.get('days', 0))
        status = ''
        if 'PACK' in self.request:
            try:
                self.request.publication.db.pack(days=days)
                status = _('ZODB successfully packed.')
            except FileStorageError, err:
                status = _(err)
        return status

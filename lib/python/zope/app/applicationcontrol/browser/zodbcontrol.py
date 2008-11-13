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

$Id: zodbcontrol.py 73536 2007-03-25 08:17:24Z dobe $
"""
__docformat__ = 'restructuredtext'

from ZODB.FileStorage.FileStorage import FileStorageError
from zope.app.applicationcontrol.i18n import ZopeMessageFactory as _
from zope.size import byteDisplay
from ZODB.interfaces import IDatabase
from zope import component

class ZODBControlView(object):

    status  = None
    
    @property
    def databases(self):
        res = []
        for name, db in component.getUtilitiesFor(
            IDatabase):
            d = dict(
                dbName = db.getName(),
                utilName = str(name),
                size = self._getSize(db),
                )
            res.append(d)
        return res
            
    def _getSize(self, db):
        """Get the database size in a human readable format."""
        size = db.getSize()        
        if not isinstance(size, (int, long, float)):
            return str(size)
        return byteDisplay(size)

    def update(self):
        if self.status is not None:
            return self.status
        status = []
        if 'PACK' in self.request.form:
            dbs = self.request.form.get('dbs', [])
            try:
                days = int(self.request.form.get('days','').strip() or 0)
            except ValueError:
                status.append(_('Error: Invalid Number'))
                self.status = status
                return self.status
            for dbName in dbs:
                db = component.getUtility(IDatabase, name=dbName)
                try:
                    db.pack(days=days)
                    status.append(_('ZODB "${name}" successfully packed.',
                               mapping=dict(name=str(dbName))))
                except FileStorageError, err:
                    status.append(_('ERROR packing ZODB "${name}": ${err}',
                                    mapping=dict(name=str(dbName), err=err)))
        self.status = status
        return self.status

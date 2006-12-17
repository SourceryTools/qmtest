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
"""Zope database adapter views

$Id: rdb.py 66859 2006-04-11 17:32:49Z jinty $
"""
from zope.rdb.interfaces import IManageableZopeDatabaseAdapter
from zope.rdb import queryForResults

class TestSQL(object):

    __used_for__ = IManageableZopeDatabaseAdapter

    def getTestResults(self):
        sql = self.request.form['sql']
        result = queryForResults(self.context(), sql)
        return result


class Connection(object):
    __used_for__ = IManageableZopeDatabaseAdapter

    def edit(self, dsn, encoding):
        self.context.setDSN(dsn)
        self.context.setEncoding(encoding)
        return self.request.response.redirect(self.request.URL[-1])

    def connect(self):
        self.context.connect()
        return self.request.response.redirect(self.request.URL[-1])

    def disconnect(self):
        self.context.disconnect()
        return self.request.response.redirect(self.request.URL[-1])

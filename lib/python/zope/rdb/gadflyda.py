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
"""Gadfly Database Adapter (batteries included)

$Id: gadflyda.py 66859 2006-04-11 17:32:49Z jinty $
"""
import gadfly
import os

from zope.rdb import ZopeDatabaseAdapter, parseDSN
from zope.rdb import DatabaseException, DatabaseAdapterError
from zope.rdb import ZopeConnection, ZopeCursor

GadflyError = DatabaseAdapterError


class GadflyAdapterCursor(ZopeCursor):

    def executemany(self, operation, parameters):
        command = operation.split(None, 1)[0].lower()
        if command not in ("insert", "update", "delete"):
            raise DatabaseAdapterError(
                "executemany() is not applicable for %r" % operation)

        operation, parameters = self._prepareOperation(operation, parameters)
        self.connection.registerForTxn()
        if command == "insert":
            self.execute(operation, parameters)
        else:
            for param in parameters:
                self.execute(operation, param)

class GadflyAdapterConnection(ZopeConnection):

    def cursor(self):
        return GadflyAdapterCursor(self.conn.cursor(), self)

class GadflyAdapter(ZopeDatabaseAdapter):
    """A Gadfly adapter for Zope3"""

    # The registerable object needs to have a container
    __name__ = __parent__ = None
    _v_connection = None
    paramstyle = 'qmark'

    def _connection_factory(self):
        """Create a Gadfly DBI connection based on the DSN.

        Only local (filesystem-based) Gadfly connections are supported
        at this moment."""

        conn_info = parseDSN(self.dsn)
        if conn_info['host'] != '' or conn_info['username'] != '' or \
           conn_info['port'] != '' or conn_info['password'] != '':
            raise DatabaseAdapterError(
                "DSN for GadflyDA must be of the form "
                "dbi://dbname or dbi://dbname;dir=directory."
                )

        connection = conn_info['dbname']
        dir = os.path.join(getGadflyRoot(),
                           conn_info['parameters'].get('dir', connection))

        if not os.path.isdir(dir):
            raise DatabaseAdapterError('Not a directory ' + dir)

        if not os.path.exists(os.path.join(dir, connection + ".gfd")):
            db = gadfly.gadfly()
            db.startup(connection, dir)
        else:
            db = gadfly.gadfly(connection, dir)

        return db

    def connect(self):
        if not self.isConnected():
            try:
                self._v_connection = GadflyAdapterConnection(
                    self._connection_factory(), self)
            except gadfly.error, error:
                raise DatabaseException(str(error))

_gadflyRoot = 'gadfly'

def setGadflyRoot(path='gadfly'):
    global _gadflyRoot
    _gadflyRoot = path

def getGadflyRoot():
    return _gadflyRoot

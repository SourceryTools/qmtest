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
"""Zope RDBMS Transaction Integration.

Provides a proxy for interaction between the zope transaction
framework and the db-api connection. Databases which want to support
sub transactions need to implement their own proxy.

$Id: __init__.py 66859 2006-04-11 17:32:49Z jinty $
"""
import re
import time, random, thread
from urllib import unquote_plus

from persistent import Persistent

import transaction
from transaction.interfaces import IDataManager

from zope.security.checker import NamesChecker

from zope.interface import implements
from zope.app.container.contained import Contained
from zope.rdb.interfaces import DatabaseException, DatabaseAdapterError
from zope.rdb.interfaces import IResultSet
from zope.rdb.interfaces import IZopeConnection, IZopeCursor
from zope.rdb.interfaces import IManageableZopeDatabaseAdapter
from zope.thread import local


DEFAULT_ENCODING = "utf-8"

def sqlquote(x):
    r"""
    Escape data suitable for inclusion in generated ANSI SQL92 code for
    cases where bound variables are not suitable.

    >>> sqlquote("Hi")
    "'Hi'"
    >>> sqlquote("It's mine")
    "'It''s mine'"
    >>> sqlquote("\\'")
    "'\\\\'''"
    >>> sqlquote(u"\\'")
    u"'\\\\'''"
    >>> sqlquote(32)
    32
    >>> sqlquote(None)
    'NULL'
    """
    if isinstance(x, (str, unicode)):
        x = "'%s'" % x.replace('\\', '\\\\').replace("'", "''")
    elif isinstance(x, (int, long, float)):
        pass
    elif x is None:
        x = 'NULL'
    else:
        raise TypeError('do not know how to handle type %s' % type(x))
    return x


class ResultSet(list):
    """Database Result Set.

    Currently we don't do lazy instantation of rows.
    """

    implements(IResultSet)
    __slots__ = ('columns',)

    def __init__(self, columns, rows):
        self.columns = tuple(columns)
        row_class = RowClassFactory(columns)
        super(ResultSet, self).__init__(map(row_class, rows))

    __safe_for_unpickling__ = True

    def __reduce__(self):
        cols = self.columns
        return (ResultSet,
                (cols, [[getattr(row, col) for col in cols] for row in self])
               )

    def __cmp__(self, other):
        if not isinstance(other, ResultSet):
            return super(ResultSet, self).__cmp__(other)
        c = cmp(self.columns, other.columns)
        if c:
            return c
        for row, other_row in zip(self, other):
            c = cmp(row, other_row)
            if c:
                return c
        return cmp(len(self), len(other))


class ZopeDatabaseAdapter(Persistent, Contained):

    implements(IManageableZopeDatabaseAdapter)

    # We need to store our connections in a thread local to ensure that
    # different threads do not accidently use the same connection. This
    # is important when instantiating database adapters using
    # rdb:provideConnection as the same ZopeDatabaseAdapter instance will
    # be used by all threads.
    _connections = local()

    def __init__(self, dsn):
        self.setDSN(dsn)
        self._unique_id = '%s.%s.%s' % (
                time.time(), random.random(), thread.get_ident()
                )

    def _get_v_connection(self):
        """We used to store the ZopeConnection in a volatile attribute.
           However this was not always thread safe.
        """
        return getattr(ZopeDatabaseAdapter._connections, self._unique_id, None)

    def _set_v_connection(self, value):
        setattr(ZopeDatabaseAdapter._connections, self._unique_id, value)

    _v_connection = property(_get_v_connection, _set_v_connection)

    def _connection_factory(self):
        """This method should be overwritten by all subclasses"""
        conn_info = parseDSN(self.dsn)

    def setDSN(self, dsn):
        assert dsn.startswith('dbi://'), "The DSN has to start with 'dbi://'"
        self.dsn = dsn

    def getDSN(self):
        return self.dsn

    def connect(self):
        if not self.isConnected():
            try:
                self._v_connection = ZopeConnection(
                    self._connection_factory(), self)
            except DatabaseException:
                raise
            # Note: I added the general Exception, since the DA can return
            # implementation-specific errors. But we really want to catch all
            # issues at this point, so that we can convert it to a
            # DatabaseException.
            except Exception, error:
                raise DatabaseException(str(error))

    def disconnect(self):
        if self.isConnected():
            self._v_connection.close()
            self._v_connection = None

    def isConnected(self):
        return self._v_connection is not None

    def __call__(self):
        self.connect()
        return self._v_connection

    # Pessimistic defaults
    paramstyle = 'pyformat'
    threadsafety = 0
    encoding = DEFAULT_ENCODING

    def setEncoding(self, encoding):
        # Check the encoding
        "".decode(encoding)
        self.encoding = encoding

    def getEncoding(self):
        return self.encoding

    def getConverter(self, type):
        'See IDBITypeInfo'
        return identity

def identity(x):
    return x

_dsnFormat = re.compile(
    r"dbi://"
    r"(((?P<username>.*?)(:(?P<password>.*?))?)?"
    r"(@(?P<host>.*?)(:(?P<port>.*?))?)?/)?"
    r"(?P<dbname>.*?)(;(?P<raw_params>.*))?"
    r"$"
    )

_paramsFormat = re.compile(r"([^=]+)=([^;]*);?")

def parseDSN(dsn):
    """Parses a database connection string.

    We could have the following cases:

       dbi://dbname
       dbi://dbname;param1=value...
       dbi://user/dbname
       dbi://user:passwd/dbname
       dbi://user:passwd/dbname;param1=value...
       dbi://user@host/dbname
       dbi://user:passwd@host/dbname
       dbi://user:passwd@host:port/dbname
       dbi://user:passwd@host:port/dbname;param1=value...

    Any values that might contain characters special for URIs need to be
    quoted as it would be returned by `urllib.quote_plus`.

    Return value is a mapping with the following keys:

       username     username (if given) or an empty string
       password     password (if given) or an empty string
       host         host (if given) or an empty string
       port         port (if given) or an empty string
       dbname       database name
       parameters   a mapping of additional parameters to their values
    """

    if not isinstance(dsn, (str, unicode)):
        raise ValueError('The dsn is not a string. It is a %r' % type(dsn))

    match = _dsnFormat.match(dsn)
    if match is None:
        raise ValueError('Invalid DSN; must start with "dbi://": %r' % dsn)

    result = match.groupdict("")
    raw_params = result.pop("raw_params")

    for key, value in result.items():
        result[key] = unquote_plus(value)

    params = _paramsFormat.findall(raw_params)
    result["parameters"] = dict([(unquote_plus(key), unquote_plus(value))
                                for key, value in params])

    return result


class ZopeCursor(object):
    implements(IZopeCursor)

    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    def execute(self, operation, parameters=None):
        """Executes an operation, registering the underlying
        connection with the transaction system.  """
        operation, parameters = self._prepareOperation(operation, parameters)
        self.connection.registerForTxn()
        if parameters is None:
            return self.cursor.execute(operation)
        return self.cursor.execute(operation, parameters)

    def executemany(self, operation, parameters):
        """Executes an operation, registering the underlying
        connection with the transaction system.  """
        operation, parameters = self._prepareOperation(operation, parameters)
        # If executemany() is not defined pass parameters
        # to execute() as defined by DB API v.1
        method = getattr(self.cursor, "executemany", self.cursor.execute)
        self.connection.registerForTxn()
        return method(operation, parameters)

    def _prepareOperation(self, operation, parameters):
        encoding = self.connection.getTypeInfo().getEncoding()
        if isinstance(operation, unicode):
            operation = operation.encode(encoding)
        parameters = self._prepareParameters(parameters, encoding)
        return operation, parameters

    def _prepareParameters(self, parameters, encoding):
        if isinstance(parameters, list):
            for i, v in enumerate(parameters):
                if isinstance(v, unicode):
                    parameters[i] = v.encode(encoding)
                else:
                    parameters[i] = self._prepareParameters(v, encoding)
        elif isinstance(parameters, tuple):
            parameters = list(parameters)
            for i, v in enumerate(parameters):
                if isinstance(v, unicode):
                    parameters[i] = v.encode(encoding)
            parameters = tuple(parameters)
        elif isinstance(parameters, dict):
            for k, v in parameters.items():
                if isinstance(v, unicode):
                    parameters[k] = v.encode(encoding)
        return parameters

    def __getattr__(self, key):
        return getattr(self.cursor, key)

    def fetchone(self):
        results = self.cursor.fetchone()
        if results is None:
            return None
        return self._convertTypes([results])[0]

    def fetchmany(self, *args, **kw):
        results = self.cursor.fetchmany(*args, **kw)
        return self._convertTypes(results)

    def fetchall(self):
        results = self.cursor.fetchall()
        return self._convertTypes(results)

    def _convertTypes(self, results):
        "Perform type conversion on query results"
        getConverter = self.connection.getTypeInfo().getConverter
        converters = [getConverter(col_info[1])
                      for col_info in self.cursor.description]
## A possible optimization -- need benchmarks to check if it is worth it
##      if [x for x in converters if x is not ZopeDatabaseAdapter.identity]:
##          return results  # optimize away

        def convertRow(row):
            return map(lambda converter, value: converter(value),
                       converters, row)

        return map(convertRow, results)

class ZopeConnection(object):

    implements(IZopeConnection)

    def __init__(self, conn, typeinfo):
        self.conn = conn
        self._txn_registered = False
        self._type_info = typeinfo

    def __getattr__(self, key):
        # The IDBIConnection interface is hereby implemented
        return getattr(self.conn, key)

    def cursor(self):
        'See IZopeConnection'
        return ZopeCursor(self.conn.cursor(), self)

    def registerForTxn(self):
        'See IZopeConnection'
        if not self._txn_registered:
            tm = ZopeDBTransactionManager(self)
            transaction.get().join(tm)
            self._txn_registered = True

    def commit(self):
        'See IDBIConnection'
        self._txn_registered = False
        self.conn.commit()

    def rollback(self):
        'See IDBIConnection'
        self._txn_registered = False
        self.conn.rollback()

    def getTypeInfo(self):
        'See IDBITypeInfoProvider'
        return self._type_info


def queryForResults(conn, query):
    """Convenience function to quickly execute a query."""

    cursor = conn.cursor()

    try:
        cursor.execute(query)
    except Exception, error:
        # Just catch the exception, so that we can convert it to a database
        # exception.
        raise DatabaseException(str(error))

    if cursor.description is not None:
        columns = [c[0] for c in cursor.description]
        results = cursor.fetchall()
    else:
        # Handle the case that the query was not a SELECT
        columns = []
        results = []

    return ResultSet(columns, results)


class ZopeDBTransactionManager(object):

    implements(IDataManager)

    def __init__(self, dbconn):
        self._dbconn = dbconn
        self.transaction_manager = transaction.manager

    def prepare(self, txn):
        pass

    def tpc_begin(self, txn):
        pass

    def tpc_vote(self, txn):
        pass

    def tpc_finish(self, txn):
        pass

    def tpc_abort(self, txn):
        pass

    def abort(self, txn):
        self._dbconn.rollback()

    def commit(self, txn):
        self._dbconn.commit()

    def sortKey(self):
        """
        ZODB uses a global sort order to prevent deadlock when it commits
        transactions involving multiple resource managers.  The resource
        manager must define a sortKey() method that provides a global ordering
        for resource managers.

        (excerpt from transaction/notes.txt)
        """
        return 'rdb' + str(id(self))

class Row(object):
    """Represents a row in a ResultSet"""

    def __init__(self, data):
        for k, v in zip(self.__slots__, data):
            setattr(self, k, v)

    def __str__(self):
        return "row class %s" % str(self.__slots__)

    def __cmp__(self, other):
        if not isinstance(other, Row):
            return super(Row, self).__cmp__(other)
        c = cmp(self.__slots__, other.__slots__)
        if c:
            return c
        for column in self.__slots__:
            c = cmp(getattr(self, column), getattr(other, column))
            if c:
                return c
        return 0

class InstanceOnlyDescriptor(object):
    __marker = object()
    def __init__(self, value=__marker):
        if value is not self.__marker:
            self.value = value

    def __get__(self, inst, cls=None):
        if inst is None:
            raise AttributeError
        return self.value

    def __set__(self, inst, value):
        self.value = value

    def __delete__(self, inst):
        del self.value

def RowClassFactory(columns):
    """Creates a Row object"""
    klass_namespace = {}
    klass_namespace['__Security_checker__'] = InstanceOnlyDescriptor(
        NamesChecker(columns))
    klass_namespace['__slots__'] = tuple(columns)

    return type('GeneratedRowClass', (Row,), klass_namespace)

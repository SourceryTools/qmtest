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
"""Relational Database Adapter interfaces.

$Id: interfaces.py 66857 2006-04-11 17:15:13Z jinty $
"""
from zope.interface import Interface
from zope.interface import Attribute
from zope.schema import TextLine
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('zope')


class IDBITypeInfoProvider(Interface):
    """This object can get the Type Info for a particular DBI
    implementation."""

    def getTypeInfo():
        """Return an IDBITypeInfo object."""

class IDBITypeInfo(Interface):
    """Database adapter specific information"""

    paramstyle = Attribute("""
        String constant stating the type of parameter marker formatting
        expected by the interface. Possible values are [2]:

       'qmark' = Question mark style, e.g. '...WHERE name=?'
       'numeric' = Numeric, positional style, e.g. '...WHERE name=:1'
       'named' = Named style, e.g. '...WHERE name=:name'
       'format' = ANSI C printf format codes, e.g. '...WHERE name=%s'
       'pyformat' = Python extended format codes, e.g. '...WHERE name=%(name)s'
       """)

    threadsafety = Attribute("""
        Integer constant stating the level of thread safety the interface
        supports. Possible values are:

            0 = Threads may not share the module.
            1 = Threads may share the module, but not connections.
            2 = Threads may share the module and connections.
            3 = Threads may share the module, connections and cursors.

        Sharing in the above context means that two threads may use a resource
        without wrapping it using a mutex semaphore to implement resource
        locking. Note that you cannot always make external resources thread
        safe by managing access using a mutex: the resource may rely on global
        variables or other external sources that are beyond your control.
        """)

    encoding = TextLine(
        title=_("Database encoding"),
        description=_("Encoding of the database content"),
        default=u"utf-8",
        required=False
        )

    def getEncoding():
        """Get the database encoding."""

    def setEncoding(encoding):
        """Set the database encoding."""

    def getConverter(type):
        """Return a converter function for field type matching key"""

class IResultSet(Interface):
    """Holds results, and allows iteration."""

    columns = Attribute("""A list of the column names of the returned result
                           set.""")

    def __getitem__(index):
        """Return a brain row for index."""


class DatabaseException(Exception):
    """Generic Database Error"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class DatabaseAdapterError(DatabaseException):
    pass

arraysize = 1 # default constant, symbolic

class IDBICursor(Interface):
    """DB API ICursor interface"""

    description = Attribute("""This read-only attribute is a sequence of
        7-item sequences. Each of these sequences contains information
        describing one result column: (name, type_code, display_size,
        internal_size, precision, scale, null_ok). This attribute will be None
        for operations that do not return rows or if the cursor has not had an
        operation invoked via the executeZZZ() method yet.

        The type_code can be interpreted by comparing it to the Type Objects
        specified in the section below. """)

    arraysize = Attribute("""This read/write attribute specifies the number of
        rows to fetch at a time with fetchmany(). It defaults to 1 meaning to
        fetch a single row at a time.

        Implementations must observe this value with respect to the
        fetchmany() method, but are free to interact with the database a
        single row at a time. It may also be used in the implementation of
        executemany().
        """)

    def close():
        """Close the cursor now (rather than whenever __del__ is called).  The
        cursor will be unusable from this point forward; an Error (or
        subclass) exception will be raised if any operation is attempted with
        the cursor.
        """

    def execute(operation, parameters=None):
        """Prepare and execute a database operation (query or
        command). Parameters may be provided as sequence or mapping and will
        be bound to variables in the operation. Variables are specified in a
        database-specific notation (see the module's paramstyle attribute for
        details). [5]

        A reference to the operation will be retained by the cursor. If the
        same operation object is passed in again, then the cursor can optimize
        its behavior. This is most effective for algorithms where the same
        operation is used, but different parameters are bound to it (many
        times).

        For maximum efficiency when reusing an operation, it is best to use
        the setinputsizes() method to specify the parameter types and sizes
        ahead of time. It is legal for a parameter to not match the predefined
        information; the implementation should compensate, possibly with a
        loss of efficiency.

        The parameters may also be specified as list of tuples to e.g. insert
        multiple rows in a single operation, but this kind of usage is
        depreciated: executemany() should be used instead.

        Return values are not defined.
        """

    def executemany(operation, seq_of_parameters):
        """Prepare a database operation (query or command) and then execute it
        against all parameter sequences or mappings found in the sequence
        seq_of_parameters.

        Modules are free to implement this method using multiple calls to the
        execute() method or by using array operations to have the database
        process the sequence as a whole in one call.

        The same comments as for execute() also apply accordingly to this
        method.

        Return values are not defined.
        """

    def fetchone():
        """Fetch the next row of a query result set, returning a single
        sequence, or None when no more data is available. [6]

        An Error (or subclass) exception is raised if the previous call to
        executeZZZ() did not produce any result set or no call was issued yet.
        """

    def fetchmany(size=arraysize):
        """Fetch the next set of rows of a query result, returning a sequence
        of sequences (e.g. a list of tuples). An empty sequence is returned
        when no more rows are available.

        The number of rows to fetch per call is specified by the parameter. If
        it is not given, the cursor's arraysize determines the number of rows
        to be fetched. The method should try to fetch as many rows as
        indicated by the size parameter. If this is not possible due to the
        specified number of rows not being available, fewer rows may be
        returned.

        An Error (or subclass) exception is raised if the previous call to
        executeZZZ() did not produce any result set or no call was issued yet.

        Note there are performance considerations involved with the size
        parameter. For optimal performance, it is usually best to use the
        arraysize attribute. If the size parameter is used, then it is best
        for it to retain the same value from one fetchmany() call to the next.
        """

    def fetchall():
        """Fetch all (remaining) rows of a query result, returning them as a
        sequence of sequences (e.g. a list of tuples). Note that the cursor's
        arraysize attribute can affect the performance of this operation.

        An Error (or subclass) exception is raised if the previous call to
        executeZZZ() did not produce any result set or no call was issued yet.
        """

class IDBIConnection(Interface):
    """A DB-API based Interface """

    def cursor():
        """Return a new IDBICursor Object using the connection.

        If the database does not provide a direct cursor concept, the module
        will have to emulate cursors using other means to the extent needed by
        this specification.  """

    def commit():
        """Commit any pending transaction to the database. Note that if the
        database supports an auto-commit feature, this must be initially off.
        An interface method may be provided to turn it back on.

        Database modules that do not support transactions should implement
        this method with void functionality.
        """

    def rollback():
        """In case a database does provide transactions this method causes the
        database to roll back to the start of any pending transaction. Closing
        a connection without committing the changes first will cause an
        implicit rollback to be performed.  """

    def close():
        """Close the connection now (rather than whenever __del__ is
        called). The connection will be unusable from this point forward; an
        Error (or subclass) exception will be raised if any operation is
        attempted with the connection. The same applies to all cursor objects
        trying to use the connection.  """

class ISQLCommand(Interface):
    """Static SQL commands."""

    connectionName = Attribute("""The name of the database connection
    to use in getConnection """)

    def getConnection():
        """Get the database connection."""

    def __call__():
        """Execute an sql query and return a result object if appropriate"""

class IZopeDatabaseAdapter(IDBITypeInfo):
    """Interface for persistent object that returns
    volatile IZopeConnections."""

    def isConnected():
        """Check whether the Zope Connection is actually connected to the
        database."""

    def __call__():
        """Return an IZopeConnection object"""

class IZopeDatabaseAdapterManagement(Interface):

    def setDSN(dsn):
        """Set the DSN for the Adapter instance"""

    def getDSN():
        """Get the DSN of the Adapter instance"""

    dsn = TextLine(
        title=_("DSN"),
        description=_(
        "Specify the DSN (Data Source Name) of the database. "
        "Examples include:\n"
        "\n"
        "dbi://dbname\n"
        "dbi://dbname;param1=value...\n"
        "dbi://user:passwd/dbname\n"
        "dbi://user:passwd/dbname;param1=value...\n"
        "dbi://user:passwd@host:port/dbname\n"
        "dbi://user:passwd@host:port/dbname;param1=value...\n"
        "\n"
        "All values should be properly URL-encoded."),
        default=u"dbi://dbname",
        required=True)

    def connect():
        """Connect to the specified database."""

    def disconnect():
        """Disconnect from the database."""

class IManageableZopeDatabaseAdapter(IZopeDatabaseAdapter,
                                     IZopeDatabaseAdapterManagement):
    """Database adapters with management functions
    """

class IZopeConnection(IDBIConnection, IDBITypeInfoProvider):

    # An implementation of this object will be exposed to the
    # user. Therefore the Zope connection represents a connection in
    # the Zope sense, meaning that the object might not be actually
    # connected to a real relational database.

    def cursor():
        """Return an IZopeCursor object."""

    def registerForTxn():
        """Join the current transaction.

        This method should only be inovoked by the Zope/DB transaction
        manager.
        """

class IZopeCursor(IDBICursor):
    """An IDBICursor that integrates with Zope's transactions"""

    def execute(operation, parameters=None):
        """Executes an operation, registering the underlying connection with
        the transaction system.

        See IDBICursor for more detailed execute information.
        """

    def executemany(operation, seq_of_parameters):
        """Executes an operation, registering the underlying connection with
        the transaction system.

        See IDBICursor for more detailed executemany information.
        """

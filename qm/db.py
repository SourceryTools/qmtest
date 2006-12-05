########################################################################
#
# File:   db.py
# Author: Nathaniel Smith <njs@codesourcery.com
# Date:   2003-06-13
#
# Contents:
#   A few simple functions to help with connecting to SQL databases
#   and using the DB 2.0 API.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import os

########################################################################
# Classes
########################################################################

class Connection:
    """A wrapper around a DB 2.0 connection.

    Provides a minimal but consistent interface to an underlying
    database connection.  In particular, a 'Connection' quotes SQL
    queries as necessary for the underlying DB 2.0 connection."""

    def __init__(self, module_name, *args, **more_args):
        """Uses the given DB 2.0 module to connect to a database.

        'module_name' -- The DB 2.0-compliant module to use to connect,
        for example "pgdb".

        'args' -- Positional arguments to pass to the module's 'connect'
        method.

        'more_args' -- Keyword arguments to pass to the module's
        'connect' method."""

        # Last argument  must be a non-empty list or __import__ will
        # return the wrong module.
        self._module = __import__(module_name,
                                  globals(),
                                  locals(),
                                  [""])
        self._connection = self._module.connect(*args, **more_args)


    def close(self):

        self._connection.close()


    def commit(self):

        self._connection.commit()


    def rollback(self):

        self._connection.rollback()


    def execute(self, sql):
        """Execute a SQL statement in this database.

        If this database requires any overall quoting of the given SQL
        (for instance, doubling of %'s), it will be performed by this
        method.

        returns -- A database cursor.
        
        """

        # According to the DB 2.0 spec, the following lines should be
        # necessary.  But in fact it seems that the database modules we
        # use do not strip doubled %'s inside SQL string constants, and
        # do not try to expand parameters inside SQL string constants.
        # Since string constants are the main place where %'s may occur,
        # we do not quote %'s at all.
        #if self._module.paramstyle in ["format", "pyformat"]:
        #    sql = sql.replace("%", "%%")
        cursor = self._connection.cursor()
        
        cursor.execute(sql)
        return cursor
        

########################################################################
# Functions
########################################################################

def quote_string(string):
    """Quotes a string for SQL.

    'string' -- A string whose contents are to be used in an SQL literal
    string.

    returns -- A SQL literal string whose contents match that of
    'string'."""

    # Replace each ' with '', then surround with more 's.  Also double
    # backslashes.  It'd be nice to handle things like quoting non-ASCII
    # characters (by replacing them with octal escapes), but we don't.
    return "'" + string.replace("'", "''").replace("\\", "\\\\") + "'"

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

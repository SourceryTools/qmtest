########################################################################
#
# File:   gadfly_idb.py
# Author: Alex Samuel
# Date:   2000-12-21
#
# Contents:
#   IDB implementation using the Gadfly RDBMS.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

# To do:
#
#   * Cache issue_class and current revision number per iid.

########################################################################
# imports
########################################################################

import cPickle
import gadfly
import os
import os.path
import qm
import sql_idb

########################################################################
# classes
########################################################################

class GadflyIdb(sql_idb.SqlIdb):
    """IDB implementation using the Gadfly RDBMS."""

    # Instances of 'GadflyIdb' are externalized via pickling.  This
    # allows configuration and state information about the IDB that
    # isn't reflected in the underlying RDBMS to be made persistent.
    

    idb_database_name = "idb"
    """The Gadfly database name for the IDB."""


    def __init__(self, path, log_file=None, create_idb=0):
        """Create a new Gadfly IDB connection object.

        'path' -- The path to the Gadfly database.

        'log_file' -- If not 'None', a file object to which the SQL
        log will be written.

        'create_idb' -- If true, creates a new IDB from scratch.
        Otherwise, connects to an existing IDB."""

        # Perform base class initialiation.
        sql_idb.SqlIdb.__init__(self, path, create_idb)

        # Create or connect to the Gadfly database.
        if create_idb:
            self.__Create()
        else:
            self.__Load()

        # Connect to the Gadfly database.
        self.connection = gadfly.gadfly(GadflyIdb.idb_database_name, path)
        # Remember the SQL log file, if any.
        self.sql_log = log_file
        

    def __Create(self):
        """Create a new Gadfly IDB database.

        preconditions -- 'self.path' must be set."""

        # Create the database.
        connection = gadfly.gadfly()
        connection.startup(GadflyIdb.idb_database_name, self.path)
        # Apparently, Gadfly doesn't really set things up until a table is
        # created, so make a dummy one.
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE _dummy ( _dummy INTEGER )")
        # Commit and finish up.
        connection.commit()
        connection.close()
        # There are no issues classes initially.
        self.issue_classes = {}


    def __Load(self):
        """Load the IDB persistent state from a pickle.

        preconditions -- 'self.path' must be set."""

        pickle_path = self.__GetPicklePath()
        pickle_file = open(pickle_path, "r")
        self.issue_classes = cPickle.load(pickle_file)
        pickle_file.close()


    def Close(self):
        """Close the connection.

        Closes the database connection, and and writes persistent
        state to disk.  The log file, if any, is not closed
        automatically (unless it is unreferenced and thus deleted)."""

        pickle_path = self.__GetPicklePath()
        # Disconnect from the database.
        self.connection.close()
        self.connection = None
        # Dump the IDB's state.  Only the set of issue classes is
        # persistent. 
        pickle_file = open(pickle_path, "w")
        cPickle.dump(self.issue_classes, pickle_file)
        pickle_file.close()
        # Do any base class operations we might need to.
        sql_idb.SqlIdb.Close(self)


    def __GetPicklePath(self):
        """Return the path to the file containing the IDB pickle."""

        return os.path.join(self.path, "idb.pickle")


    def GetCursor(self):
        """Return a cursor for the database.

        Any outstanding operations are committed when the cursor is
        deleted.""" 

        # Obtain a cursor from Gadfly.
        cursor = self.connection.cursor()
        # Store a reference back to the IDB.
        cursor.idb = self
        # Dynamically subclass the cursor to add some extra behaviour.
        cursor.__class__ = GadflyCursor
        return cursor



class GadflyCursor(gadfly.GF_Cursor):
    """Extension of Gadfly cursor class."""

    def __del__(self):
        """Commit outstanding operations on deletion."""
        
        self.idb.connection.commit()


    def execute(self, statement=None, params=None):
        """Execute an SQL statement."""

        # Extract a pointer back to the IDB.
        idb = self.idb
        log = idb.sql_log
        # Write the statement being executed.
        if log is not None:
            log.write("SQL STATEMENT:\n  %s" % statement)
            if params != None:
                log.write(str(params))
            log.write("\n")
        try:
            # Execute the statement.
            gadfly.GF_Cursor.execute(self, statement, params)
            # Write the result.
            if log is not None:
                log.write("SQL RESULT:\n  %s\n\n" % self.pp())
        finally:
            if log is not None:
                log.flush()


        
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

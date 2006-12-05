########################################################################
#
# File:   sql_result_stream.py
# Author: Nathaniel Smith <njs@codesourcery.com>
# Date:   2003-06-13
#
# Contents:
#   SQLResultStream, SQLResultSource
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.fields
from qm.extension          import Extension
from qm.test.result_stream import ResultStream
from qm.test.result_reader import ResultReader
from qm.db                 import quote_string, Connection
from qm.test.result        import Result

########################################################################
# Classes
########################################################################

class _SQLConnected(Extension):
    """Mixin class for classes that need a database connection."""

    arguments = [
        qm.fields.TextField(
            name = "db_name",
            title = "Database name",
            description = "The PostgreSQL database to connect to.",
            verbatim = "true",
            default_value = ""),
        qm.fields.TextField(
            name = "db_module",
            title = "Database module",
            description = "The DB 2.0 module to use.",
            verbatim = "true",
            default_value = "pgdb"),
        qm.fields.PythonField(
            name = "connection"),
    ]

    def __init__(self, arguments = None, **args):

        if arguments: args.update(arguments)
        super(_SQLConnected, self).__init__(**args)

        if not self.connection:
            self.connection = Connection(self.db_module,
                                         database=self.db_name)



class SQLResultStream(ResultStream, _SQLConnected):
    """A 'SQLResultStream' writes results out to an SQL database.
    
    This class currently supports PostgreSQL only."""


    def __init__(self, arguments = None, **args):

        super(SQLResultStream, self).__init__(arguments, **args)

        run_id_cursor = self.connection.execute("""
            SELECT nextval('run_id_seq');
            """)
        (self._run_id,) = run_id_cursor.fetchone()

        self.connection.execute("""
            INSERT INTO runs (run_id) VALUES (%i)
            """ % (self._run_id,))


    def WriteAnnotation(self, key, value):

        self.connection.execute("""
            INSERT INTO run_annotations (run_id, key, value)
            VALUES (%i, %s, %s)
            """ % (self._run_id,
                   quote_string(key),
                   quote_string(value)))
        

    def WriteResult(self, result):

        self.connection.execute("""
            INSERT INTO results (run_id, result_id, kind, outcome)
            VALUES (%i, %s, %s, %s)
            """ % (self._run_id,
                   quote_string(result.GetId()),
                   quote_string(result.GetKind()),
                   quote_string(result.GetOutcome())))

        for key, value in result.items():
            self.connection.execute("""
                INSERT INTO result_annotations (run_id,
                                                result_id,
                                                result_kind,
                                                key,
                                                value)
                VALUES (%i, %s, %s, %s, %s)
                """ % (self._run_id,
                       quote_string(result.GetId()),
                       quote_string(result.GetKind()),
                       quote_string(key),
                       quote_string(value)))


    def Summarize(self):

        self.connection.commit()



class _Buffer:
    """A little buffering iterator with one-element rewind."""

    def __init__(self, size, get_more):
        """Create a '_Buffer'.

        'size' -- the number of items to hold in the buffer at a time.

        'get_more' -- a function taking a number as its sole argument;
                      should return a list of that many new items (or as
                      many items are left, whichever is less).
        """

        self.size = size
        self.get_more = get_more
        self.buffer = get_more(size)
        self.idx = 0
        # Needed for rewinding over buffer refills:
        self.last = None


    def next(self):
        """Returns the next item, refilling the buffer if necessary."""

        idx = self.idx
        if idx == len(self.buffer):
            self.buffer = self.get_more(self.size)
            self.idx = 0
            idx = 0
        if not self.buffer:
            raise StopIteration
        self.idx += 1
        self.last = self.buffer[idx]
        return self.buffer[idx]


    def rewind(self):

        if self.idx == 0:
            self.buffer.insert(0, self.last)
        else:
            self.idx -= 1


    def __iter__(self):

        return self



class SQLResultReader(ResultReader, _SQLConnected):
    """A 'SQLResultReader' reads result in from an SQL database.

    This class currently supports PostgreSQL only."""

    arguments = [
        qm.fields.IntegerField(
            name = "run_id",
            title = "Run ID",
        ),
    ]

    def __init__(self, arguments = None, **args):

        super(SQLResultReader, self).__init__(arguments, **args)

        self._batch_size = 1000

        self._LoadAnnotations()
        self._SetupResultCursors()


    def _LoadAnnotations(self):

        cursor = self.connection.execute("""
            SELECT key, value FROM run_annotations
                              WHERE run_id = %i
            """ % (self.run_id))

        self._annotations = dict(iter(cursor.fetchone, None))


    def GetAnnotations(self):

        return self._annotations


    def _SetupResultCursors(self):
    
        # Set up our two result cursors.
        self.connection.execute("""
            DECLARE results_c CURSOR FOR
                SELECT result_id, kind, outcome FROM results
                                                WHERE run_id = %i
                ORDER BY result_id, kind
            """ % (self.run_id,))
        self.connection.execute("""
            DECLARE annote_c CURSOR FOR
                SELECT result_id, result_kind, key, value
                FROM result_annotations WHERE run_id = %i
                ORDER BY result_id, result_kind
            """ % (self.run_id,))

        def get_more_results(num):
            return self.connection.execute("""
                       FETCH FORWARD %i FROM results_c
                   """ % (num,)).fetchall()
        def get_more_annotations(num):
            return self.connection.execute("""
                       FETCH FORWARD %i FROM annote_c
                   """ % (num,)).fetchall()

        self._r_buffer = _Buffer(self._batch_size, get_more_results)
        self._a_buffer = _Buffer(self._batch_size, get_more_annotations)
        

    def GetResult(self):

        try:
            id, kind, outcome = self._r_buffer.next()
        except StopIteration:
            return None
        annotations = {}
        for result_id, result_kind, key, value in self._a_buffer:
            if (result_id, result_kind) != (id, kind):
                self._a_buffer.rewind()
                break
            annotations[key] = value
        return Result(kind, id, outcome, annotations)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

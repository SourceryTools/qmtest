########################################################################
#
# File:   pickle_result_stream.py
# Author: Mark Mitchell
# Date:   11/25/2002
#
# Contents:
#   PickleResultStream
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import cPickle
import qm.fields
from   qm.test.file_result_stream import FileResultStream

########################################################################
# Classes
########################################################################

class PickleResultStream(FileResultStream):
    """A 'PickleResultStream' writes out results as Python pickles."""

    _max_pinned_results = 1000
    """A limit on how many `Result's to pin in memory at once.

    Pickling an object normally pins it in memory; this is necessary
    to ensure correct behaviour when pickling multiple references to
    the same object.  We know that `Result's can't refer to each
    other, so this pinning is useless overhead; however, clearing the
    cache at every call to `WriteResult' slows down both pickling and
    unpickling by about a factor of two.  As a solution, any given
    `PickleResultStream', will clear its cache after
    `_max_pinned_results' calls to WriteResult.  This cache-clearing
    technique causes a very minor slowdown on small result streams,
    and a substantial speedup on large result streams."""


    arguments = [
        qm.fields.IntegerField(
            name = "protocol_version",
            description = """The pickle protocol version to use.

            There are multiple versions of the pickle protocol; in
            general, higher numbers correspond to faster operation and
            more compact files, but may produce files that cannot be
            understood by older versions of Python.

            As of 2003-06-20, the defined protocol versions are:
               0: Traditional ASCII-only format.
               1: Traditional binary format.
               2: New binary format.
              -1: Equivalent to the highest version supported by your
                  Python release.
            Pickle versions 0 and 1 can be understood by any version
            of Python; version 2 pickles can only be created or
            understood by Python 2.3 and newer.  (See PEP 307 for
            details.)

            Currently the default version is 1.

            """,
            default_value = 1,
        ),
    ]

    def __init__(self, arguments):

        # Initialize the base class.
        super(PickleResultStream, self).__init__(arguments)
        # Create a pickler.
        self.__pickler = cPickle.Pickler(self.file, self.protocol_version)
        # We haven't processed any `Result's yet.
        self.__processed = 0


    def WriteResult(self, result):

        self.__pickler.dump(result)
        self.__processed += 1
        # If enough results have been pickeled, clear the pickling
        # cache.
        if not self.__processed % self._max_pinned_results:
            self.__pickler.clear_memo()

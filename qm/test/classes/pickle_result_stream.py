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
from   qm.test.result_stream import ResultStream

########################################################################
# Classes
########################################################################

class PickleResultStream(ResultStream):
    """A 'PickleResultStream' writes out results as Python pickles."""

    def __init__(self, file):
        """Construct a 'PickleResultStream'.

        'file' -- The file object to which the results should be
        written.  Closing the file remains the responsibility of the
        caller."""

        # Initialize the base class.
        ResultStream.__init__(self, {})
        # Create a pickler.
        self.__pickler = cPickle.Pickler(file, 1)


    def WriteResult(self, result):

        self.__pickler.dump(result)
        

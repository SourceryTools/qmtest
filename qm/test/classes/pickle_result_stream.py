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
from   qm.test.file_result_stream import FileResultStream

########################################################################
# Classes
########################################################################

class PickleResultStream(FileResultStream):
    """A 'PickleResultStream' writes out results as Python pickles."""

    def __init__(self, arguments):

        # Initialize the base class.
        FileResultStream.__init__(self, arguments)
        # Create a pickler.
        self.__pickler = cPickle.Pickler(self.file, 1)


    def WriteResult(self, result):

        self.__pickler.dump(result)
        

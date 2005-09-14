########################################################################
#
# File:   reader_test_run.py
# Author: Mark Mitchell
# Date:   2005-08-08
#
# Contents:
#   QMTest ReaderTestRun class.
#
# Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.test.result import Result
from qm.test.test_run import TestRun
from qm.test.result_reader import ResultReader

########################################################################
# Classes
########################################################################

class ReaderTestRun(TestRun):
    """A 'ReaderTestRun' reads its results using a 'ResultReader'.

    A 'ResultReader' provides an iterative interface for reading
    results.  A 'ReaderTestRun' uses a 'ResultReader' to populate a
    dictionary storing all the results from the reader."""

    def __init__(self, reader):
        """Create a new 'ReaderTestRun'

        'reader' -- The 'ResultReader' from which we are to read
        results."""

        # Read the results.
        self.__results = {}
        for kind in Result.kinds:
            self.__results[kind] = {}
        for result in reader:
            self.__results[result.GetKind()][result.GetId()] = result

        # Read the annotations.
        self.__annotations = reader.GetAnnotations()


    def GetResult(self, id, kind = Result.TEST):

        return self.__results[kind].get(id)


    def GetAnnotation(self, key):

        return self.__annotations.get(key)
        

    def GetAllResults(self, directory = "", kind = Result.TEST):

        if directory == "":
            return self.__results[kind].values()
        else:
            return [self.__results[kind][id] for id in self.__results[kind]
                    if id.startswith(directory)]

    


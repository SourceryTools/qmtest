########################################################################
#
# File:   pickle_result_source.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   PickleResultSource
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import cPickle
from qm.test.file_result_source import FileResultSource

########################################################################
# Classes
########################################################################

class PickleResultSource(FileResultSource):
    """A 'PickleResultSource' reads in results from pickle files.

    See also 'PickleResultStream', which does the reverse."""

    def __init__(self, arguments):

        super(PickleResultSource, self).__init__(arguments)
        self.__unpickler = cPickle.Unpickler(self.file)


    def GetResult(self):

        try:
            return self.__unpickler.load()
        except EOFError:
            return None
        except cPickle.UnpicklingError:
            # This is raised at EOF if file is a StringIO.
            return None

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

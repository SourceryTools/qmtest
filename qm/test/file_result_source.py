########################################################################
#
# File:   file_result_source.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   FileResultSource
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
from qm.test.result_source import ResultSource
import sys

########################################################################
# Classes
########################################################################

class FileResultSource(ResultSource):
    """A 'FileResultSource' gets its input from a file.

    A 'FileResultSource' is an abstract base class for other result
    source classes that read results from a single file.  The file
    from which results should be read can be specified using either
    the 'filename' argument or the 'file' argument.  The latter is for
    use by QMTest internally."""


    arguments = [
        qm.fields.TextField(
            name = "filename",
            title = "File Name",
            description = """The name of the file.

            All results will be read from the file indicated.  If no
            filename is specified, or the filename specified is "-",
            the standard input will be used.""",
            verbatim = "true",
            default_value = ""),
        qm.fields.PythonField(
            name = "file"),
    ]

    _is_binary_file = 0
    """If true, the file written is a binary file.

    This flag can be overridden by derived classes."""
    
    def __init__(self, arguments):

        super(FileResultSource, self).__init__(arguments)

        if not self.file:
            if self.filename and self.filename != "-":
                if self._is_binary_file:
                    mode = "rb"
                else:
                    mode = "r"
                self.file = open(self.filename, mode, 0)
            else:
                self.file = sys.stdin


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

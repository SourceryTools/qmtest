########################################################################
#
# File:   file_result_stream.py
# Author: Mark Mitchell
# Date:   04/13/2003
#
# Contents:
#   FileResultStream
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.common
import qm.fields
from   qm.test.result_stream import ResultStream
import sys

########################################################################
# Classes
########################################################################

class FileResultStream(ResultStream):
    """A 'FileResultStream' writes its output to a file.

    A 'FileResultStream' is an abstract base class for other result
    stream classes that store results in a single file.  The file to
    which results should be written can be specified using either the
    'filename' argument or the 'file' argument.  The latter is for use
    by QMTest internally."""

    arguments = [
        qm.fields.TextField(
            name = "filename",
            title = "File Name",
            description = """The name of the file.

            All results will be written to the file indicated.  If no
            filename is specified, or the filename specified is "-",
            the standard output will be used.""",
            verbatim = "true",
            default_value = ""),
        qm.fields.PythonField(
            name = "file"),
    ]

    _is_binary_file = 0
    """If true, the file written is a binary file.

    This flag can be overridden by derived classes."""
    
    def __init__(self, arguments):

        ResultStream.__init__(self, arguments)

        if not self.file:
            if self.filename and self.filename != "-":
                # Open the file in unbuffered mode so that results will be
                # written out immediately.
                if self._is_binary_file:
                    mode = "wb"
                else:
                    mode = "w"
                self.file = open(self.filename, mode, 0)
                # Child processes do not need to write to the results
                # file.
                qm.common.close_file_on_exec(self.file)
            else:
                self.file = sys.stdout
            

        

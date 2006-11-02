########################################################################
#
# File:   file_result_reader.py
# Author: Nathaniel Smith
# Date:   2003-06-23
#
# Contents:
#   FileResultReader
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from qm.fields import TextField, PythonField
from qm.common import QMException
from qm.test.result_reader import ResultReader
import sys

########################################################################
# Classes
########################################################################

class FileResultReader(ResultReader):
    """A 'FileResultReader' gets its input from a file.

    A 'FileResultReader' is an abstract base class for other result
    reader classes that read results from a single file.  The file
    from which results should be read can be specified using either
    the 'filename' argument or the 'file' argument.  The latter is for
    use by QMTest internally."""

    class InvalidFile(QMException):
        """An 'InvalidFile' exception indicates an incorrect file format.

        If the constructor for a 'FileResultStream' detects an invalid
        file, it must raise an instance of this exception."""

        pass

        
    
    arguments = [
        TextField(
            name = "filename",
            title = "File Name",
            description = """The name of the file.

            All results will be read from the file indicated.  If no
            filename is specified, or the filename specified is "-",
            the standard input will be used.""",
            verbatim = "true",
            default_value = ""),
        PythonField(
            name = "file"),
    ]

    _is_binary_file = 0
    """If true, results are stored in a binary format.

    This flag can be overridden by derived classes."""
    
    def __init__(self, arguments = None, **args):
        """Construct a new 'FileResultReader'.

        'arguments' -- As for 'ResultReader'.

        If the file provided is not in the input format expected by this
        result reader, the derived class '__init__' function must raise
        an 'InvalidStream' exception."""

        super(FileResultReader, self).__init__(arguments, **args)

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

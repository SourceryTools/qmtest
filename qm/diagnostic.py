########################################################################
#
# File:   diagnostic.py
# Author: Alex Samuel
# Date:   2001-02-27
#
# Contents:
#   Code for managing and generating diagnostics.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
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

########################################################################
# imports
########################################################################

import re
import string
import types

########################################################################
# classes
########################################################################

class DiagnosticSet:

    comment_regex = re.compile("^[ \t]*#.*$", re.MULTILINE)
    separator_regex = re.compile("^@", re.MULTILINE)

    def __init__(self, path, program_name):
        self.__program_name = program_name
        self.__diagnostics = {}
        self.ReadFile(path)


    def ReadFile(self, path):
        file = open(path, "r")
        contents = file.read()
        contents = self.comment_regex.sub("", contents)
        entries = self.separator_regex.split(contents)
                
        for entry in entries:
            if not "\n" in entry:
                continue
            tag, message = string.split(entry, "\n", 1)
            tag = string.strip(tag)
            message = string.strip(message)
            # Store it.
            self.__diagnostics[tag] = message


    def Generate(self, tag, severity="error", output=None, **substitutions):
        
        message = self.__diagnostics[tag] % substitutions
        if output is None:
            pass
        else:
            output.write("%s: %s: %s\n"
                         % (self.__program_name, severity, message)) 
        return message



########################################################################
# functions
########################################################################

# Place function definitions here.

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

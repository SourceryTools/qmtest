########################################################################
#
# File:   diagnostic.py
# Author: Alex Samuel
# Date:   2001-02-27
#
# Contents:
#   Code for managing and generating diagnostics.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
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

"""Table-based diagnostic message generation.

Diagnostics are loaded from text files.  These files are laid out
according to special rules:

  - Lines beginning with a hash mark are ignored.

  - Each diagnostic begins with a line that contains an at sign (@) and
    a tag used to identify the diagnostic.

  - Subsequent text until the start of the next diagnostic is
    the diagnostic template.

  - Diagnostic templates may contain named-substition tokens as
    used by the Python % operator on a string.

  - Diagnostic messages are interpreted as structured text.

For example:

    # This line is a comment

    @ my first diagnostic
    The command you entered, '$(command)s', is bogus.  Please try again.

    @ my second diagnostic
    The value you specified, '$(value)d', is completely bogus.  Don't
    even bother trying again.

"""

########################################################################
# imports
########################################################################

import common
import os
import qm
import re
import string
import types

########################################################################
# classes
########################################################################

class DiagnosticSet:

    # Regular expression to match comment lines.
    __comment_regex = re.compile("^[ \t]*#.*$", re.MULTILINE)

    # Regular express that matches the start of a new diagnostic entry. 
    __separator_regex = re.compile("^@", re.MULTILINE)


    def __init__(self):
        """Initialize a new set of diagnostics."""

        self.__diagnostics = {}


    def ReadFromFile(self, path):
        """Load diagnostics from a file.

        'path' -- Path to the file containing diagnostics."""

        # Read the file.
        file = open(path, "r")
        contents = file.read()
        file.close()
        # Erase comment lines.
        contents = self.__comment_regex.sub("", contents)
        # Split the file's contents into entries.
        entries = self.__separator_regex.split(contents)
                
        for entry in entries:
            if not "\n" in entry:
                continue
            # The tag is everything up to the first newline.
            tag, message = string.split(entry, "\n", 1)
            # Clean up the tag and the diagnostic message.
            tag = string.strip(tag)
            message = string.strip(message)
            # Store it.
            self.__diagnostics[tag] = message


    def Generate(self, tag, severity="error", output=None, **substitutions):
        """Generate a diagnostic message.

        'tag' -- The tag of the diagnostic to generate.

        'severity' -- A string representing the severity of the
        diagnostic, for instance "warning" or "error".

        'output' -- If not 'None', the a file object to which the
        a full diagnostic is written.

        'substitutions' -- Named values for substitution into the
        diagnostic message.

        returns -- The bare diagnostic message."""
        
        substitutions = substitutions.copy()
        substitutions["program_name"] = common.program_name
        message = self.__diagnostics[tag] % substitutions
        if output is None:
            pass
        else:
            output.write("%s: %s: %s\n"
                         % (common.program_name, severity, message)) 
        return message



########################################################################
# functions
########################################################################

def message(tag, **substitutions):
    """Generate a diagnostic message."""

    global diagnostic_set
    return apply(diagnostic_set.Generate,
                 (tag, "message", None),
                 substitutions)


def error(tag, output=None, **substitutions):
    """Generate or emit an error diagnostic."""

    global diagnostic_set
    return apply(diagnostic_set.Generate,
                 (tag, "error", output, ),
                 substitutions)

    
def warning(tag, output=None, **substitutions):
    """Generate or emit a warning diagnostic."""

    global diagnostic_set
    return apply(diagnostic_set.Generate,
                 (tag, "warning", output, ),
                 substitutions)


def load_messages(tool):
    """Read messages that apply to 'tool'.

    'tool' -- A string giving the name of a QM tool."""

    # Load diagnostics.
    if os.environ['QM_BUILD'] == '1':
        diagnostic_file \
            = qm.get_share_directory("..", "qm", tool, "share",
                                     "messages", "diagnostics.txt")
    else:
        diagnostic_file \
          = qm.get_share_directory("messages", tool, "diagnostics.txt")
    diagnostic_set.ReadFromFile(diagnostic_file)
    # Load help messages.
    if os.environ['QM_BUILD'] == '1':
        diagnostic_file \
            = qm.get_share_directory("..", "qm", tool, "share",
                                     "messages", "help.txt")
    else:
        diagnostic_file \
            = qm.get_share_directory("messages", tool, "help.txt")
    help_set.ReadFromFile(diagnostic_file)
    
    
########################################################################
# variables
########################################################################

diagnostic_set = DiagnosticSet()
"""The 'DiagnosticSet' object from which diagnostics are generated."""

help_set = DiagnosticSet()
"""The 'DiagnosticSet'object from which help text messages are
generated."""

########################################################################
# initialization
########################################################################

def __initialize_module():
    # Load common diagnostics.
    diagnostic_file = qm.get_share_directory("diagnostics", "common.txt")
    diagnostic_set.ReadFromFile(diagnostic_file)

    # Load common help messages.
    help_file = qm.get_share_directory("diagnostics", "common-help.txt")
    help_set.ReadFromFile(help_file)


__initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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
# For license terms see the file COPYING.
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
# Variables
########################################################################

__diagnostic_set = None
"""The 'DiagnosticSet' object from which diagnostics are generated."""

__help_set = None
"""The 'DiagnosticSet'object from which help text messages are
generated."""

########################################################################
# functions
########################################################################

def get_diagnostic_set():
    """Return the 'DiagnosticSet' containing warning/error messages.

    returns -- The 'DiagnosticSet' containing warning/error messages."""

    global __diagnostic_set
    if __diagnostic_set is None:
        __diagnostic_set = DiagnosticSet()
        __diagnostic_set.ReadFromFile(qm.get_share_directory("diagnostics",
                                                             "common.txt"))

    return __diagnostic_set


def get_help_set():
    """Return the 'DiagnosticSet' for help messages.

    returns -- The 'DiagnosticSet' containing help messages."""

    global __help_set
    if __help_set is None:
        __help_set = DiagnosticSet()
        __help_set.ReadFromFile(qm.get_share_directory("diagnostics",
                                                       "common-help.txt"))

    return __help_set

    
def message(tag, **substitutions):
    """Generate a diagnostic message."""

    return apply(get_diagnostic_set().Generate,
                 (tag, "message", None),
                 substitutions)


def error(tag, output=None, **substitutions):
    """Generate or emit an error diagnostic."""

    return apply(get_diagnostic_set().Generate,
                 (tag, "error", output, ),
                 substitutions)

    
def warning(tag, output=None, **substitutions):
    """Generate or emit a warning diagnostic."""

    return apply(get_diagnostic_set().Generate,
                 (tag, "warning", output, ),
                 substitutions)


def load_messages(tool):
    """Read messages that apply to 'tool'.

    'tool' -- A string giving the name of a QM tool."""

    # Load diagnostics.
    diagnostic_file = qm.get_share_directory('messages', 'diagnostics.txt')
    get_diagnostic_set().ReadFromFile(diagnostic_file)
    # Load help messages.
    diagnostic_file = qm.get_share_directory('messages', 'help.txt')
    get_help_set().ReadFromFile(diagnostic_file)
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

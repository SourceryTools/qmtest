########################################################################
#
# File:   python_label.py
# Author: Mark Mitchell
# Date:   06/11/2002
#
# Contents:
#   PythonLabel
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   qm.label   import *
import re

########################################################################
# Classes
########################################################################

class PythonLabel(Label):
    """A 'PythonLabel' is a 'Label' that uses the 'a.b.c' naming scheme.

    A 'PythonLabel' is a 'Label' whose separator character is the period
    and whose components consist of lower-case letters, numerals, and
    underscores.  These labels have the property that they can be easily
    mapped to filenames on most operating systems; all valid labels are
    valid filenames (replacing '.' with '/') and two different labels
    will always map to two different filenames."""

    sep = '.'
    """The separator character used to separate components."""

    __valid_label_regexp = re.compile("[-a-z0-9_%s]+$" % sep)
    """A compiled regular expression that matches valid labels."""
    
    def IsValid(self, label, is_component):
        """Returns true if this label is not valid.

        returns -- True if this label is not valid."""

        if not Label.IsValid(self, label, is_component):
            # If the label does not meet the basic validity
            # requirements, reject it.
            return 0
        elif not self.__valid_label_regexp.match(label):
            # If the label contains invalid characters, reject it.
            return 0

        return 1



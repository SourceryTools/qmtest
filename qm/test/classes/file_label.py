########################################################################
#
# File:   file_label.py
# Author: Mark Mitchell
# Date:   06/11/2002
#
# Contents:
#   FileLabel
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   __future__ import nested_scopes
from   qm.label   import *
import os
import re

########################################################################
# Classes
########################################################################

class FileLabel(Label):
    """A 'FileLabel' is a 'Label' that uses the filesystem's naming scheme.

    A 'FileLabel' is a 'Label' whose separator character is the
    operating system's file system separator character (typically '/' or
    '\\').  These labels are not system-independent; there is no
    guarantee that 'FileLabel's will have the same meaning on different
    operating systems."""

    sep = os.sep

    def Join(self, *labels):
        """Combine this label and the 'labels' into a single label.

        'labels' -- A sequence of strings giving the components of the
        new label.  All but the last are taken as directory names; the
        last is treated as a basename."""

        return self.__class__(apply(os.path.join, (self._label,) + labels))
    
        
    def Split(self):
        """Split the label into a pair '(directory, basename)'.

        returns -- A pair '(directory, basename)', each of which is
        a label.

        It is always true that 'directory.join(basename)' will return a
        label equivalent to the original label."""

        return os.path.split(self._label)


    def Components(self):
        """Split the label into its components.

        returns -- A sequence of labels, each corresponding to a
        component of this label."""

        return map(self.__class__, self._label.split(self.sep))

                   
    def Basename(self):
        """Return the basename for the label.

        returns -- A string giving the basename for the label.  The
        value returned for 'l.basename()' is always the same as
        'l.split()[1]'."""

        return os.path.basename(self._label)
    
    
    def Dirname(self):
        """Return the directory name for the 'label'.

        returns -- A string giving the directory name for the 'label'.
        The value returned for 'l.dirname()' is always the same as
        'l.split()[0]'."""

        return os.path.dirname(self._label)

########################################################################
#
# File:   label.py
# Author: Alex Samuel
# Date:   2001-03-17
#
# Contents:
#   Label
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

from   __future__ import nested_scopes
import os
import re
import string
import types

########################################################################
# Classes
########################################################################

class Label:
    """A 'Label' identifies an entity.

    A 'Label' is a generalization of a filename.  Like filenames, labels
    consist of one or more directories followed by a basename.  However,
    the format used for a label need not be the same as that used by
    filenames.

    Each label class defines a separator character to take the place of
    the '/' character used by many file systems.
    
    All labels are relative labels; no label may begin with a separator
    character."""

    def __init__(self, label):
        """Construct a new 'Label'.

        'label' -- A string giving the value of the label."""

        assert type(label) in (types.StringType, types.UnicodeType)
        self._label = label
        

    def Join(self, *labels):
        """Combine this label and the 'labels' into a single label.

        'labels' -- A sequence of strings giving the components of the
        new label.  All but the last are taken as directory names; the
        last is treated as a basename."""

        result = self._label
        for l in labels:
            if not result:
                # If the label is empty so far, l is the first component.
                result = l
            elif result and result[-1] == self.sep:
                # If the label thus far ends with a separator, we do not
                # want to add another one.
                result += l
            else:
                result = result + self.sep + l

        return self.__class__(result)
    
        
    def Split(self):
        """Split the label into a pair '(directory, basename)'.

        returns -- A pair '(directory, basename)', each of which is
        a label.

        It is always true that 'directory.join(basename)' will return a
        label equivalent to the original label."""

        last_sep = self._label.rfind(self.sep)
        if last_sep != -1:
            return (self.__class__(self._label[:last_sep]),
                    self.__class__(self._label[last_sep + 1:]))
        else:
            return (self.__class__(""),
                    self.__class__(self._label))


    def SplitLeft(self):
        """Split the label into a pair '(parent, subpath)'.  This is
        the same operation as Split, except the split occurs at the
        leftmost separator, not the rightmost.

        returns -- A pair '(directory, basename)', each of which is
        a label.

        It is always true that 'directory.join(basename)' will return a
        label equivalent to the original label."""

        first_sep = self._label.find(self.sep)
        if first_sep != -1:
            return (self.__class__(self._label[:first_sep]),
                    self.__class__(self._label[first_sep + 1:]))
        else:
            return (self.__class__(self._label),
                    self.__class__(""))


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

        return self.Split()[1]
    
    
    def Dirname(self):
        """Return the directory name for the 'label'.

        returns -- A string giving the directory name for the 'label'.
        The value returned for 'l.dirname()' is always the same as
        'l.split()[0]'."""

        return self.Split()[0]


    def ToPath(self, extension = ""):
        """Return a filesystem path corresponding to this label.

        'extension' -- A string which is added to each of the components
        but the last.  For example, if 'extension' is '.ext', and
        'Components' returns '('a', 'b', 'c')', the path returned will
        be 'a.ext/b.ext/c' if '/' is the separator character.
        
        returns -- A string giving a relative path in the filesystem
        corresponding to this label."""

        components = self.Components()
        if components:
            components = (map(lambda l: str(l) + extension,
                              components[:-1]) 
                          + [str(components[-1])])
            
        return apply(os.path.join, components)
        

    def IsValid(self, label, is_component):
        """Returns true if 'label' is not valid.

        'label' -- The string being tested for validity.
        
        'is_component' -- True if the string being tested is just a
        single component of a label path.
        
        returns -- True if 'label' is not valid."""

        if label and label[0] == self.sep:
            # All labels are relative; a valid label cannot begin with a
            # separator.
            return 0
        elif is_component and self.sep in label:
            # A component label cannot contain a separator.
            return 0
        elif label.find(self.sep + self.sep) != -1:
            # It is invalid to have two separators in a row.
            return 0
            
        return 1


    def __str__(self):
        """Return the string form of this label."""

        return self._label
    
########################################################################
# Functions
########################################################################

__thunk_regex = re.compile("[^a-z0-9_]")

def thunk(label):
    """Sanitize and convert 'label' to a valid label.

    Makes a best-effort attempt to keep 'label' recognizable during
    the conversion.

    returns -- A valid label."""

    # Strip leading and trailing whitespace.
    label = string.strip(label)
    # Lower capital letters.
    label = string.lower(label)
    # Replace all invalid characters with underscores.
    label = string.replace(label, "+", "x")
    label = __thunk_regex.sub("_", label)
    # Trim leading underscores.
    while len(label) > 0 and label[0] == "_":
        label = label[1:]
    # Make sure the label isn't empty.
    if label == "":
        raise ValueError, "Empty label"
    return label

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

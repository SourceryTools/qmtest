########################################################################
#
# File:   label.py
# Author: Alex Samuel
# Date:   2001-03-17
#
# Contents:
#   Functions for manipulating lowest-common-demoniator labels.
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

"""A "label" is an operating-system independent path name.

A label names entities in the same way that file names name files, but
in an operating-system independent way.  For example, while the
separator character on some systems is '/', and on other systems is
'\', it is always '.' in QM.  It is easy to convert labels to real
file names when necessary.

QM does not always map labels on to file names.  For example,
labels are used to name tests in a QMTest test database, but the
database is free to store the tests however it likes.  It could,
for example, store them all in a single file.

Labels are strings that follow the following rules:

  - A label consists of one or more characters chosen from [a-z0-9_.].

  - Labels that begin with an underscore are considered reserved for
    internal use.  While they are valid labels, users are not allowed
    to create entities with these names.

The '.' is treated as the separator character.  A label that begins
with a '.' is called an "absolute label"; one that does not is a
"relative label"."""

########################################################################
# imports
########################################################################

import os
import re
import string

########################################################################
# constants
########################################################################

sep = "."
"""The namespace separator character in labels."""

root = sep
"""The root label."""

########################################################################
# classes
########################################################################

class AsAbsolute:
    """An 'AsAbsolute' turns relative labels into absolute labels.

    An 'AsAbsolute' stores a directory.  When applied to a label, the
    directory and the label are 'join'ed."""
        
    def __init__(self, directory):
        """Construct a new 'AsAbsolute'.

        'directory' -- A label indicating a directory.  Labels provided
        to the '__call__' method will be treated as relative to
        'directory'."""

        self.__directory = directory


    def __call__(self, label):
        """Return an absolute label for 'label'.

        'label' -- A relative label.

        returns -- An absolute label, constructed by 'join'ing the
        'directory' used to construct the 'AsAbsolute' with 'label'."""

        return join(self.__directory, label)



class AsRelative:
    """An 'AsRelative' transforms absolute labels into relative labels.

    An 'AsAbsolute' stores a directory.  When applied to a label, the
    portion of the label that is relative to the directory is
    returned."""

    def __init__(self, directory):
        """Construct a new 'AsRelative'.

        'directory' -- A label naming a directory."""
        
        self.__directory = directory


    def __call__(self, label):
        """Return a relative label for 'label'.

        'label' -- An absolute label, whose prefix is the 'directory'.
        used to to construct the 'AsRelative'.
        
        returns -- A relative label.  Applying 'join' to the 'directory'
        and the returned value will yield the original 'label'.

        raises -- 'ValueError' if the 'directory' is nott a prefix of
        'label'."""

        path_len = len(self.__directory)
        if path_len == 0:
            return label
        if len(label) < path_len + 1 \
           or label[:path_len] != self.__directory:
            raise ValueError, \
                  "path %s is not a prefix of label %s" \
                  % (self.__directory, label)
        return label[:path_len + 1]


########################################################################
# functions
########################################################################

__label_regex = re.compile("[a-z0-9_]+$")
__label_regex_with_sep = re.compile("[a-z0-9_%s]+$" % sep)

def is_valid(label, user=1, allow_separator=0):
    """Test whether 'label' is a valid label.

    'label' -- The string to validate.

    'user' -- If true, labels reserved for internal use are also
    rejected.  Labels beginning with an underscore are reserved for
    internal use.

    'allow_separator' -- If true, allow a period in the label, as a path
    separator. 

    returns -- True if 'label' is valid."""

    # A label must have at least one character.
    if len(label) == 0:
        return 0
    # Choose the appropriate regular expression.
    if allow_separator:
        regex = __label_regex_with_sep
    else:
        regex = __label_regex
    # Try to match.
    if not regex.match(label):
        return 0
    # The regex doesn't match empty strings, so this indexing is OK.
    if user and label[0] == '_':
        return 0
    return 1


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
    return normpath(label)


def split(label):
    """Divide a label at the last separator character.

    returns -- A pair '(namespace, name)', where 'name' is the name of
    the label in its containing 'namespace'.  If the separator character
    does not appear in 'label', 'namespace' is "." and 'name' is the
    same as 'label'."""
    
    label = normpath(label)
    if label == sep:
        return (sep, "")
    elif sep in label:
        last_sep = string.rfind(label, sep)
        return (label[:last_sep], label[last_sep + 1:])
    else:
        return (sep, label)


def split_fully(label):
    """Divide a label into components at separator characters.

    returns -- A sequence of path components.  If 'label' is the root
    label, the return value is an empty sequence."""

    label = normpath(label)
    if label == sep:
        return []
    return string.split(label, sep)


def basename(label):
    """Return the last component of 'label'."""

    return split(label)[1]


def dirname(label):
    """Return 'label' without its last component."""

    result = split(label)[0]
    if result == "":
        result = sep
    return result


__multiple_separators_regex = re.compile("%s+" % re.escape(sep))

def normpath(label):
    """Normalize separators in 'label'."""

    # Remove leading and trailing separators.
    while len(label) > 0 and label[0] == sep:
        label = label[1:]
    while len(label) > 0 and label[-1] == sep:
        label = label[:-1]
    # Anything left?
    if label == "":
        return sep
    else:
        # Replace multiple separators with a single one.
        return __multiple_separators_regex.sub(sep, label)


def join(*components):
    """Join components with the separator character."""

    # Join the results.
    return normpath(string.join(components, sep))


def to_path(label, extension=""):
    """Return a path corresponding to 'label'.

    'label' -- A label.

    'extension' -- If extension is non-empty, it will be added to
    every directory name in the path returned.

    returns -- A path (without a leading separator) corresponding
    to 'label'.  The path returned is always relative; it will never
    begin with the operating system path separator character.

    For example, if 'extension' is '".ext"', the file name returned
    for the label '"a.b.c"' will be '"a.ext/b.ext/c"', assuming that
    '/' is the operating system path separator."""

    # 'normpath' returns a label that begins with 'sep' only in one
    # case: if 'label' corresponds to the root label.  In this case, we
    # should return a null path string, not the file system path
    # separator, so handle this case specially.
    if label == sep:
        return ""
    else:
        return string.replace(label, sep, extension + os.sep)


def from_path(path):
    """Return a label corresponding to a file system 'path'.

    Leading path separators are ignored, so you can't distinguish from
    the label whether the path was absolute or relative."""

    label = string.replace(path, os.sep, sep)
    return normpath(label)


def is_prefix(path, path_prefix):
    """Return true if 'path_prefix' is a path prefix of 'path'."""

    path_prefix = normpath(path_prefix)
    if path_prefix == sep:
        # This is the top-level path, and therefore considered a prefix
        # to any path.
        return 1
    else:
        length = len(path_prefix)
        return length <= len(path) and path[:length] == path_prefix
    

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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

"""A "label" is standard tag for identifying entities.

The intent of using labels is to provide a lowest-common-denominator
text implementation that can be used throughout QM as a persistent,
user-visible naming scheme for entities.  By placing strong
restrinctions on the format of the label, we improve the likelihood that
it'll be easy to create staightforward, one-to-one mappings from labels
onto other name spaces (such as file system paths on various platforms,
URLs, or typographical namespaces consistent with the naming constraints
of various systems).

Labels are restricted by these rules:

  - A label consists of one or more characters chosen from lower-case
    English letters (a-z), digits (0-9), and underscores.

  - Labels that begin with an underscore are considered reserved for
    internal use.  While they are valid labels, they should be
    disallowed for user-specified labels.

  - Optionally, labels may be placed in a typographical namespace by
    using a period (.) as the namespace separator character.  There is
    no notion of absolute or relative paths in the namespace, nor is
    their a notation for representing the parent namespace (analogous to
    .. in filenames).

"""

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

########################################################################
# classes
########################################################################

class MakeRelativeTo:
    """Callable to process relative labels."""

    def __init__(self, path):
        """Construct a new instance.

        'path' -- Labels are made relative to this path.  For instance,
        if 'path' is "foo.bar", the label "baz" would be transformed to
        "foo.bar.baz"."""

        self.__path = path


    def __call__(self, label):
        """Return 'label' interpreted as a relative label."""

        return join(self.__path, label)



class UnmakeRelativeTo:
    """Callable to undo 'MakeRelativeTo'."""

    def __init__(self, path):
        """Construct a new instance.

        'path' -- Labels must be relative to this path, and the path
        prefix is removed.  For instance, if 'path' is "foo.bar", the
        label "foo.bar.baz" would be transformed to "baz"."""

        self.__path = path


    def __call__(self, label):
        """Return 'label' interpreted as a relative label.

        raises -- 'ValueError' if the path specified in the initializer
        function isn't a prefix of 'label'."""

        path_len = len(self.__path)
        if path_len == 0:
            return label
        if len(label) < path_len + 1 \
           or label[:path_len] != self.__path:
            raise ValueError, \
                  "path %s is not a prefix of label %s" \
                  % (self.__path, label)
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
    # Make sure the label isn't empty.  If it is, concoct something.
    if label == "":
        raise ValueError, "Empty label"
    return label


def split(label):
    """Divide a label at the last separator character.

    returns -- A pair '(namespace, name)', where 'name' is the name of
    the label in its containing 'namespace'.  If the separator character
    does not appear in 'label', 'namespace' is an empty string and
    'name' is the same as 'label'."""
    
    if sep in label:
        last_sep = string.rfind(label, sep)
        return (label[:last_sep], label[last_sep + 1:])
    else:
        return ("", label)


def basename(label):
    """Return the last component of 'label'."""

    return split(label)[1]


def dirname(label):
    """Return 'label' without its last component."""

    result = split(label)[0]
    if result == "":
        result = "."
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


def to_path(label):
    """Return a relative file system path corresponding to 'label'."""

    label = normpath(label)
    if label == sep:
        return ""
    else:
        return string.replace(label, sep, os.sep)


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

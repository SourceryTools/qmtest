########################################################################
#
# File:   common.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   General-purpose classes and functions.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
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

import cPickle
import os
import os.path
import re
import socket
import string
import time
import traceback
import types

########################################################################
# exceptions
########################################################################

class MethodShouldBeOverriddenError(Exception):
    """Indicates a method was called that should have been overridden."""

    pass



class MutexLockError(Exception):
    """Indicates that a file exists that wasn't expected to."""

    pass



class ConfigurationError(RuntimeError):

    pass



class UserError(Exception):

    pass



########################################################################
# classes
########################################################################

class FileSystemMutex:
    """A mutual exclusion lock residing in the file system."""

    retry_interval = 0.1
    """The interval, in seconds, at which to retry a lock."""


    def __init__(self, path):
        "Create a new mutex at 'path'.  No lock is aquired."""

        self.__path = path
        self.__pid_filename = os.path.join(path, "pid")

        # Perform sanity check.  If 'path' exists, it should be a
        # lock held by another instance of this class.
        if os.path.exists(self.__path):
            if not os.path.isdir(self.__path):
                raise RuntimeError, "path exists and isn't a directory"

        self.__locked = 0


    def GetPath(self):
        """Return the path of the lock."""

        return self.__path


    def Lock(self, timeout=None):
        """Aquire a lock.  If the mutex is already held, block.

        'timeout' -- If 'None', the lock operation blocks
        indefinitely, until the mutex is available.  If not 'None',
        this is a timeout, in seconds, after which to give up.  If
        zero, this function returns immediately if a lock cannot be
        acquired.

        raises - 'MutexLockError' if a lock was not acquired."""

        # Don't allow double locks.
        if self.__locked:
            return

        start_time = time.time()
        while 1:
            parent_dir = os.path.dirname(self.__path)
            # Make sure the parent directory exists.
            if not os.path.isdir(parent_dir):
                raise MutexLockError, \
                      "parent directory %s doesn't exist" % parent_dir
            # Check if the directory exists.
            if not os.path.isdir(self.__path):
                # If not, attempt to create it.
                try:
                    os.mkdir(self.__path)
                    # Creation succeeded; the lock is ours.
                    self.__locked = 1
                    # Write our pid into a file in the directory.
                    pid_file = open(self.__pid_filename, "w")
                    pid_file.write("%d\n" % os.getpid())
                    pid_file.close()
                    return
                except os.error:
                    # Couldn't lock.
                    pass
            # Time out yet?
            if timeout != None \
               and (time.time() - start_time) >= timeout:
                # Timed out.  Raise an exception.
                raise MutexLockError, \
                      "lock on %s timed out" % self.__path
            # Sleep for a while before trying again.
            time.sleep(self.retry_interval)

        
    def Unlock(self):
        """Release a lock."""

        # Don't try to unlock if we're not already locked.
        if not self.__locked:
            return

        # Sanity checks.
        assert os.path.isdir(self.__path)
        assert os.path.isfile(self.__pid_filename)

        # Unlock.
        os.unlink(self.__pid_filename)
        os.rmdir(self.__path)
        self.__locked = 0


    def IsLocked(self):
        """Return true if a lock is held on the mutex."""

        return self.__locked
        
        

class Configuration:
    """A persistent set of program configuration variables.

    A 'Configuration' object acts as a map of configuration variables.
    The configuration is associated with a file path.  It can be made
    persistent by invoking 'Save', which writes it to that file."""

    def __init__(self, path, **initialization):
        """Create or load a configuration.

        'path' -- The path to the configuration file.

        'initialization' -- Initial configuration values."""

        self.__path = path
        self.__fields = {}
        # Initialize the fields using our '__setitem__' method.
        for key, value in initialization.items():
            self[key] = value


    def Save(self):
        """Save the configuration."""
        
        # Write the configuration to a pickle.
        pickle_file = open(self.__path, "w")
        cPickle.dump(self.__fields, pickle_file)
        pickle_file.close()


    def Load(self):
        """Load the configuration.

        raise -- 'ConfigurationError' if the configuration cannot be
        loaded."""

        # Unpickle the configuration.
        pickle_file = open(self.__path, "r")
        self.__fields = cPickle.load(pickle_file)
        pickle_file.close()


    def __getitem__(self, key):
        return self.__fields[key]


    def __setitem__(self, key, value):
        self.__fields[key] = value


    def __delitem__(self, key):
        del self.__fields[key]



class MapReplacer:
    """A callable object to replace text according to a map."""

    def __init__(self, replacements):
        """Generate a function to replace text according to a map.

        'replacements' -- A mapping of replacements.  For each element,
        the key is the text to match, and the corresponding value is the
        replacements for that text."""

        # Construct a regular expression that matches any of the
        # replacements.
        keys = map(re.escape, replacements.keys())
        regex = "(" + string.join(keys, "|") + ")"
        self.__regex = re.compile(regex)
        # The replacement function.  It simply looks up the replacement text
        # in 'replacements'.
        self.__substitution = lambda match, replacements=replacements: \
                              replacements[match.group(0)]


    def __call__(self, text):
        """Perform replacements in 'text'.

        returns -- The replaced text."""

        return self.__regex.sub(self.__substitution, text)



########################################################################
# functions
########################################################################

base_directory = None

def get_base_directory():
    """Return the absolute path to the top QM Python directory."""

    assert base_directory is not None
    return base_directory


__label_regex = re.compile("[a-z0-9_]+$")

def is_valid_label(label, user=1):
    """Test whether 'label' is a valid label.

    A valid label is a string consisting of lower-case letters,
    digits, and underscores.

    'label' -- The string to validate.

    'user' -- If true, labels reserved for internal use are also
    rejected.  Labels beginning with an underscore are reserved for
    internal use.

    returns -- True if 'label' is valid."""

    if not __label_regex.match(label):
        return 0
    # The regex doesn't match empty strings, so this indexing is OK.
    if user and label[0] == '_':
        return 0
    return 1


__label_thunk_regex = re.compile("[^a-z0-9_]")

def thunk_to_label(label):
    """Sanitize and convert 'label' to a valid label.

    Makes a best-effort attempt to keep 'label' recognizable during
    the conversion.

    returns -- A valid label."""

    # Strip leading and trailing whitespace.
    label = string.strip(label)
    # Lower capital letters.
    label = string.lower(label)
    # Replace all invalid characters with underscores.
    label = __label_thunk_regex.sub("_", label)
    # Trim leading underscores.
    while len(label) > 0 and label[0] == "_":
        label = label[1:]
    # Make sure the label isn't empty.
    if label == "":
        label = "x"
    return label


__host_name = None

def get_host_name():
    """Return the name of this computer."""

    global __host_name

    # FIXME:  Should we try the 'hostname' command here?

    # Figure out the host name the first time this function is called.
    if __host_name is None:
        # First try to look up our own address in DNS.
        try:
            name = socket.gethostbyname_ex(socket.gethostname())[0]
        except socket.error:
            name = None
        # That didn't work.  Just use the local name.
        if name is None:
            try:
                name = socket.gethostname()
            except socket.error:
                pass
        # That didn't work either.  Check if the host name is stored in
        # the environment.
        if name is None:
            try:
                name = os.environ["HOSTNAME"]
            except KeyError:
                pass
        # We're stumped.  Use localhost.
        if name is None:
            name = "localhost"
        # Store the name for next time.
        __host_name = name

    return __host_name


def format_exception(exc_info):
    """Format an exception as structured text.

    'exc_info' -- A three-element tuple containing exception info, of
    the form '(type, value, traceback)'.

    returns -- A string containing a the formatted exception."""

    # FIXME.  We can do better by looking into the traceback ourselves. 

    # Break up the exection info tuple.
    type, value, trace = exc_info
    # Format the traceback, with a newline separating elements.
    traceback_listing = traceback.format_tb(trace)
    traceback_listing = string.join(traceback_listing)
    # Generate output.
    return "Exception '%s : %s'\n%s\n" % (type, value, traceback_listing)


def format_byte_count(bytes):
    """Return the traditional representation of 'bytes' bytes."""

    kb = 1024.0
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024
    
    for name, order in [
        ("TB", 1024.0 ** 4),
        ("GB", 1024.0 ** 3),
        ("MB", 1024.0 ** 2),
        ("KB", 1024.0 ** 1),
        ]:
        if bytes >= order:
            return "%.1f %s" % (bytes / order, name)

    return "%d bytes" % bytes


def remove_directory_recursively(path):
    """Remove the directory at 'path' and everything under it."""

    assert os.path.isdir(path)
    # FIXME: Make this portable, or provide a Windows implementation.
    os.system('rm -rf "%s"' % path)


def replace_by_map(text, replacements):
    """Perform multiple replacements.

    'text' -- The text in which to make the replacements.

    'replacements' -- A mapping of replacements.  For each element, the
    key is the text to match, and the corresponding value is the
    replacements for that text.

    returns -- The replaced text."""

    return MapReplacer(replacements)(text)


def invert_map(m):
    """Return the inverse of 'm'.

    'm' -- A map object.

    returns -- A map of values of 'm' to corresponding keys.  If a value
    of 'm' is associated with more than one key, it is mapped to one of
    these keys in the result, but which one is undefined."""

    result = {}
    for key, value in m.items():
        result[value] = key
    return result


def convert_from_dos_text(text):
    """Replace CRLF with LF in 'text'."""

    return string.replace(text, "\n\r", "\n")


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

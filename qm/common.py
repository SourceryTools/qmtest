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

import os
import os.path
import re
import string
import time

########################################################################
# exceptions
########################################################################

class MethodShouldBeOverriddenError(Exception):
    """Indicates a method was called that should have been overridden."""

    pass



class MutexLockError(Exception):
    """Indicates that a file exists that wasn't expected to."""

    pass



########################################################################
# classes
########################################################################

class FileSystemMutex:
    """A mutual exclusion lock residing in the file system."""

    retry_interval = 0.1
    """The interval, in seconds, at which to retry a lock."""

    class MutexLockError(Exception):
        """Indicates that a lock could not be acquired."""

        pass


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
            # First check if the directory exists.
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
                raise self.MutexLockError, "lock timed out"
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
        
        

########################################################################
# functions
########################################################################

label_regex = re.compile("[a-z0-9_]+$")

def is_valid_label(label, user=1):
    """Test whether 'label' is a valid label.

    A valid label is a string consisting of lower-case letters,
    digits, and underscores.

    'label' -- The string to validate.

    'user' -- If true, labels reserved for internal use are also
    rejected.  Labels beginning with an underscore are reserved for
    internal use.

    returns -- True if 'label' is valid."""

    if not label_regex.match(label):
        return 0
    # The regex doesn't match empty strings, so this indexing is OK.
    if user and label[0] == '_':
        return 0
    return 1


label_thunk_regex = re.compile("[^a-z0-9_]")

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
    label = label_thunk_regex.sub("_", label)
    # Trim leading underscores.
    while len(label) > 0 and label[0] == "_":
        label = label[1:]
    # Make sure the label isn't empty.
    if label == "":
        label = "x"
    return label
        

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

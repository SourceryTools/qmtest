########################################################################
#
# File:   context.py
# Author: Mark Mitchell
# Date:   11/06/2001
#
# Contents:
#   QMTest Context class
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.common
import re
import sys
import types

########################################################################
# Classes
########################################################################

class ContextException(qm.common.QMException):
    """A 'ContextException' indicates a missing context variable."""

    def __init__(self, key):
        """Construct a new 'ContextException'.

        'key' -- A string giving the context key for which no value
        was available."""

        qm.common.QMException.__init__(self, "Missing context variable.")
        self.key = key

        
    
class Context(types.DictType):
    """Test-time and local configuration for tests.

    A 'Context' object contains all of the information a test needs to
    execute, beyond what is stored as part of the test specification
    itself.  Information in the context can include,

      * Local (per-user, etc.) configuration, such as where to find the
        tested program.

      * Environmental information, such as which machine the test is
        running on.

      * One-time configuration, including test arguments specified on
        the command line.

    A 'Context' object is effectively a mapping object whose keys must
    be labels and values must be strings."""

    TMPDIR_CONTEXT_PROPERTY = "qmtest.tmpdir"
    """A context property whose value is a string giving the path to a
    temporary directory.  This directory will be used only by the
    'Runnable' in whose context this property occurs during the
    execution of that 'Runnable'. No other object will use the same
    temporary directory at the same time.  There is no guarantee that
    the temporary directory is empty, however; it may contain files
    left behind by the execution of other 'Runnable' objects."""

    def __init__(self, context = None):
        """Construct a new context.

        'context' -- If not 'None', the existing 'Context' being
        wrapped by this new context.
        
        'initial_properties' -- Initial key/value pairs to include in
        the context."""

        super(Context, self).__init__()

        self.__context = context
        
        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            value = qm.rc.Get(option, None)
            assert value is not None
            self[option] = value


    def GetTemporaryDirectory(self):
        """Return the path to the a temporary directory.

        returns -- The path to the a temporary directory.  The
        'Runnable' object may make free use of this temporary
        directory; no other 'Runnable's will use the same directory at
        the same time."""
        
        return self[self.TMPDIR_CONTEXT_PROPERTY]

    
    def Read(self, file_name):
        """Read the context file 'file_name'.

        'file_name' -- The name of the context file.

        Reads the context file and adds the context properties in the
        file to 'self'."""

        if file_name == "-":
            # Read from standard input.
            file = sys.stdin
        else:
            # Read from a named file.
            try:
                file = open(file_name, "r")
            except:
                raise qm.cmdline.CommandError, \
                      qm.error("could not read file", path=file_name)
        # Read the assignments.
        assignments = qm.common.read_assignments(file)
        # Add them to the context.
        for (name, value) in assignments.items():
            try:
                # Insert it into the context.
                self[name] = value
            except ValueError, msg:
                # The format of the context key is invalid, but
                # raise a 'CommandError' instead.
                raise qm.cmdline.CommandError, msg

    
    # Methods to simulate a map object.

    def __contains__(self, key):

        if super(Context, self).__contains__(key):
            return 1

        if self.__context is not None:
            return self.__context.__contains__(key)

        return 0
        

    def get(self, key, default = None):

        if key in self:
            return self[key]

        return default
    

    def has_key(self, key):

        return key in self

    
    def __getitem__(self, key):
        try:
            return super(Context, self).__getitem__(key)
        except KeyError:
            if self.__context is None:
                raise ContextException(key)
            try:
                return self.__context[key]
            except KeyError:
                raise ContextException(key)


    # Helper methods.

    def GetAddedProperties(self):
        """Return the properties added to this context by resources.

        returns -- A map from strings to values indicating properties
        that were added to this context by resources."""

        if self.__context is None:
            return {}
        
        added = self.__context.GetAddedProperties()
        added.update(self)
        return added


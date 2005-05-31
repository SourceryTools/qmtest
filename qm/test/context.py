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
    """A 'ContextException' indicates an invalid context variable."""

    def __init__(self, key, msg = "missing context variable"):
        """Construct a new 'ContextException'.

        'key' -- A string giving the context key for which no valid
        value was available.

        'msg' -- A diagnostic identifier explaining the problem.  The
        message string may contain a fill-in for the key."""

        msg = qm.error(msg, key = key)
        qm.common.QMException.__init__(self, msg)
        self.key = key

        
    
class ContextWrapper:
    """Do-nothing class to preserve pickle compatability.

    A class called 'ContextWrapper' used to be used in instead of a
    'Context' class in some cases, and we used to put contexts into
    'Result's.  Because of how pickles work, this means that the only way
    to unpickle these old 'Result's is to have a do-nothing placeholder
    class that can be instantiated and then thrown away."""

    pass



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
    
    TARGET_CONTEXT_PROPERTY = "qmtest.target"
    """The context variable giving the name of the current target."""

    DB_PATH_CONTEXT_PROPERTY = "qmtest.dbpath"
    """The context variable giving the path to the database.

    The value of this context variable will be a string giving the
    path to the database directory.  For example, if QMTest is invoked
    as 'qmtest -D /path/to/db run', the value of this variable would
    be '/path/to/db'.  The value may be an absolute or a relative
    path."""

    ID_CONTEXT_PROPERTY = "qmtest.id"
    """The context variable giving the name of the running test or resource.

    This value of this context variable will be the string giving the
    name of the of the test or resource that is presently executing."""
    
    TMPDIR_CONTEXT_PROPERTY = "qmtest.tmpdir"
    """A context property whose value is a string giving the path to a
    temporary directory.  This directory will be used only by the
    'Runnable' in whose context this property occurs during the
    execution of that 'Runnable'. No other object will use the same
    temporary directory at the same time.  There is no guarantee that
    the temporary directory is empty, however; it may contain files
    left behind by the execution of other 'Runnable' objects."""

    __safe_for_unpickling__ = 1
    """Required to unpickle new-style classes under Python 2.2."""

    def __init__(self, context = None):
        """Construct a new context.

        'context' -- If not 'None', the existing 'Context' being
        wrapped by this new context."""

        super(Context, self).__init__()

        self.__context = context
        
        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            value = qm.rc.Get(option, None)
            assert value is not None
            self[option] = value


    def GetBoolean(self, key, default = None):
        """Return the boolean value associated with 'key'.

        'key' -- A string.

        'default' -- A default boolean value.

        returns -- The value associated with 'key' in the context,
        interpreted as a boolean.

        If there is no value associated with 'key' and default is not
        'None', then the boolean value associated with default is
        used.  If there is no value associated with 'key' and default
        is 'None', an exception is raised.

        The value associated with 'key' must be a string.  If not, an
        exception is raised.  If the value is a string, but does not
        correspond to a boolean value, an exception is raised."""

        valstr = self.get(key)
        if valstr is None:
            if default is None:
                raise ContextException(key)
            else:
                return default

        try:
            return qm.common.parse_boolean(valstr)
        except ValueError:
            raise ContextException(key, "invalid boolean context var")
        

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


    def items(self):

        if self.__context is None:
            return super(Context, self).items()
        else:
            # Have to be careful, because self.__context and self may
            # contain different values for the same keys, and the values
            # defined in self should override the values defined in
            # self.__context.
            unified_dict = dict(self.__context.items())
            unified_dict.update(self)
            return unified_dict.items()


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



########################################################################
#
# File:   context.py
# Author: Mark Mitchell
# Date:   11/06/2001
#
# Contents:
#   QMTest Context class
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm
import qm.common
import re
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

        self.key = key

        
    
class Context:
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

    def __init__(self, **initial_properties):
        """Construct a new context.

        'initial_properties' -- Initial key/value pairs to include in
        the context."""

        self.__properties = initial_properties
        for key, value in self.__properties.items():
            self.ValidateKey(key)

        # Stuff everything in the RC configuration into the context.
        options = qm.rc.GetOptions()
        for option in options:
            self.ValidateKey(option)
            value = qm.rc.Get(option, None)
            assert value is not None
            self.__properties[option] = value

        self.__temporaries = {}


    # Methods to simulate a map object.

    def __getitem__(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            raise ContextException(key)


    def __setitem__(self, key, value):
        self.ValidateKey(key)
        self.__properties[key] = value


    def __delitem__(self, key):
        del self.__properties[key]


    def has_key(self, key):
        return self.__properties.has_key(key)


    def keys(self):
        return self.__properties.keys()


    def values(self):
        return self.__properties.values()


    def items(self):
        return self.__properties.items()


    def get(self, key, default=None):
        """Get the value associated with 'key'.

        key -- A key.

        default -- The value to return if there is no value associated
        with 'key'.
        
        returns -- The value associated with 'key', or 'default' if
        there is no such value."""

        if self.has_key(key):
            return self[key]
        else:
            return default
        
    
    def copy(self):
        # No need to re-validate.
        result = Context()
        result.__properties = self.__properties.copy()
        return result


    # Helper methods.

    def ValidateKey(self, key):
        """Validate 'key'.

        raises -- 'ValueError' if 'key' is not a string.

        raises -- 'RuntimeError' if 'key' is not valid."""

        if not isinstance(key, types.StringType):
            raise ValueError, "context key must be a string"
        if not re.match("[-A-Za-z0-9_.]+", key):
            raise ValueError, \
                  qm.error("invalid context key", key=key)



class ContextWrapper:
    """Wrapper for 'Context' objects.

    A 'ContextWrapper' allows additional properties to be added
    temporarily to a context.  It also keeps new properties added to the
    context separate from those that were specified when the context
    wrapper was intialized.

    There are three sets of properties in a context wrapper.

      1. Properties of the wrapped 'Context' object.

      2. Extra properties specified when the wrapper was created.

      3. Properties added (using '__setitem__') after the wrapper was
         created.

    A property in 3 shadows a property with the same name in 1 or 2,
    and a property in 2 similarly shadows a property with the same name
    in 1."""

    def __init__(self, context, extra_properties={}):
        """Create a context wrapper.

        'context' -- The wrapped 'Context' object.

        'extra_properties' -- Additional properties."""

        self.__context = context
        self.__extra = extra_properties.copy()
        self.__added = {}


    def GetAddedProperties(self):
        """Return the properties added after this wrapper was created."""

        return self.__added


    def __getitem__(self, key):
        """Return a property value."""

        # Check added properties first.
        try:
            return self.__added[key]
        except KeyError:
            pass
        # Then check properties added during initialization.
        try:
            return self.__extra[key]
        except KeyError:
            pass
        # Finally check properties of the wrapped context object.
        return self.__context[key]


    def __setitem__(self, key, value):
        """Set a property value."""

        self.__context.ValidateKey(key)
        # All properties set via '__setitem__' are stored here.
        self.__added[key] = value


    def __delitem__(self, key):
        try:
            del self.__added[key]
        except KeyError:
            # A property cannot be deleted unless it was set with
            # '__setitem__'.
            if self.__extra.has_key(key) or self.__context.has_key(key):
                raise RuntimeError, \
                      qm.error("context property cannot be deleted",
                               property=key)
            else:
                # The property didn't exist at all.
                raise
           

    def has_key(self, key):
        return self.__added.has_key(key) \
               or self.__extra.has_key(key) \
               or self.__context.has_key(key)


    def keys(self):
        return self.__added.keys() \
               + self.__extra.keys() \
               + self.__context.keys()


    def values(self):
        values = []
        for key in self.keys():
            values.append(self.getitem(key))
        return values


    def items(self):
        items = []
        for key in self.keys():
            items.append((key, self[key], ))
        return items


    def get(self, key, default=None):
        """Get the value associated with 'key'.

        key -- A key.

        default -- The value to return if there is no value associated
        with 'key'.
        
        returns -- The value associated with 'key', or 'default' if
        there is no such value."""

        if self.has_key(key):
            return self[key]
        else:
            return default


    def copy(self):
        result = ContextWrapper(self.__context, self.__extra)
        result.__added = self.__added.copy()
        return result


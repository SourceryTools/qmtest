########################################################################
#
# File:   extension.py
# Author: Mark Mitchell
# Date:   07/31/2002
#
# Contents:
#   Extension
#
# Copyright (c) 2002 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import qm

########################################################################
# Classes
########################################################################

class Extension:
    """A class derived from 'Extension' is a QM extension.

    A variety of different classes are derived from 'Extension'.  All
    of these classes can be derived from by users to produce
    customized QM extensions.

    'Extension' is an abstract class."""

    arguments = [
        ]
    """A list of the arguments to the extension class.

    Each element of this list should be an instance of 'Field'.  The
    'Field' instance describes the argument.

    Derived classes may redefine this class variable.  However,
    derived classes should not explicitly include the arguments from
    base classes; QMTest will automatically combine all the arguments
    found throughout the class hierarchy."""

    def __init__(self, arguments):
        """Construct a new 'Extension'.

        'arguments' -- A dictionary mapping argument names (as
        specified in the 'arguments' class variable) to values.  The
        keys are strings; the values should be appropriate for the
        corresponding fields.  The values are converted to values via
        the 'Field.ParseFormValue' method.

        This method will place all of the arguments into this objects
        instance dictionary.
        
        Derived classes may override this method, but should call this
        method during their processing."""

        # Make sure that no arguments have been provided that do not
        # apply to this extension class.
        class_arguments = get_class_arguments_as_dictionary(self.__class__)
        for name in arguments.keys():
            if not class_arguments.has_key(name):
                raise qm.QMException, \
                      qm.error("unexpected extension argument",
                               name = name,
                               class_name = self.__class__.__name__)

        # If an argument was not specified, give it an appropriate
        # default value.
        for ca in class_arguments.values():
            name = ca.GetName()
            if not arguments.has_key(name):
                arguments[name] = ca.GetDefaultValue()
            
        self.__dict__.update(arguments)
        
########################################################################
# Functions
########################################################################

def get_class_arguments(extension_class):
    """Return the arguments associated with 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.
    
    returns -- A list of 'Field' objects containing all of the
    arguments in the class hierarchy."""

    assert issubclass(extension_class, Extension)
    
    arguments = []

    # Start with the most derived class.
    classes = [extension_class]
    while classes:
        # Pull the first class off the list.
        c = classes.pop(0)
        # Add all of the new base classes to the end of the list.
        classes.extend(c.__bases__)
        # Add the arguments from this class.
        arguments.extend(c.__dict__.get("arguments", []))

    return arguments
        

def get_class_arguments_as_dictionary(extension_class):
    """Return the arguments associated with 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.

    returns -- A dictionary mapping argument names to 'Field'
    objects.  The dictionary contains all of the arguments in the
    class hierarchy."""

    arguments = get_class_arguments(extension_class)
    dictionary = {}
    for argument in arguments:
        dictionary[argument.GetName()] = argument
    return dictionary
        

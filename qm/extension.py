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
import xml

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

    kind = None
    """A string giving kind of extension is implemented by the class.

    This field is used in an application-specific way; for example,
    QMTest has 'test' and 'target' extension classes."""
    
    _argument_list = None
    """A list of all the 'Field's in this class.

    This list combines the complete list of 'arguments'.  'Field's
    appear in the order reached by a pre-order breadth-first traversal
    of the hierarchy, starting from the most derived class."""
    
    _argument_dictionary = None
    """A map from argument names to 'Field' instances.

    A map from the names of arguments for this class to the
    corresponding 'Field'."""
    
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

        # Make sure that all the arguments actually correspond to
        # 'Field's for this class.
        if __debug__:
            dictionary = get_class_arguments_as_dictionary(self.__class__)
            for a, v in arguments.items():
                assert dictionary.has_key(a)
        
        # Remember the arguments provided.
        self.__dict__.update(arguments)


    def __getattr__(self, name):

        # Perhaps a default value for a class argument should be used.
        field = get_class_arguments_as_dictionary(self.__class__).get(name)
        if field is None:
            raise AttributeError, name
        return field.GetDefaultValue()
                
########################################################################
# Functions
########################################################################

def get_class_arguments(extension_class):
    """Return the arguments associated with 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.
    
    returns -- A list of 'Field' objects containing all of the
    arguments in the class hierarchy."""

    assert issubclass(extension_class, Extension)

    arguments = extension_class._argument_list
    if arguments is None:
        # There are no arguments yet.
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
        extension_class._argument_list = arguments
        
    return arguments
        

def get_class_arguments_as_dictionary(extension_class):
    """Return the arguments associated with 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.

    returns -- A dictionary mapping argument names to 'Field'
    objects.  The dictionary contains all of the arguments in the
    class hierarchy."""

    assert issubclass(extension_class, Extension)

    dictionary = extension_class._argument_dictionary
    if dictionary is None:
        arguments = get_class_arguments(extension_class)
        dictionary = {}
        for argument in arguments:
            dictionary[argument.GetName()] = argument
        extension_class._argument_dictionary = dictionary
        
    return dictionary
        

def get_class_description(extension_class, brief=0):
    """Return a brief description of the extension class 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.
    
    'brief' -- If true, return a brief (one-line) description of the
    extension class.
    
    returns -- A structured text description of 'extension_class'."""

    assert issubclass(extension_class, Extension)

    # Extract the class's doc string.
    doc_string = extension_class.__doc__
    if doc_string is not None:
        if brief:
            doc_string = qm.structured_text.get_first(doc_string)
        return doc_string
    else:
        return "&nbsp;"
    

def get_extension_class_name(extension_class):
    """Return the name of 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.
    
    returns -- The name of 'extension_class'.  This is the name that
    is used when users refer to the class."""

    assert issubclass(extension_class, Extension)

    return extension_class.__module__ + "." + extension_class.__name__
    
    
def validate_arguments(extension_class, arguments):
    """Validate the 'arguments' to the 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.

    'arguments' -- A dictionary mapping argument names (strings) to
    values (strings).

    returns -- A dictionary mapping 'Field's to values.
    
    Check that each of the 'arguments' is a valid argument to
    'extension_class'.  If so, the argumets are converted as required
    by the 'Field', and the dictionary returned contains the converted
    values.  Otherwise, an exception is raised."""

    assert issubclass(extension_class, Extension)

    # We have not converted any arguments yet.
    converted_arguments = {}
    
    # Check that there are no arguments that do not apply to this
    # class.
    class_arguments = get_class_arguments_as_dictionary(extension_class)
    for name, value in arguments.items():
        field = class_arguments.get(name)
        if not field:
            raise qm.QMException, \
                  qm.error("unexpected extension argument",
                           name = name,
                           class_name \
                               = get_extension_class_name(extension_class))
        if field.IsComputed():
            raise qm.QMException, \
                  qm.error("value provided for computed field",
                           name = name,
                           class_name \
                               = get_extension_class_name(extension_class))
        converted_arguments[name] = field.ParseTextValue(value)

    return converted_arguments


def make_dom_element(extension_class, arguments, document, element = None):
    """Create a DOM node for an instance of 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.

    'arguments' -- The arguments to the extension class.

    'document' -- The DOM document that will contain the new
    element.

    'element' -- If not 'None' the extension element to which items
    will be added.  Otherwise, a new element will be created by this
    function.

    returns -- A new DOM element corresponding to an instance of the
    extension class.  The caller is responsible for attaching it to
    the 'document'."""

    # Get the dictionary of 'Field's for this extension class.
    field_dictionary = get_class_arguments_as_dictionary(extension_class)

    # Create the element.
    if element:
        extension_element = element
    else:
        extension_element = document.createElement("extension")
    # Create an attribute describing the kind of extension.
    extension_element.setAttribute("kind", extension_class.kind)
    # Create an ttribute naming the extension class.
    extension_element.setAttribute("class",
                                   get_extension_class_name(extension_class))
    # Create an element for each of the arguments.
    for argument_name, value in arguments.items():
        # Skip computed arguments.
        field = field_dictionary[argument_name]
        if field.IsComputed():
            continue
        # Create a node for the argument.
        argument_element = document.createElement("argument")
        # Store the name of the field.
        argument_element.setAttribute("name", argument_name)
        # Store the value.
        argument_element.appendChild(field.MakeDomNodeForValue(value,
                                                               document))
        # Add the attribute node to the target.
        extension_element.appendChild(argument_element)

    return extension_element


def make_dom_document(extension_class, arguments):
    """Create a DOM document for an instance of 'extension_class'.

    'extension_class' -- A class derived from 'Extension'.

    'arguments' -- The arguments to the extension class.

    returns -- A new DOM document corresponding to an instance of the
    extension class."""

    document = qm.xmlutil.create_dom_document(
            public_id=qm.test.base.dtds["extension"],
            dtd_file_name="extension",
            document_element_tag="extension"
            )
    make_dom_element(extension_class, arguments, document,
                     document.documentElement)
    return document
    
        

def parse_dom_element(element, class_loader):
    """Parse a DOM node representing an instance of 'Extension'.

    'element' -- A DOM node, of the format created by
    'make_dom_element'.

    'class_loader' -- A callable.  The callable will be passed the
    name of the extension class and must return the actual class
    object.

    returns -- A pair ('extension_class', 'arguments') containing the
    extension class (a class derived from 'Extension') and the
    arguments (a dictionary mapping names to values) stored in the
    'element'."""

    # Determine the name of the extension class.
    class_name = element.getAttribute("class")
    # DOM nodes created by earlier versions of QMTest encoded the
    # class name in a separate element, so look there for backwards
    # compatbility.
    if not class_name:
        class_element = element.getElementsByTagName("class")[0]
        class_name = qm.xmlutil.get_dom_text(class_element)
    # Load it.
    extension_class = class_loader(class_name)

    # Get the dictionary of 'Field's for this extension class.
    field_dictionary = get_class_arguments_as_dictionary(extension_class)

    # Collect the arguments to the extension class.
    arguments = {}
    for argument_element in element.getElementsByTagName("argument"):
        name = argument_element.getAttribute("name")
        # Find the corresponding 'Field'.
        field = field_dictionary[name]
        # Get the DOM node for the value.  It is always a element.
        value_node \
            = filter(lambda e: e.nodeType == xml.dom.Node.ELEMENT_NODE,
                     argument_element.childNodes)[0]
        # Parse the value.
        value = field.GetValueFromDomNode(value_node, None)
        # Remember it.
        arguments[name] = value
    
    return (extension_class, arguments)

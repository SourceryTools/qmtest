########################################################################
#
# File:   issue_class.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Generic implementation of an issue class.
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

import qm
import qm.track
import time
import types

########################################################################
# constants
########################################################################

# The default categories enumeration to use for a new issue class, if
# one is not provided.

default_categories = {
    "default" : 0,
}


# The default set of states to use for a new issue class, if one is
# not provided.

default_states = {
    "active" : 0,
    "deleted" : -1
}


########################################################################
# classes
########################################################################

class IssueField:
    """Base class for issue field types."""

    def __init__(self, name):
        """Create a new (generic) field.

        'name' -- The value of the name attribute.  Must be a valid
        label."""

        if not qm.is_valid_label(name):
            raise ValueError, "%s is not a valid field name" % name

        self.__attributes = { "name" : name }


    def GetName(self):
        """Return the name of the field."""

        return self.GetAttribute("name")


    def SetDefaultValue(self, value):
        """Make 'value' the default value for this field."""

        # Validate the default value.
        value = self.Validate(value)
        self.default_value = value


    def UnsetDefaultValue(self):
        """Remove the default value for this field, if any.

        If a field has no default value, its value must be specified
        for every issue created with that field."""

        if hasattr(self, "default_value"):
            del self.default_value


    def HasDefaultValue(self):
        """Return true if this field has a default value."""

        return hasattr(self, "default_value")


    def GetDefaultValue(self):
        """Return the default value for this field."""

        return self.default_value


    def GetAttribute(self, attribute_name, default_value=""):
        """Return the value of an attribute.

        Return the value of the attribute named by 'attribute_name'.
        If that attribute is not set, return 'default_value'."""

        if self.__attributes.has_key(attribute_name):
            return self.__attributes[attribute_name]
        else:
            return default_value


    def SetAttribute(self, attribute_name, value):
        """Set the value of an attribute."""

        self.__attributes[attribute_name] = value


    def UnsetAttribute(self, attribute_name):
        """Remove an attribute.

        If there is no attribute named 'attribute_name', does nothing."""

        if self.__attributes.has_key(attribute_name):
            del self.__attributes[attribute_name]


    def Validate(self, value):
        """Validate a field value.

        For an acceptable type and value, return the representation of
        'value' in the underlying field storage.

        'value' -- A value to validate for this field.

        returns -- The canonicalized representation of 'value'.

        raises -- 'TypeError' if 'value' is not a valid value for
        this field."""

        raise qm.MethodShouldBeOverriddenError, "IssueField.Validate"



class IssueFieldInteger(IssueField):

    def __init__(self, name, default_value=0):
        """Create an integer field.

        The field must be able to represent a 32-bit signed
        integer.

        'default_value' -- The default value for the field."""

        # Perform base class initialization.
        IssueField.__init__(self, name)
        # Set the default value.
        self.SetDefaultValue(default_value)


    def Validate(self, value):
        return int(value)



class IssueFieldText(IssueField):
    """A field that contains text.  

    'default_value' -- The default value for this field.

    A text field uses the following attributes:

    multiline -- If true, the field may contain line breaks, and is
    presented to the user accordingly.

    verbatim -- If true, the contents of the field are quoted as a
    block when the field is externalized; otherwise, individual
    characters are quoted as required by the externalizaton mechanism.

    big -- This is a hint that, if true, recommends to issue database
    mechanisms that the contents of the field may be large and should
    be stored out-of-line."""

    def __init__(self, name, default_value=""):
        """Create a text field."""

        # Perform base class initialization.
        IssueField.__init__(self, name)
        # Set default attribute values.
        self.SetAttribute("multiline", "false")
        self.SetAttribute("verbatim", "false")
        self.SetAttribute("big", "false")
        # Set the default field value.
        self.SetDefaultValue(default_value)


    def Validate(self, value):
        return str(value)



class IssueFieldSet(IssueField):
    """A field containing zero or more instances of some other field.

    All contents must be of the same field type.  A set field may not
    contain sets.

    The default field value is set to an empty set."""

    def __init__(self, contained):
        """Create a set field.

        The name of the contained field is taken as the name of this
        field.

        'contained' -- An 'IssueField' instance describing the
        elements of the set. 

        raises -- 'ValueError' if 'contained' is a set field.

        raises -- 'TypeError' if 'contained' is not an 'IssueField'."""

        # A set field may not contain a set field.
        if isinstance(contained, IssueFieldSet):
            raise ValueError, \
                  "A set field may not contain a set field."
        if not isinstance(contained, IssueField):
            raise TypeError, "A set must contain another field."
        # Perform base class initialization.
        IssueField.__init__(self, contained.GetName())
        # Remeber the contained field type.
        self.__contained = contained
        # Set the default field value to any empty set.
        self.SetDefaultValue([])


    def Validate(self, value):
        # Assume 'value' is a sequence.  Copy it, simultaneously
        # validating each element in the contained field.
        result = []
        for element in value:
            result.append(self.__contained.Validate(element))
        return result


    def GetContainedField(self):
        """Returns the field instance of the contents of the set."""

        return self.__contained



class IssueFieldAttachment(IssueField):
    """A field containing a file attachment."""

    def __init__(self, name):
        """Create an attachment field.

        Sets the default value of the field to 'None'."""

        # Perform base class initialization.
        IssueField.__init__(self, name)
        # Set the default value of this field.
        self.SetDefaultValue(None)


    def Validate(self, value):
        # The value should be a triplet.
        if value != None and not isinstance(value, qm.track.Attachment):
            raise TypeError, \
                  "the value of an attachment field must be an 'Attachment'"
        return value



class IssueFieldEnumeration(IssueFieldInteger):
    """A field that contains an enumeral value.

    The enumeral value is selected from an enumerated set of values.
    An enumeral field uses the following attributes:

    enumeration -- A mapping from enumeral names to enumeral values.
    Names are converted to strings, and values are stored as integers.

    ordered -- If non-zero, the enumerals are presented to the user
    ordered by value."""

    def __init__(self, name, enumeration, default_value=None):
        """Create an enumeral field.

        'enumeration' -- A mapping from names to integer values.

        'default_value' -- The default value for this enumeration.  If
        'None', the lowest-valued enumeral is used."""

        # Copy the enumeration mapping, and canonicalize it so that
        # keys are strings and values are integers.
        self.__enumeration = {}
        for key, value in enumeration.items():
            self.__enumeration[str(key)] = int(value)
        if len(self.__enumeration) == 0:
            raise ValueError, "enumeration must not be empty"
        # If 'default_value' is 'None', use the lowest-numbered enumeral.
        if default_value == None:
            default_value = min(self.__enumeration.values())
        # Perform base class initialization.
        IssueFieldInteger.__init__(self, name, default_value)
        # Store the enumeration as an attribute.
        self.SetAttribute("enumeration", repr(enumeration))


    def Validate(self, value):
        # First check whether value is an enumeration key, i.e. the
        # name of an enumeral.
        if self.__enumeration.has_key(value):
            return self.__enumeration[value]
        # Also accept a value, i.e. an integer mapped by an enumeral.
        elif value in self.__enumeration.values():
            return value
        else:
            raise ValueError, "invalid enumeration value: %s" % str(value)



class IssueFieldTime(IssueFieldText):
    """A field containing a date and time."""

    __time_format = "%Y-%m-%d %H:%M"
    """The format, ala the 'time' module, used to represent field values."""

    def __init__(self, name):
        """Create a time field.

        The field is given a default value for this field is 'None', which
        causes the current time to be used when an issue is created if no
        field value is provided."""

        # Perform base class initalization.
        IssueFieldText.__init__(self, name, default_value=None)


    def Validate(self, value):
        # Parse and reformat the time value.
        if value == None:
            return value
        else:
            time_tuple = time.strptime(value, self.__time_format)
            return time.strftime(self.__time_format, time_tuple)


    def GetDefaultValue(self):
        default_value = IssueFieldText.GetDefaultValue(self)
        if default_value == None:
            default_value = self.GetCurrentTime() 
        return default_value


    def GetCurrentTime(self):
        now = time.localtime(time.time())
        return time.strftime(self.__time_format, now)
        


class IssueFieldIid(IssueFieldText):
    """A field containing the ID of an issue."""

    # No special semantics this interface level.  IDB implementations
    # may enforce referential integrity constraints.
    pass



class IssueFieldUid(IssueFieldText):
    """A field containing a user ID."""

    # No special semantics this level.
    pass



class IssueClass:
    """Generic in-memory implementation of an issue class."""

    def __init__(self, name, categories=default_categories,
                 states=default_states):
        """Create a new issue class named 'name'.

        The issue class initially includes mandatory fields.  The iid
        and revision fields, in that order, are gauranteed to be the
        first two fields added, and as returned by 'GetFields()'."""

        self.__name = name
        self.__fields = {}

        # Create mandatory fields.
        
        # The issue id field.
        self.AddField(IssueFieldText("iid"))

        # The revision number field.
        field = IssueFieldInteger("revision")
        self.AddField(field)

        # The user id field.
        field = IssueFieldUid("user")
        self.AddField(field)

        # The revision timestamp field.
        field = IssueFieldTime("timestamp")
        self.AddField(field)

        # The summary field.
        field = IssueFieldText("summary")
        self.AddField(field)

        # The categories field.
        field = IssueFieldEnumeration("categories", categories)
        field = IssueFieldSet(field)
        self.AddField(field)

        # The parents field.
        field = IssueFieldSet(IssueFieldIid("parents"))
        self.AddField(field)

        # The children field.
        field = IssueFieldSet(IssueFieldIid("children"))
        self.AddField(field)

        # The state field.
        field = IssueFieldEnumeration("state", states)
        self.AddField(field)


    def GetName(self):
        """Return the name of this class."""

        return self.__name


    def GetFields(self):
        """Return the fields in this class.

        returns -- A sequence of fields.  Nothing is gauranteed about
        the order of the fields."""

        return self.__fields.values()


    def HasField(self, name):
        """Return true if there is a field named 'name'."""

        return self.__fields.has_key(name)


    def GetField(self, name):
        """Return the field named by 'name'.

        raises -- 'KeyError' if 'name' is not the name of a field of
        this issue class."""

        try:
            return self.__fields[name]
        except KeyError:
            raise KeyError, "%s is not a field of issue class %s" \
                  % (name, self.GetName())

        
    def AddField(self, field):
        """Add a new field to the issue class.

        'field' -- An instance of a subclass of 'IssueField' which
        describes the field to be added.  The object is copied, and
        subsequent modifications to it will not affect the issue class.

        'default_value' -- The value to assign for this field to
        existing issues of the issue class.  If 'None', there is no
        default, and each newly-created issue must assign this field.
        Otherwise, must be a valid field value."""

        name = field.GetName()
        self.__fields[name] = field


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("IssueClass %s\n" % self.GetName())
        for name, field in self.__fields.items():
            file.write("  -- %s: %s, default = %s\n"
                       % (name, field.__class__.__name__,
                          repr(self.__default_values[name])))
        file.write("\n")


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

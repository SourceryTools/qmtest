########################################################################
#
# File:   issue.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Generic implementation of issues.
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

import sys

########################################################################
# classes
########################################################################

class IssueFieldError(Exception):
    """An error involving the value of an issue field."""

    pass



class Issue:
    """Generic issue implementation."""

    def __init__(self, issue_class, iid, **field_values):
        """Create a new issue.

        'issue_class' -- The class to which this issue belongs.  An
        instance of 'IssueClass'.

        'iid' -- The ID for the new issue.

        'field_values' -- Additional values for issue fields.  The
        default value is used for any field in the issue class that is
        not included here."""

        self.__issue_class = issue_class
        self.__fields = {}

        # Initialize fields to default values, 
        for field in issue_class.GetFields():
            name = field.GetName()
            if name == "iid":
                self.__fields[name] = iid
            elif field_values.has_key(name):
                self.__fields[name] = field_values[name]
            elif field.HasDefaultValue():
                self.__fields[name] = field.GetDefaultValue()


    def Copy(self):
        """Return a duplicate of this issue."""

        # Construct a new 'Issue' instance with the same class and the
        # same field values.  The issue class itself and field values
        # should not be copied, but the field mapping should.
        return apply(Issue, (self.GetClass(), ), self.__fields)


    def GetClass(self):
        """Return the issue class of this issue."""

        return self.__issue_class


    def GetField(self, name):
        """Return the value of the field 'name'."""

        return self.__fields[name]


    def SetField(self, name, value):
        """Set the value of the field 'name' to 'value'."""

        field = self.__issue_class.GetField(name)
        self.__fields[name] = value


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("Issue, class: %s\n" % self.__issue_class.GetName())
        for name, value in self.__fields.items():
            file.write("  -- %s: %s\n" % (name, repr(value)))
        file.write("\n")


    def Validate(self):
        """Check that all field values are valid.

        returns -- A mapping indicating invalid fields.  Each key is the
        name of a field whose value is invalid.  The corresponding value
        is an exception info triple (see 'sys.exc_info') representing
        the problem.  If the mapping is empty, all fields are valid."""

        invalid_fields = {}
        # Loop over fields.
        for field in self.__issue_class.GetFields():
            field_name = field.GetName()
            # Extrace the value.
            value = self.__fields[field_name]
            # Is it valid?
            try:
                valid_value = field.Validate(value)
            except ValueError:
                # Nope; store the problem.
                invalid_fields[field_name] = sys.exc_info()
            else:
                # Yes, but replace the old value with the validated one.
                if valid_value != value:
                    self.__fields[field_name] = valid_value
        # All done.
        return invalid_fields


    def AssertValid(self):
        """Make sure all field values are valid.

        raises -- 'ValueError' if one or more fields are not valid."""

        invalid_fields = self.Validate()
        if len(invalid_fields) > 0:
            raise ValueError, invalid_fields


    # Convenience methods for dealing with mandatory fields.

    def GetId(self):
        """Return the iid."""

        return self.GetField("iid")


    def GetRevision(self):
        """Return the revision number."""

        return self.GetField("revision")


    def StampTime(self):
        """Set the timestamp to now."""

        timestamp_field = self.GetClass().GetField("timestamp")
        self.SetField("timestamp", timestamp_field.GetCurrentTime())


    def IsDeleted(self):
        """Return true if this issue has been deleted.

        An issue is considered to be deleted if its state value is
        negative."""

        return self.GetField("state") < 0




class Attachment:
    """A file attachment."""

    def __init__(self, location, mime_type, description):
        """Creates a new attachment object."""

        self.location = location
        self.mime_type = mime_type
        self.description = description


    def GetLocation(self):
        """Returns the location of the attachment data.

        The interpretation of the return value, a string, is
        context-dependent."""

        return self.location


    def GetMimeType(self):
        """Returns the MIME type of the attachment."""

        return self.mime_type


    def GetDescription(self):
        """Returns a description of the attachment."""

        return self.description



class IssueSortPredicate:
    """Predicate function to sort issues by a given field value."""

    def __init__(self, field_name, reverse=0):
        """Initialize a sort predicate.

        'field_name' -- The name of the field to sort by.

        'reverse' -- If true, sort in reverse order."""

        self.__field_name = field_name
        self.__reverse = reverse


    def __call__(self, iss1, iss2):
        """Compare two issues."""

        # Use built-in comparison on the field values.
        result = cmp(iss1.GetField(self.__field_name),
                     iss2.GetField(self.__field_name))
        # If a reverse sort was specified, flip the sense.
        if self.__reverse:
            return -result
        else:
            return result
        


########################################################################
# functions
########################################################################

def get_differing_fields(iss1, iss2):
    """Return a list of fields that differ between two issues.

    'iss1', 'iss2' -- The issues to compare.  They must be in the same
    class.

    returns -- A sequence 'IssueField' items for fields that
    differ."""

    # Make sure the issues are in the same class.
    issue_class = iss1.GetClass()
    if iss2.GetClass() != issue_class:
        raise ValueError, 'issue classes are different'
    # Loop over fields.
    differing_fields = []
    for field in issue_class.GetFields():
        field_name = field.GetName()
        # Extract the values.
        value1 = iss1.GetField(field_name)
        value2 = iss2.GetField(field_name)
        # Record this field if they're not the same.
        if not field.ValuesAreEqual(value1, value2):
            differing_fields.append(field)
    return differing_fields


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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
                self.__fields[name] = field.Validate(field_values[name])
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
        self.__fields[name] = field.Validate(value)


    def StampTime(self):
        """Set the timestamp to now."""

        timestamp_field = self.GetClass().GetField("timestamp")
        self.SetField("timestamp", timestamp_field.GetCurrentTime())


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("Issue, class: %s\n" % self.__issue_class.GetName())
        for name, value in self.__fields.items():
            file.write("  -- %s: %s\n" % (name, repr(value)))
        file.write("\n")


    # Convenience methods for returning values of mandatory fields.

    def GetId(self):
        """Return the iid."""

        return self.GetField("iid")


    def GetRevision(self):
        """Return the revision number."""

        return self.GetField("revision")



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
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

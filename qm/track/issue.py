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
        for field in issue_class.GetFields().values():
            name = field.GetName()
            if name == "iid":
                value = iid
            elif field_values.has_key(name):
                value = field.Validate(fields_values[name])
            elif field.GetDefaultValue() != None:
                value = field.GetDefaultValue()
            else:
                raise IssueFieldError, \
                      "value for field %s must be specified" % field.GetName()
            self.__fields[name] = value


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



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

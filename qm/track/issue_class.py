########################################################################
#
# File:   issue_class.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   Generic implementation of an issue class.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
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

import issue
import qm
import qm.fields
import qm.label
import string

########################################################################
# constants
########################################################################

# The default categories enumeration to use for a new issue class, if
# one is not provided.

# FIXME: These are bogus test values.  Put something better here.

default_categories = {
    "crash" : 0,
    "documentation" : 1,
    "improvement": 2,
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

class IidField(qm.fields.TextField):
    """A field containing the ID of an issue."""

    def __init__(self, name, **attributes):
        """Create an IID field.

        The field has no default value."""
        
        # Do base-class initialization, with different defaults.
        attributes["default_value"] = None
        apply(qm.fields.TextField.__init__, (self, name), attributes)


    def GetTypeDescription(self):
        return "an issue ID"


    def Validate(self, value):
        value = str(value)
        if not qm.label.is_valid(value):
            raise ValueError, \
                  qm.track.error("invalid iid", iid=value) 
        return value


    def SetDefaultValue(self, value):
        # An issue ID field never has a default value.
        pass



class IssueClass:
    """Generic in-memory implementation of an issue class."""

    def __init__(self,
                 name,
                 title=None,
                 description="",
                 categories=default_categories,
                 states=default_states):
        """Create a new issue class.

        'name' -- The name of this issue class.

        'title' -- A user-friendly name.  If 'None', the value of 'name'
        is used.

        'description' -- A description of the issue class.

        'categories' -- The enumeral to use for the "categories" field.

        'states' -- The enumeal to use for the "states" field.

        The issue class initially includes mandatory fields.  The iid
        and revision fields, in that order, are gauranteed to be the
        first two fields added, and as returned by 'GetFields()'."""

        self.__name = name
        if title is None:
            self.__title = name
        else:
            self.__title = title
        self.__description = description
        # Maintain both a list of fields and a mapping from field
        # names to fields.  The list is to preserve the order of the
        # fields; the mapping is for fast lookups by field name.
        self.__fields = []
        self.__fields_by_name = {}

        # Create mandatory fields.
        
        # The issue id field.
        field = IidField(
            name="iid",
            title="Issue ID",
            description="A label that uniquely identifies the issue.",
            initialize_only="true")
        # We do not want the iid to have a default value. It
        # always must be specified.
        field.UnsetDefaultValue()
        self.AddField(field)

        # The revision number field.
        field = qm.fields.IntegerField(
            name="revision",
            title="Revision Number",
            description="The cardinality of this revision of the issue.",
            hidden="true")
        self.AddField(field)

        # The revision timestamp field.
        field = qm.fields.TimeField(
            name="timestamp",
            title="Modification Time",
            description="The time when this revision was created.",
            read_only="true")
        self.AddField(field)

        # The user id field.
        field = qm.fields.UidField(
            name="user",
            title="Modifying User",
            description="The ID of the user who created this revision.",
            read_only="true")
        self.AddField(field)

        # The summary field.
        field = qm.fields.TextField(
            name="summary",
            title="Summary",
            description="A brief description of this issue.",
            nonempty="true")
        self.AddField(field)

        # The categories field.
        field = qm.fields.EnumerationField(
            name="categories",
            enumeration=categories,
            title="Categories",
            description="""
            The names of categories to which this issue belongs.  A
            category is a group of issues that share a similar feature,
            for instance all bugs in the particular component.
            """)
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The parents field.
        field = IidField(
            name="parents",
            title="Parents",
            description="""
            The issue ID of the issue from which this issue was split,
            or the issue IDs of the issues from which this issue was
            joined.
            """,
            hidden="true")
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The children field.
        field = IidField(
            name="children",
            title="Children",
            description="""
            The issue IDs of issues into which this issue was split, or
            the issue ID of the issue which resulted when this issue was
            joined with other issues.
            """,
            hidden="true")
        field = qm.fields.SetField(field)
        self.AddField(field)

        # The state field.
        field = qm.fields.EnumerationField(
            name="state",
            enumeration=states,
            title="State",
            description="""
            The state of this issue in the issue class's state model.
            The state reflects the status of this issue within the set of
            procedures by which an issue is normally resolved.
            """,
            default_value="active")
        self.AddField(field)


    def GetName(self):
        """Return the name of this class."""

        return self.__name


    def GetTitle(self):
        """Return the user-friendly title of this class."""

        return self.__title


    def GetDescription(self):
        """Return a description of this issue class."""

        return self.__description


    def GetFields(self):
        """Return the fields in this class.

        returns -- A sequence of fields.  The order of the fields is
        the order in which they were added to the class."""

        return self.__fields


    def HasField(self, name):
        """Return true if there is a field named 'name'."""

        return self.__fields_by_name.has_key(name)


    def GetField(self, name):
        """Return the field named by 'name'.

        raises -- 'KeyError' if 'name' is not the name of a field of
        this issue class."""

        try:
            return self.__fields_by_name[name]
        except KeyError:
            raise KeyError, \
                  qm.track.error("field not in class",
                                 field_name=name,
                                 issue_class_name=self.GetName())

        
    def AddField(self, field):
        """Add a new field to the issue class.

        'field' -- An instance of a subclass of 'Field' which describes
        the field to be added.  The object is copied, and subsequent
        modifications to it will not affect the issue class.

        'default_value' -- The value to assign for this field to
        existing issues of the issue class.  If 'None', there is no
        default, and each newly-created issue must assign this field.
        Otherwise, must be a valid field value."""

        name = field.GetName()
        self.__fields_by_name[name] = field
        self.__fields.append(field)


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("IssueClass %s\n" % self.GetName())
        for field in self.__fields:
            name = field.GetName()
            file.write("  -- %s: %s, default = %s\n"
                       % (name, field.__class__.__name__,
                          repr(self.__default_values[name])))
        file.write("\n")



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

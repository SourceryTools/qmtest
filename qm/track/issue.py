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

import config
import qm
import qm.attachment
import qm.xmlutil
import string
import sys
import xml.dom.ext.reader.Sax

########################################################################
# classes
########################################################################

class IssueFieldError(Exception):
    """An error involving the value of an issue field."""

    pass



class IssueFileError(RuntimeError):
    """An error while reading or interpreting an issue file."""

    pass



class Attachment(qm.attachment.Attachment):
    """An attachments whose data is stored in the IDB.

    This subclass of 'qm.attachment.Attachment' always uses the
    'location' attribute to refer to attachment contents in the IDB.
    The 'data' attribute is never used to carry attachment data around
    with attachment objects."""

    def __init__(self,
                 mime_type=None,
                 description="",
                 file_name="",
                 data=None,
                 location=None):
        """Create a new attachment.

        'data' -- The attachment data, or 'None' if it's already in the
        IDB.

        'location' -- The location of the data in the IDB, or 'None' if
        it isn't there yet.

        Exactly one of 'data' and 'location' should be not 'None.  If
        'data' is specified, the data is put into the database."""

        # Check semantics.
        assert data is None or location is None
        assert data is not None or location is not None

        # Perform base class initialization.
        qm.attachment.Attachment.__init__(self, mime_type,
                                          description, file_name)
        if data is not None:
            # We have the attachment data.  Put it in the IDB.
            idb = config.get_idb()
            location = idb.GetNewAttachmentLocation()
            idb.SetAttachmentData(location, data)
            self.location = location
        else:
            # Data is already in the IDB.  Reference it.
            self.location = location


    def GetData(self):
        # Obtain it from the IDB.
        return config.get_idb().GetAttachmentData(self.location)


    def GetDataSize(self):
        # Obtain it from the IDB.
        return config.get_idb().GetAttachmentSize(self.location)


    def MakeDomNode(self, document):
        # Always include the attachment's content data in-line when
        # representing it as XML.
        return qm.attachment.make_dom_node(self, document,
                                           data=self.GetData())



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


    def __repr__(self):
        return "<Issue (%s) %s #%d>" \
               % (self.GetClass().GetName(), self.GetId(), self.GetRevision())


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

        try:
            return self.__fields[name]
        except KeyError:
            # Hmm... no value for this field.  Maybe the field was added
            # subsequently.  Use the default value of this field, if it
            # has one.
            issue_class = self.GetClass()
            field = self.GetClass().GetField(name)
            if field.HasDefaultValue():
                return field.GetDefaultValue()
            else:
                # No default value; rethrow the exception.
                raise


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


    def GetFieldAsText(self, field_name):
        """Get the value of 'field_name' and format it as text."""

        value = self.GetField(field_name)
        field = self.GetClass().GetField(field_name)
        return field.FormatValueAsText(value)


    def IsDeleted(self):
        """Return true if this issue has been deleted.

        An issue is considered to be deleted if its state value is
        negative."""

        return self.GetField("state") < 0


    def MakeDomElement(self, document):
        """Generate a DOM element node for this issue.

        'document' -- The containing DOM document node."""

        issue_class = self.GetClass()
        fields = issue_class.GetFields()

        # The node is an issue element.
        element = document.createElement("issue")
        element.setAttribute("id", self.GetId())
        # Add a node containing the issue class name.
        class_element = qm.xmlutil.create_dom_text_element(
            document, "class", issue_class.GetName())
        element.appendChild(class_element)

        # Add an element for each field.
        for field in fields:
            field_name = field.GetName()
            # Skip the IID and revision fields.
            if field_name in [ "iid", "revision" ]:
                continue
            # The field value goes in a field element.
            field_element = document.createElement("field")
            field_element.setAttribute("name", field_name)

            # Get the issue's value for this field.
            value = self.GetField(field_name)
            # Is it the same as the field's default?
            if field.HasDefaultValue() \
               and value == field.GetDefaultValue() \
               and (str(value) == "" or str(value) == "[]"):
                # Yes; suppress this field for brevity.
                continue

            # Generate the field value.
            value_element = field.MakeDomNodeForValue(value, document)
            # Put the field value in the field element.
            field_element.appendChild(value_element)
            # Add the field element to the issue element.
            element.appendChild(field_element)

        return element



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

    returns -- A sequence of 'Field' items for fields that differ."""

    # Make sure the issues are in the same class.
    issue_class = iss1.GetClass()
    if iss2.GetClass() != issue_class:
        raise ValueError, 'issue classes are different'
    # Loop over fields.
    differing_fields = []
    for field in issue_class.GetFields():
        field_name = field.GetName()
        # Ignore these fields when checking for differences.
        if field_name in [ "revision", "timestamp", "user" ]:
            continue
        # Extract the values.
        value1 = iss1.GetField(field_name)
        value2 = iss2.GetField(field_name)
        # Record this field if they're not the same.
        if not field.ValuesAreEqual(value1, value2):
            differing_fields.append(field)
    return differing_fields


def load_issues_from_xml_file(file_name):
    """Load issues in XML file 'file_name'.

    returns -- A sequence of 'Issue' objects."""
    
    # Create a validating XML parser.
    reader = xml.dom.ext.reader.Sax.Reader(validate=1)
    # Open the input file.
    issue_file = open(file_name, "r")
    try:
        # Read and parse input.
        issues_document = reader.fromStream(issue_file)
    except xml.sax._exceptions.SAXParseException, exception:
        raise IssueFileError, qm.error("xml parse error",
                                       line=exception.getLineNumber(),
                                       character=exception.getColumnNumber(),
                                       file_name=file_name,
                                       message=exception._msg)
    issue_file.close()
    issues_element = issues_document.documentElement
    # Convert DOM nodes to 'Issue' instances.
    return __issues_from_dom(issues_element)


def __issues_from_dom(issues_node):
    """Convert a DOM element to issues.

    'issues_node' -- A DOM issues element node.

    returns -- A sequence of 'Issue' objects."""

    assert issues_node.tagName == "issues"

    # Extract one result for each result element.
    issues = []
    for issue_node in issues_node.getElementsByTagName("issue"):
        issue_ = __issue_from_dom(issue_node)
        issues.append(issue_)
    return issues
    

def __issue_from_dom(issue_node):
    """Convert a DOM element to an issue.

    'issue_node' -- A DOM issue element node.

    returns -- An 'Issue' instance."""

    assert issue_node.tagName == "issue"

    idb = config.get_idb()

    # Extract the issue ID.
    iid = issue_node.getAttribute("id")
    # Extract the issue class name.
    issue_class_name = qm.xmlutil.get_dom_child_text(issue_node, "class")
    try:
        # Look up the issue class.
        issue_class = idb.GetIssueClass(issue_class_name)
    except KeyError:
        # It's a class we don't know.
        raise IssueFileError, \
              qm.error("xml file unknown class", class_name=issue_class_name)

    # Extract field values.  Each is in a field element.
    field_values = {}
    for field_node in issue_node.getElementsByTagName("field"):

        # The field name is stored in an attribute.
        field_name = field_node.getAttribute("name")
        try:
            # Look up the corresponding field.
            field = issue_class.GetField(field_name)
        except KeyError:
            # There's no field by that name in the class.
            raise IssueFileError, \
                  qm.error("xml file unknown field",
                           field_name=field_name,
                           class_name=issue_class_name)

        # There should be only one node in the field element, namely the
        # value element.
        assert len(field_node.childNodes) == 1
        value_node = field_node.childNodes[0]
        # The field can convert the DOM node to a value.  Let any
        # exceptions from this method percolate up.
        value = field.GetValueFromDomNode(value_node)
        # Validate the value.  Let exceptions percolate.
        value = field.Validate(value)
        # Store the field value.
        field_values[field_name] = value

    # Construct an issue.
    return apply(Issue, [ issue_class, iid ], field_values)


def issues_to_xml(issues, output):
    """Generate an XML representation of issues.

    'issues' -- A sequence of issues.

    'output' -- A file object to which to write the XML."""

    idb = qm.track.get_idb()

    # Create a DOM document.
    document = qm.xmlutil.create_dom_document(
        public_id="-//Software Carpentry//QMTrack Issue V0.1//EN",
        dtd_file_name="issue.dtd",
        document_element_tag="issues"
        )
    # Add an issue element for each issue.
    for issue in issues:
        issue_element = issue.MakeDomElement(document)
        document.documentElement.appendChild(issue_element)
    # Generate output.
    qm.xmlutil.write_dom_document(document, output)
    

def eval_issue_expression(expression, issue, extra_locals={}):
    """Evaluate a user expression on an issue.

    The Python expression 'expression' is evlauated using a special
    variable context that makes it easy to refer to fields of an issue.
    The fields of 'issue' can be referred to as if they are local
    variables of the same name.

    'expression' -- The Python text of the expression.

    'issue' -- The issue.

    'extra_locals' -- A map from name to corresponding value for
    extra additions to the local namespace when the expression is
    evaluated. 

    returns -- The evaluated result of the expression."""

    # FIXME: Security.
    globals = { "__builtins__": allowed_builtins }
    locals = extra_locals.copy()

    issue_class = issue.GetClass()
    fields = issue_class.GetFields()
    # Add a local variable for each field.  The variable's value is the
    # value of that field in 'issue'.
    for field in fields:
        field_name = field.GetName()
        value = issue.GetField(field_name)
        locals[field_name] = value
    # Do it.
    return eval(expression, globals, locals)


def eval_revision_expression(expression,
                             revision,
                             previous_revision,
                             extra_locals={}):
    """Evaluate a user expression on a revision to an issue.

    The Python expression 'expression' is evlauated using a special
    variable context that makes it easy to refer to fields of an issue.
    The fields of 'issue' can be referred to as if they are local
    variables of the same name.  

    Some special namespace attributes that are also visible:

      '_previous' -- This object looks like a class whose attributes are
      the fields of the previous issue.

      '_changed' -- A function that takes the name of a field and
      returns true if the field's value has been changed.

      '_changed_to' -- A function that takes the name of a field and a
      value, and returns if the field's value was changed to that value
      from a different value.

      '_new' -- A true value if this is a new revision.

    A limited subset of Python built-in functions and other functions
    are available as well.

    'expression' -- The Python text of the expression.

    'revision' -- The modified issue revision.

    'previous_revision' -- A previous revision of the issue, before the
    modificaiton, or 'None' if this is a new issue.

    'extra_locals' -- A map from name to corresponding value for
    extra additions to the local namespace when the expression is
    evaluated. 

    returns -- The evaluated result of the expression."""

    issue_class = revision.GetClass()
    assert previous_revision is None \
           or issue_class is previous_revision.GetClass()
    fields = issue_class.GetFields()

    if previous_revision is not None:
        # An empty class used as an attribute container.
        class Field:
            pass
        # Construct an object with an attribute for each field; the
        # value of each attribute is the field's value in
        # 'previous_issue'.
        previous = Field()
        for field in fields:
            field_name = field.GetName()
            value = previous_revision.GetField(field_name)
            setattr(previous, field_name, value)

        # Add two additional functions.  '_changed' makes it easier to
        # ask whether the value of a particular field has changed.
        changed_fn = lambda name, rev=revision, prev=previous_revision: \
                     rev.GetField(name) != prev.GetField(name)
        # '_changed_to' also checks that the new value is as specified.
        changed_to_fn = lambda name, val, \
                        rev=revision, prev=previous_revision: \
                        rev.GetField(name) != prev.GetField(name) \
                        and rev.GetField(name) == val
    else:
        previous = None
        changed_fn = lambda name: 1
        changed_to_fn = lambda name, val: 1

    extra_locals["_previous"] = previous
    extra_locals["_changed"] = changed_fn
    extra_locals["_changed_to"] = changed_to_fn
    extra_locals["_new"] = previous_revision is None

    return eval_issue_expression(expression, revision, extra_locals)


########################################################################
# variables
########################################################################

allowed_builtins = {}
"""Builtin functions permitted for field expressions.

A map from names of builtin functions to the actual Python builtin
function objects."""

########################################################################
# initialization
########################################################################

def _initialize_module():
    qm.attachment.attachment_class = Attachment

    global allowed_builtins
    for name in [ 'None', 'abs', 'buffer', 'chr', 'cmp', 'coerce',
                  'complex', 'divmod', 'filter', 'float', 'getattr',
                  'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance',
                  'issubclass', 'len', 'list', 'long', 'map', 'max',
                  'min', 'oct', 'ord', 'pow', 'range', 'reduce', 'repr',
                  'round', 'slice', 'str', 'tuple', 'type', 'xrange' ]:
        allowed_builtins[name] = __builtins__[name]


_initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

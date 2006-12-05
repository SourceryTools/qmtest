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
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import qm
import qm.attachment
import qm.xmlutil
import string
import sys

########################################################################
# exceptions
########################################################################

class IssueFieldError(Exception):
    """An error involving the value of an issue field."""

    pass



class IssueFileError(RuntimeError):
    """An error while reading or interpreting an issue file."""

    pass



class ExpressionNameError(Exception):
    """A unknown name was referenced in an issue expression.

    The expression argument is the referenced name."""

    pass



class ExpressionSyntaxError(Exception):
    """An issue expression contained a syntax error."""

    pass



########################################################################
# classes
########################################################################

class IssueDifference:
    """A difference between two issues.

    An 'IssueDifference' stores only fields that differ between two
    issues.  The issues must be in the same class.

    Use 'difference_issues' to construct an 'IssueDifference' instance
    automatically from two issues."""

    def __init__(self, issue_class, **field_values):
        """Construct a new 'IssueDifference' object.

        'issue_class' -- The issue class.

        'field_values' -- Field name and value associations for fields
        that differ between the two issues."""

        self.__issue_class = issue_class
        self.__fields = field_values.copy()


    def GetClass(self):
        """Return the issue class of this issue difference."""

        return self.__issue_class


    def HasField(self, name):
        """Return true if this difference includes the field named 'name'."""

        return self.__fields.has_key(name)


    def GetField(self, name):
        """Return the value of the field named 'name'.

        raises -- 'KeyError' if this difference doesn't include that
        field.""" 

        return self.__fields[name]


    def SetField(self, name, value):
        """Set the value for field 'name' to 'value'."""

        self.__fields[name] = value

        
    def GetFieldNames(self):
        """Return a list of field names in this issue difference."""

        return self.__fields.keys()


    def MakeDomElement(self, document):
        """Generate a DOM element node for this issue.

        'document' -- The containing DOM document node."""

        # The node is an "issue-difference" element.
        element = document.createElement("issue-difference")

        # Add an element for each field.
        for field_name, value in self.__fields.items():
            field = self.__issue_class.GetField(field_name)
            # The field value goes in a field element.
            field_element = document.createElement("field")
            field_element.setAttribute("name", field_name)
            # Generate the field value.
            value_element = field.MakeDomNodeForValue(value, document)
            # Put the field value in the field element.
            field_element.appendChild(value_element)
            # Add the field element to the issue element.
            element.appendChild(field_element)

        return element



class Issue:
    """Generic issue implementation."""

    def __init__(self, issue_class, **field_values):
        """Create a new issue.

        'issue_class' -- The class to which this issue belongs.  An
        instance of 'IssueClass'.

        'field_values' -- Additional values for issue fields.  The
        default value is used for any field in the issue class that is
        not included here."""

        self.__issue_class = issue_class
        self.__fields = {}

        # Initialize fields to default values, 
        for field in issue_class.GetFields():
            name = field.GetName()
            if field_values.has_key(name):
                self.__fields[name] = field_values[name]
            else:
                self.__fields[name] = field.GetDefaultValue()


    def __repr__(self):
        return "<Issue (%s) %s #%d>" \
               % (self.GetClass().GetName(), self.GetId(),
                  self.GetRevisionNumber())


    def copy(self):
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
            field = issue_class.GetField(name)
            return field.GetDefaultValue()


    def SetField(self, name, value):
        """Set the value of the field 'name' to 'value'."""

        assert self.GetClass().GetField(name) is not None
        self.__fields[name] = value


    def DiagnosticPrint(self, file):
        """Print a debugging summary to 'file'."""

        file.write("Issue, class: %s\n" % self.GetClass().GetName())
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
        for field in self.GetClass().GetFields():
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


    def GetRevisionNumber(self):
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


    def IsOpen(self):
        """Return true if this issue is in an open state."""

        state_name = self.GetField("state")
        state_model = self.GetClass().GetField("state").GetStateModel()
        state = state_model.GetState(state_name)
        return state.IsOpen()


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
            if value == field.GetDefaultValue() \
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

    def __init__(self, field, reverse=0):
        """Initialize a sort predicate.

        'field' -- The field to sort by.

        'reverse' -- If true, sort in reverse order."""

        self.__field = field
        self.__field_name = field.GetName()
        self.__reverse = reverse


    def __call__(self, iss1, iss2):
        """Compare two issues."""

        # Use built-in comparison on the field values.
        result = self.__field.CompareValues(
            iss1.GetField(self.__field_name),
            iss2.GetField(self.__field_name)
            )
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
        if field.CompareValues(value1, value2) != 0:
            differing_fields.append(field)
    return differing_fields


def difference_issues(iss1, iss2):
    """Return an issue difference between issues 'iss1' and 'iss2'.

    'iss1', 'iss2' -- Two 'Issue' instances in the same issue class.

    returns -- An 'IssueDifference' instance containing fields of 'iss2'
    that differ from 'iss1'."""

    # Make sure both are in the same class.
    issue_class = iss1.GetClass()
    assert issue_class == iss2.GetClass()

    # Construct the 'IssueDifference' object.
    difference = IssueDifference(issue_class)
    for field in issue_class.GetFields():
        field_name = field.GetName()
        value1 = iss1.GetField(field_name)
        value2 = iss2.GetField(field_name)
        if field.CompareValues(value1, value2) != 0:
            difference.SetField(field_name, value2)
    return difference


def patch_issue(issue, difference):
    """Inverse of 'difference_issues'.

    'issue' -- An 'Issue' instance.

    'difference' -- An 'IssueDifference' instance.  It must have the
    same issue class as 'issue'.

    returns -- A new issue constructed from 'issue' with the fields in
    'difference' applied."""

    # Make sure both are in the same class.
    assert issue.GetClass() == difference.GetClass()
    # Start with a copy of 'issue'.
    result = issue.copy()
    # Patch in all differing field values.
    for field_name in difference.GetFieldNames():
        result.SetField(field_name, difference.GetField(field_name))
    return result


def get_issues_from_dom_node(issues_node, issue_classes, attachment_store):
    """Convert a DOM element to issues.

    'issues_node' -- A DOM issues element node.

    'issue_classes' -- A map from issue class names to corresponding
    'IssueClass' objects.

    'attachment_store' -- The attachment store in which attachments are
    presumed to be located.

    returns -- A sequence of 'Issue' objects."""

    assert issues_node.tagName == "issues"

    # Extract one result for each result element.
    issues = []
    for issue_node in issues_node.getElementsByTagName("issue"):
        issue_ = get_issue_from_dom_node(
            issue_node, issue_classes, attachment_store)
        issues.append(issue_)
    return issues
    

def _get_field_values_from_dom_node(node, issue_class, attachment_store):
    """Extract field values from a DOM node.

    Extracts field values from child elements named "field".

    'node' -- A DOM node.

    'issue_class' -- The issue class containing the fields to extract.

    'attachment_store' -- The attachment store in which to presume
    attachments are located.

    returns -- A map from field names to corresponding values.  The
    values are validated in the corresponding field."""
    
    field_values = {}
    for field_node in node.getElementsByTagName("field"):
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
                           class_name=issue_class.GetName())

        # There should be only one node in the field element, namely the
        # value element.
        assert len(field_node.childNodes) == 1
        value_node = field_node.childNodes[0]
        # The field can convert the DOM node to a value.  Let any
        # exceptions from this method percolate up.
        value = field.GetValueFromDomNode(value_node, attachment_store)
        # Validate the value.  Let exceptions percolate.
        value = field.Validate(value)
        # Store the field value.
        field_values[field_name] = value

    return field_values


def get_issue_from_dom_node(issue_node, issue_classes, attachment_store):
    """Convert a DOM element to an issue.

    'issue_node' -- A DOM issue element node.

    'issue_classes' -- A map from issue class names to corresponding
    'IssueClass' objects.

    'attachment_store' -- The attachment store in which attachments are
    presumed to be located.

    returns -- An 'Issue' instance."""

    assert issue_node.tagName == "issue"

    # Extract the issue ID.
    iid = issue_node.getAttribute("id")
    # Extract the issue class name.
    issue_class_name = qm.xmlutil.get_child_text(issue_node, "class")
    try:
        # Look up the issue class.
        issue_class = issue_classes[issue_class_name]
    except KeyError:
        # It's a class we don't know.
        raise IssueFileError, \
              qm.error("xml file unknown class", class_name=issue_class_name)

    # Extract field values.  Each is in a field element.]
    field_values = _get_field_values_from_dom_node(
        issue_node, issue_class, attachment_store)
    field_values["iid"] = iid

    # Construct an issue.
    return apply(Issue, [issue_class], field_values)


def get_issue_difference_from_dom_node(difference_node,
                                       issue_class,
                                       attachment_store):
    """Convert a DOM element to an issue difference.

    'difference_node' -- A DOM "issue-difference" element.

    'issue_class' -- The issue class for the difference node.  This must
    be provided, since the XML representation of an issue difference
    does not include the issue class explicitly.

    'attachment_store' -- The attachment store in which to presume
    attachments are located.

    returns -- An 'IssueDifference' instance."""

    assert difference_node.tagName == "issue-difference"
    # Extract field values.  Each is in a field element.
    field_values = _get_field_values_from_dom_node(
        difference_node, issue_class, attachment_store)
    return apply(IssueDifference, [issue_class], field_values)


def get_histories_from_dom_node(histories_node,
                                issue_classes,
                                attachment_store):
    """Convert a DOM element to a sequence of issue histories.

    'histories_node' -- A DOM issue histories element node.  The node
    must be a "histories" element.

    'issue_classes' -- A map from issue class names to corresponding
    'IssueClass' objects.

    'attachment_store' -- The attachment store in which attachments are
    presumed to be located.

    returns -- A sequence of issue histories.  Each element is a
    sequence of consecutive revisions of a single issue."""

    assert histories_node.tagName == "histories"
    issue_histories = []
    for history_node in qm.xmlutil.get_children(histories_node, "history"):
        issue_history = get_history_from_dom_node(
            history_node, issue_classes, attachment_store)
        issue_histories.append(issue_history)
    return issue_histories
    

def get_history_from_dom_node(history_node, issue_classes, attachment_store):
    """Convert a DOM element to an issue history.

    'history_node' -- A DOM issue history element node.  The node must
    be a "history" element.

    'issue_classes' -- A map from issue class names to corresponding
    'IssueClass' objects.

    'attachment_store' -- The attachment store in which attachments are
    presumed to be located.

    returns -- A sequence of consecutive revisions of the issue."""

    assert history_node.tagName == "history"

    issue_nodes = history_node.getElementsByTagName("issue")
    assert len(issue_nodes) == 1
    issue = get_issue_from_dom_node(
        issue_nodes[0], issue_classes, attachment_store)
    issue.SetField("revision", 0)
    revisions = [issue]
    
    issue_class = issue.GetClass()
    for difference_node in \
        history_node.getElementsByTagName("issue-difference"):
        
        difference = get_issue_difference_from_dom_node(
            difference_node, issue_class, attachment_store)

        if not difference.HasField("revision"):
            raise IssueFileError, \
                  qm.error("xml file no revision number")
        revision_number = difference.GetField("revision")
        if revision_number != len(revisions):
            raise IssueFileError, \
                  qm.error("xml file nonconsecutive revisions")
        
        revision = patch_issue(revisions[-1], difference)
        revisions.append(revision)
            
    return revisions


def issues_to_xml(issues, output):
    """Generate an XML representation of issues.

    'issues' -- A sequence of issues.

    'output' -- A file object to which to write the XML."""

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
    

def write_issue_histories(issue_histories, output):
    """Write full histories, with revision history, as XML.

    'issue_histories' -- A sequence of issue histories.  Each element is
    a sequence of revisions of a single issue.

    'output' -- A file object to which to write the XML issue histories."""

    # Create a DOM document.
    document = qm.xmlutil.create_dom_document(
        public_id="-//Software Carpentry//QMTrack Issue V0.1//EN",
        dtd_file_name="issue.dtd",
        document_element_tag="histories"
        )
    # Add an issue element for each issue.
    for issue_history in issue_histories:
        # Create a 'history' element for this issue.
        history_element = document.createElement("history")

        # Write the initial revision.
        assert issue_history[0].GetRevisionNumber() == 0
        revision_element = issue_history[0].MakeDomElement(document)
        history_element.appendChild(revision_element)
        
        # Process subsequent revisions, only including differing
        # fields. 
        for revision_number in xrange(1, len(issue_history)):
            difference = difference_issues(issue_history[revision_number - 1],
                                           issue_history[revision_number])
            revision_element = difference.MakeDomElement(document)
            history_element.appendChild(revision_element)

        document.documentElement.appendChild(history_element)
    # Generate output.
    qm.xmlutil.write_dom_document(document, output)


def load_issue_histories(issue_file_path, issue_classes, attachment_store):
    """Load issue histories stored in the XML file at 'issue_file_path'.

    'issue_classes' -- A map from issue class names to corresponding
    'IssueClass' objects.

    'attachment_store' -- The attachment store in which attachments are
    presumed to be located.

    preconditions -- The file specified by 'issue_file_path' must be a
    valid XML file, whose document element is a "histories" element.

    returns -- A sequence of issue histories.  Each issue history is a
    sequence of 'Issue' instances representing consecutive revisions of
    a single issue."""

    document = qm.xmlutil.load_xml_file(issue_file_path)
    assert document.documentElement.tagName == "histories"
    return get_histories_from_dom_node(
        document.documentElement, issue_classes, attachment_store)


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
    try:
        return eval(expression, globals, locals)
    except NameError, exception:
        raise ExpressionNameError, str(exception)
    except SyntaxError, exception:
        raise ExpressionSyntaxError, str(exception)


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

    extra_locals["_issue"] = revision
    extra_locals["_previous"] = previous
    extra_locals["_changed"] = changed_fn
    extra_locals["_changed_to"] = changed_to_fn
    extra_locals["_new"] = previous_revision is None

    try:
        return eval_issue_expression(expression, revision, extra_locals)
    except NameError, exception:
        raise ExpressionNameError, str(exception)
    except SyntaxError, exception:
        raise ExpressionSyntaxError, str(exception)


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

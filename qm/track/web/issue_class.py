########################################################################
#
# File:   issue_class.py
# Author: Alex Samuel
# Date:   2001-05-02
#
# Contents:
#   Web GUI for viewing and editing an issue class.
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

import copy
import qm.common
import qm.fields
import qm.label
import qm.track
import qm.track.idb
import qm.track.issue_class
import qm.web
import string
import sys
import web

########################################################################
# classes
########################################################################

class ShowPageInfo(web.PageInfo):
    """DTML context for displaying an issue class."""

    mandatory_field_names = qm.track.issue_class.mandatory_field_names

    def __init__(self, request, issue_class):
        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        self.issue_class = issue_class


    def GetFieldType(self, field):
        """Return a description of the type of field 'field', as HTML."""

        if isinstance(field, qm.fields.SetField):
            return "<tt>%s</tt> of <tt>%s</tt>"  \
                   % (field.__class__, field.GetContainedField().__class__)
        else:
            return "<tt>%s</tt>" % field.__class__



class NewFieldPageInfo(web.PageInfo):
    """DTML context for the form to add a field to an issue class."""

    field_types = [
        ("integer field", "qm.fields.IntegerField"),
        ("text field", "qm.fields.TextField"),
        ("attachment field", "qm.fields.AttachmentField"),
        ("enumeration field", "qm.fields.EnumerationField"),
        ("time field", "qm.fields.TimeField"),
        ("user ID field", "qm.fields.UidField"),
        ]
    """Names and Python class names of standard field types."""


    def __init__(self,
                 request,
                 field_name="",
                 field_class_name="",
                 is_set=0,
                 errors={}):
        """Create a new 'PageInfo' context.

        'errors' -- A map of field errors.  If not empty, we're
        redisplaying the new field form to display errors from an
        invalid form submission.  Each key in 'errors' is a field name,
        either "name" or "type", and the corresponding value is a
        structured text error message describing the problem with the
        value of that field."""
        
        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        # Store attributes for use in DTML.
        self.field_name = field_name
        self.field_class_name = field_class_name
        self.is_set = is_set
        # Convert the error messages in 'errors' from structured text to
        # HTML. 
        for key, value in errors.items():
            errors[key] = qm.structured_text.to_html(value)
        self.errors = errors



########################################################################
# functions
########################################################################

def _get_issue_class_for_session(request):
    """Return the issue class object for the session in 'request'."""

    # The request should contain a field specifying the internal ID of
    # the session object, as a sanity check.
    try:
        session_issue_class_id = int(request["session_issue_class_id"])
    except KeyError:
        # The session ID wasn't specified in the request.
        raise RuntimeError, "No ID session issue class in request."
    # The issue class object itself should be attached to the session
    # object. 
    session = request.GetSession()
    try:
        issue_class = session.__issue_class
    except AttributeError:
        # Oops, no issue class for this session.
        raise RuntimeError, "No issue class for request."
    # Make sure the ID specified in the request matches our ID.
    if id(issue_class) != session_issue_class_id:
        raise RuntimeError, "ID mismatch for session issue class."

    return issue_class


def handle_show_class(request):
    """Handle a web request to show and edit an issue class.

    'request' -- A 'WebRequest' object."""

    session = request.GetSession()

    try:
        # Try to extract the name of the issue class from the request.
        issue_class_name = request["issue_class"]
    except KeyError:
        # There is no class name specified.  Use the class associated
        # with the session.
        issue_class = _get_issue_class_for_session(request)
    else:
        # Got the issue class name.  Get it from the IDB.
        idb = qm.track.get_idb()
        issue_class = idb.GetIssueClass(issue_class_name)
        # Make a copy of it.
        issue_class = copy.deepcopy(issue_class)
        # Attach the copy to the request.  Subsequent requests refer to
        # this copy by omitting the 'class' query field.
        session.__issue_class = issue_class
        # Now redirect to a page that uses the session's issue class,
        # rather than specifying the issue class explicitly.  Store the
        # internal ID of the copied issue class in the URL, so we can do
        # a sanity check later when the issue class is retrieved from
        # the session.
        del request["issue_class"]
        request["session_issue_class_id"] = str(id(issue_class))
        raise qm.web.HttpRedirect, request.AsUrl()

    page_info = ShowPageInfo(request, issue_class)
    return web.generate_html_from_dtml("issue-class.dtml", page_info)


def handle_show_field(request):
    """Handle the request to show/edit an issue class field.

    Uses the issue class associated with the request's session.  The
    name of the field is specified in the "field" attribute of the
    request."""

    # Get hold of the field.
    issue_class = _get_issue_class_for_session(request)
    field_name = request["field"]
    field = issue_class.GetField(field_name)
    # This is the request to which to submit edits to the field.  See
    # 'handle_submit_field'. 
    submit_request = request.copy("submit-issue-field")
    # Have the field generate its page.
    return field.GenerateEditWebPage(request, submit_request)


def handle_submit_field(request):
    """Handle the submission of edits to an issue class field.

    Uses the issue class associated with the request's session.  The
    name of the field is specified in the "field" attribute of the
    request."""

    # Get the issue class associated with the session.
    issue_class = _get_issue_class_for_session(request)
    # Get the field.  Its name is included in the request.
    field_name = request["field"]
    field = issue_class.GetField(field_name)

    # Change the field according to the request.
    field.UpdateFromRequest(request)

    # Return a page that closes the field editing window and reloads the
    # issue class page in the window opener.
    return '''
    <html>
     <body>
      <script language="JavaScript">
      // Reload the document in the parent window, which should be the
      // page showing whatever contains this field.
      window.opener.location = window.opener.location;
      // Close this popup window.
      window.close();
      </script>
     </body>
    </html>
    '''


def handle_config_idb(request):
    """Handle a request for the IDB configuration page."""

    # FIXME: Check authorization.
    request.GetSession()

    page_info = qm.track.web.PageInfo(request)
    idb = qm.track.get_idb()
    # Generate a list of issue classes in the IDB.
    page_info.issue_classes = idb.GetIssueClasses()
    # Put them into dictionary order.
    page_info.issue_classes.sort(
        lambda c1, c2: cmp(c1.GetName(), c2.GetName()))
    return qm.track.web.generate_html_from_dtml("config-idb.dtml",
                                                page_info)


def handle_submit_class(request):
    """Handle a 'submit-issue-class' request.

    This request commits changes to the issue class attached to the
    request's session.

    'request' -- A 'WebRequest' object."""

    session = request.GetSession()

    # Extract the issue class we're submitting, which is associated with
    # the request's session.
    issue_class = _get_issue_class_for_session(request)
    issue_class_name = issue_class.GetName()

    # Is this a new issue class, or a revision to an existing one?
    # Determine by checking whether there is already an issue class in
    # the IDB with the same name.
    try:
        idb = qm.track.get_idb()
        previous_issue_class = idb.GetIssueClass(issue_class_name)

    except KeyError:
        # This is a new issue class.
        # FIXME: Implement this.
        raise NotImplemenedError, "new issue class"

    else:
        # This is a new revision of an exising issue class.
        idb.UpdateIssueClass(issue_class)

    # Dissociate the issue class from the session. 
    del session.__issue_class    
    # Redirect to the IDB configuration page.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("config-idb", base=request).AsUrl()


def handle_delete_field(request):
    """Handle a 'delete-issue-field' request.

    This request removes a field from the issue class currently being
    edited in the request's session.  The "field" query attribute
    contains the name of the field to delete."""

    # Get hold of the field to delete.
    issue_class = _get_issue_class_for_session(request)
    field_name = request["field"]
    field = issue_class.GetField(field_name)
    # Remove it.
    issue_class.RemoveField(field)
    # Redisplay the issue class.
    show_request = request.copy("show-issue-class")
    del show_request["field"]
    raise qm.web.HttpRedirect, show_request.AsUrl()


def handle_add_field(request):
    """Handle an 'add-issue-field' request.

    This request shows a form for adding a new field to the issue class
    currently being edited in the request's session."""

    issue_class = _get_issue_class_for_session(request)
    page_info = NewFieldPageInfo(request)
    return web.generate_html_from_dtml("add-issue-field.dtml", page_info)


def handle_new_field(request):
    """Handle a 'new-issue-field' request.

    Processes the addition of a new field to the issue class currently
    being editied in the request's session.  These query attributes are
    used from the request:

      'name' -- The name of the new field.

      'type' -- The Python class name of the field type.

      'is_set' -- Either "true" or "false", for whether this is a set
      field.  If it is, 'type' is the name of the contained field type.
    """

    issue_class = _get_issue_class_for_session(request)
    errors = {}

    # Extract the field name.
    field_name = string.strip(request["name"])
    if not qm.label.is_valid(field_name):
        errors["name"] = qm.error("invalid field name", field_name=field_name)
    # Extract the name of the field type.
    field_class_name = string.strip(request["type"])
    try:
        # Load the class.
        field_class = qm.common.load_class(field_class_name, sys.path)
    except (ImportError, ValueError), err:
        # Couldn't load the class.
        errors["type"] = qm.error("invalid field type",
                                  field_type=field_class_name)
    else:
        # Make sure the field type is a subclass of 'Field'.
        if not issubclass(field_class, qm.fields.Field) \
           or field_class is qm.fields.Field:
            errors["type"] = qm.error("invalid field type",
                                      field_type=field_class.__name__)
    # Is this a set field?
    is_set = ["false", "true"].index(request["is_set"])

    if len(errors) > 0:
        # There were errors.  Redisplay the form for adding a new field,
        # showing the values already entered, and the appropriate error
        # messages. 
        page_info = NewFieldPageInfo(request, field_name,
                                     field_class_name, is_set, errors)
        return web.generate_html_from_dtml("add-issue-field.dtml",
                                           page_info)
    else:
        # Good to go.  Instantiate a field object.
        field = field_class(field_name, title=field_name)
        # If a set was requested, wrap it in a 'SetField'.
        if is_set:
            field = qm.fields.SetField(field)
        # Add it to the issue class.
        issue_class.AddField(field)

        # Redirect to the page displaying the issue class.
        show_request = request.copy("show-issue-class")
        for attribute_name in ["name", "type", "is_set"]:
            del show_request[attribute_name]
        raise qm.web.HttpRedirect, show_request.AsUrl()


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

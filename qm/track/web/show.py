########################################################################
#
# File:   show.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Web form to display an issue.
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

"""Web form to show a single issue.

This form is generated from the DTML template show.dtml.  It can be
used to show an issue in read-only mode or as an editable form.  The
latter may be used for editing an existing issue or submitting a new
one.

The form recognizes the following query arguments:

'style' -- The style of the form.  

'class' -- The name of the issue class containing the issue.

'history' -- If specified, whether to show revision history.

Available styles include:

full -- Read-only view.

new -- Create a new issue.

edit -- Edit an existing issue."""

########################################################################
# imports
########################################################################

import mimetypes
import qm.fields
import qm.structured_text
import qm.track.issue
import qm.track.issue_store
import qm.web
import string
import sys
import urllib
import web

########################################################################
# classes
########################################################################

class ShowPage(web.DtmlPage):
    """Page for displaying or editing an issue.

    The following attributes are available as DTML variables.

      'issue' -- The 'Issue' instance to display.

      'fields' -- A sequence of 'Field' objects representing the fields
      of the issue class containing 'issue', in the order they are to be
      displayed.

      'style' -- A string representing the style of the page to
      generate.

      'request' -- The 'WebRequest' object for which this page is being
      generated."""
    

    def __init__(self,
                 issue,
                 style="full",
                 show_history=0,
                 errors={}):
        """Create a new page.

        'issue' -- To show or edit an existing page, pass it as 'issue'.
        To create a new issue, pass a freshly-made 'Issue' instance as
        'issue', and specify the style "new" in 'request'.

        'style' -- The style in which to display the issue.  May be
        "full" for a read-only display, "edit" to edit an existing
        issue, or "new" to edit a new issue.

        'show_history' -- If true, show the revision history.

        'errors' -- A mapping from field names to error messages.
        If non-empty, the error messages are shown with the
        corresponding fields."""

        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "show.dtml",
                              style=style,
                              issue=issue,
                              show_history=show_history)
        # Convert the error messages in 'errors' from structured text to
        # HTML. 
        for key, value in errors.items():
            errors[key] = qm.structured_text.to_html(value)
        self.errors = errors
        self.fields = self.issue.GetClass().GetFields()
        if self.style == "edit":
            # Since we're editing the issue, show it with an
            # incremented revision number.
            issue.SetField("revision", issue.GetField("revision") + 1)
        # Cache the issue's revision history in this attribute.
        self.__history = None


    def IsForm(self):
        """Return a true value if generating an HTML form."""

        return self.style == "new" or self.style == "edit"


    def IsShowField(self, field):
        """Return a true value if 'field' should be displayed."""

        # If we're showing a specific revision of the issue, rather
        # than the current revision, display the revision number.
        if field.GetName() == "revision" \
           and self.request.has_key("revision"):
            return 1
        # Show all other fields that aren't hidden.
        return not field.IsProperty("hidden")


    def FormatFieldValue(self, field):
        """Return an HTML rendering of the value for 'field'."""

        idb = self.request.GetSession().idb
        style = self.style
        field_name = field.GetName()
        value = self.issue.GetField(field_name)

        # If creating or editing an issue, it doesn't make sense to show
        # the last modifying user and time.
        if style in ["new", "edit"]:
            if field_name is "user":
                # For the user field, show the active user.
                value = self.request.GetSession().GetUserId()
            elif field_name is "timestamp":
                # For the timestamp field, show the current time.
                value = field.GetCurrentTime()

        # If the user shouldn't be allowed to initialize or edit this
        # field, don't render it as editiable.
        if field.IsProperty("read_only") \
           and style in ["new", "edit"]:
            style = "full"
        if field.IsProperty("initialize_only") and style == "edit":
            style = "full"
        if field.IsProperty("initialize_to_default") \
           and style == "new":
            style = "full"

        result = field.FormatValueAsHtml(value, style)

        if field.GetName() == "revision" and self.show_history:
            # Doctor the value of the result field slightly to
            # indicate we're not showing the current revision.
            result = result \
                     + " (current revision is %d)" \
                     % self.GetHistory()[-1].GetRevisionNumber()

        return result


    def MakeSubmitUrl(self):
        """Generate a URL for submitting a new issue or revision."""

        request = self.request.copy("submit")
        request["class"] = self.issue.GetClass().GetName()
        return request.AsUrl()
    

    def MakeEditUrl(self):
        """Generate a URL for editing the issue being shown."""

        request = self.request.copy()
        request["style"] = "edit"
        # Always edit the current revision.
        if request.has_key("revision"):
            del request["revision"]
        if request.has_key("history"):
            del request["history"]
        return request.AsUrl()


    def MakeHistoryUrl(self, show=1):
        """Generate a URL for showing or hiding the revision history.

        'show' -- If true, show the revision history.  Otherwise,
        don't."""

        request = self.request.copy()
        # Use the argument 'history=1' to show the history; omit this
        # argument to hide.
        if show:
            request["history"] = "1"
            request["revision"] = self.issue.GetRevisionNumber()
        else:
            if request.has_key("history"):
                del request["history"]
            if request.has_key("revision"):
                del request["revision"]
        return request.AsUrl()


    def MakeShowRevisionUrl(self, revision_number):
        """Generate a URL to show a revision of this issue."""

        request = self.request.copy()
        request["revision"] = "%d" % revision_number
        return request.AsUrl()


    def FormatHistory(self):
        """Generate HTML for the revision history of this issue."""

        fragment = web.HistoryPageFragment(
            self.GetHistory(), self.issue.GetRevisionNumber())
        fragment.MakeShowRevisionUrl = self.MakeShowRevisionUrl
        return fragment()


    def GetHistory(self):
        """Return a list of all revisions of the issue."""

        # Obtain the list of revisions just in time, and cache the
        # results. 
        if self.__history is None:
            issue_store = self.request.GetSession().idb.GetIssueStore()
            iid = self.issue.GetId()
            self.__history = issue_store.GetIssueHistory(iid)
        return self.__history



########################################################################
# functions
########################################################################

def handle_show(request):
    """Generate the show issue page.

    'request' -- A 'WebRequest' object."""

    # Make sure that the form has the iid argument set.  If not, the
    # user probably submitted the form without entering an IID.
    if not request.has_key("iid"):
        msg = "You must specify an issue ID."
        return qm.web.generate_error_page(request, msg)

    # Determine the issue to show.
    iid = request["iid"]
    istore = request.GetSession().idb.GetIssueStore()

    try:
        # Get the issue.
        if request.has_key("revision"):
            # A specific revision was requested.
            issue = istore.GetIssue(iid, int(request["revision"]))
        else:
            # Use the current revision.
            issue = istore.GetIssue(iid)
    except KeyError:
        # An issue with the specified iid was not fount.  Show a page
        # indicating the error.
        msg = """
        The issue database does not contain an issue with the ID you
        specified, "%s".""" \
        % iid
        return qm.web.generate_error_page(request, msg)

    style = request.get("style", "full")
    show_history = int(request.get("history", 0))
    page = ShowPage(issue, style, show_history)
    # Generate HTML.
    return page(request)


def handle_new(request):
    """Generate a form for a new issue."""

    idb = request.GetSession().idb

    # If an issue class was specified, use it; otherwise, assume the
    # default class.
    if request.has_key("class"):
        issue_class_name = request["class"]
    else:
        issue_class_name = idb.GetConfiguration()["default_class"]
    issue_class = idb.GetIssueClass(issue_class_name)
    # Create a new issue.
    issue = qm.track.issue.Issue(issue_class)

    return ShowPage(issue, "new")(request)


def handle_submit(request):
    """Process a submission of a new or modified issue."""

    requested_revision = int(request["revision"])
    idb = request.GetSession().idb
    istore = idb.GetIssueStore()
    issue_class = idb.GetIssueClass(request["class"])

    # Is this the submission of a new issue?
    is_new = (requested_revision == 0)
        
    if is_new:
        # Create a new issue instance.
        iid = issue_class.AllocateNextId()
        issue = qm.track.issue.Issue(issue_class, iid=iid)
    else:
        # It's a new revision of an existing issue.  Retrieve the
        # latter.
        iid = request["iid"]
        issue = istore.GetIssue(iid)
        # Make sure the requested revision is one greater than the
        # most recent stored revision for this issue.  If it's not,
        # this probably indicates that this issue was modified while
        # this new revision was being formulated by the user.
        if issue.GetRevisionNumber() + 1 != requested_revision:
            msg = """
            Someone else has modified this issue since you started
            editing it (or perhaps you submitted the same changes
            twice).  Please reload the issue and resubmit your edits.
            """
            return qm.web.generate_error_page(request, msg)

    errors = {}

    field_prefix = qm.fields.Field.form_field_prefix
    # Loop over query arguments in the submission.
    for name, value in request.items():
        # Does this look like a form field representing an issue field
        # value? 
        if not qm.starts_with(name, field_prefix):
            # No, so skip it.
            continue
        # Trim off the prefix to obtain the field name.
        field_name = name[len(field_prefix):]
        # Obtain the corresponding field.
        field = issue_class.GetField(field_name)
        # Interpret the query argument value as the field value.
        try:
            value = field.ParseFormValue(value)
        except:
            sys.stderr.write(qm.common.format_exception(sys.exc_info()))
            # Something went wrong parsing the value.  Associate an
            # error message with this field.
            message = str(sys.exc_info()[1])
            errors[field_name] = message
        else:
            # If the field is an attachment field, or a set of
            # attachments field, we have to process the values.  The
            # data for each attachment is stored in the temporary
            # attachment store; we need to copy it from there into the
            # IDB.  This function does the work.
            if isinstance(field, qm.fields.AttachmentField):
                # An attachment field -- process the value.
                value = web.store_attachment_data(idb, issue, value)
            elif isinstance(field, qm.fields.SetField) \
                 and isinstance(field.GetContainedField(),
                                qm.fields.AttachmentField):
                # An attachment set field -- process each element of the
                # value.
                value = map(
                    lambda attachment, idb=idb, issue=issue: \
                    web.store_attachment_data(idb, issue, attachment),
                    value)

            issue.SetField(field_name, value)

    # Set the user ID in the issue or revision.
    issue.SetField("user", request.GetSession().GetUserId())

    # Is the submission valid?
    invalid_fields = issue.Validate()
    if len(invalid_fields) > 0:
        # There are invalid fields.  Instead of putting the submission
        # through, reshow the form, indicating the problems.
        for field_name, exc_info in invalid_fields.items():
            errors[field_name] = str(exc_info[1])

    # If this is a new revision of an existing issue, find the changes
    # made relative to the previous revision.
    if requested_revision > 0:
        previous_revision = istore.GetIssue(iid)
        differences = qm.track.issue.get_differing_fields(
            issue, previous_revision)
        # Has anything at all changed?
        if len(differences) == 0:
            # No, so don't update.
            errors["_issue"] = qm.warning("no changes")

    # Submit the issue or revision if there are no errors so far.
    if len(errors) == 0:
        try:
            if requested_revision == 0:
                # Add the new issue.
                istore.AddIssue(issue)
            else:
                # Add the new revision.
                issue.SetField("revision", requested_revision)
                istore.AddRevision(issue)
        except ValueError, exception:
            errors["iid"] = qm.error("iid already used", iid=iid)
        except qm.track.issue_store.TriggerRejectError, exception:
            trigger_result = exception.GetResult()
            errors["_issue"] = trigger_result.GetMessage()

    if len(errors) > 0:
        # There were errors, so redisplay the edit form.
        if is_new:
            style = "new"
        else:
            style = "edit"
        page = ShowPage(issue, style, errors=errors)
        new_request = qm.web.WebRequest("show", base=request)
        # We need to use this syntax since 'class' is a keyword.
        new_request["class"] = request["class"]
        return page(new_request)
    else:
        # The issue or revision was entered successfully.  Redirect
        # to the show page for the newly-created or -modified issue.
        # That way, if the user reloads the page or backs up to it,
        # the issue form will not be resubmitted.
        raise qm.web.HttpRedirect, \
              qm.web.WebRequest("show", base=request, iid=iid)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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

import cgi
import qm.web
import string
import web

########################################################################
# classes
########################################################################

class ShowPageInfo(web.PageInfo):
    """DTML context for generationg 'show.dtml'.

    The following attributes are available as DTML variables.

    'issue' -- The 'Issue' instance to display.

    'fields' -- A sequence of 'IssueField' objects representing the
    fields of the issue class containing 'issue', in the order they
    are to be displayed.

    'style' -- A string representing the style of the page to
    generate.

    'request' -- The 'WebRequest' object for which this page is being
    generated."""
    

    def __init__(self, request, issue):
        """Create a new page.

        To show or edit an existing page, pass it as 'issue'.  To
        create a new issue, pass a freshly-made 'Issue' instance as
        'issue', and specify the style "new" in 'request'."""

        # Initialize the base class.
        qm.web.PageInfo.__init__(self, request)
        # Set up attributes.
        self.issue = issue
        self.fields = self.issue.GetClass().GetFields()
        if request.has_key("style"):
            self.style = request["style"]
        else:
            # Default style is "full".
            self.style = "full"
        if request.has_key("history"):
            self.show_history = int(request["history"])
        else:
            self.show_history = 0
        if self.style == "edit":
            # Since we're editing the issue, show it with an
            # incremented revision number.
            issue.SetField("revision", issue.GetField("revision") + 1)


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
        return not field.IsAttribute("hidden")


    def FormatFieldValue(self, field):
        """Return an HTML rendering of the value for 'field'."""

        value = self.issue.GetField(field.GetName())
        result = web.format_field_value(field, value, self.style)

        if field.GetName() == "revision" \
           and self.request.has_key("revision"):
            # Doctor the value of the result field slightly to
            # indicate we're not showing the current revision.
            result = result \
                     + " (current revision is %d)" \
                     % self.current_revision.GetRevision()

        return result


    def MakeSubmitUrl(self):
        """Generate a URL for submitting a new issue or revision."""

        request = qm.web.WebRequest("submit")
        request["class"] = self.issue.GetClass().GetName()
        return qm.web.make_url_for_request(request)
    

    def MakeEditUrl(self):
        """Generate a URL for editing the issue being shown."""

        request = self.request.copy()
        request["style"] = "edit"
        # Always edit the current revision.
        if request.has_key("revision"):
            del request["revision"]
        if request.has_key("history"):
            del request["history"]
        return qm.web.make_url_for_request(request)


    def MakeHistoryUrl(self, show=1):
        """Generate a URL for showing or hiding the revision history.

        'show' -- If true, show the revision history.  Otherwise,
        don't."""

        request = self.request.copy()
        # Use the argument 'history=1' to show the history; omit this
        # argument to hide.
        if show:
            request["history"] = "1"
            request["revision"] = self.issue.GetRevision()
        else:
            if request.has_key("history"):
                del request["history"]
            if request.has_key("revision"):
                del request["revision"]
        return qm.web.make_url_for_request(request)


    def MakeShowRevisionUrl(self, revision_number):
        """Generate a URL to show a revision of this issue."""

        request = self.request.copy()
        request["revision"] = "%d" % revision_number
        return qm.web.make_url_for_request(request)


    def FormatHistory(self):
        """Generate HTML for the revision history of this issue."""

        page_info = web.HistoryPageInfo(self.revisions,
                                        self.issue.GetRevision())
        page_info.MakeShowRevisionUrl = self.MakeShowRevisionUrl
        return web.generate_html_from_dtml("history.dtml", page_info)




########################################################################
# functions
########################################################################

def handle_show(request):
    """Generate the show issue page.

    'request' -- A 'WebRequest' object."""

    # Determine the issue to show.
    iid = request["iid"]
    idb = qm.track.get_idb()

    # Get the issue.
    if request.has_key("revision"):
        # A specific revision was requested.
        issue = idb.GetIssue(iid, int(request["revision"]))
    else:
        # Use the current revision.
        issue = idb.GetIssue(iid)

    page_info = ShowPageInfo(request, issue)
    # If we're be showing a revision history, we need to provide all
    # previous revisions too 
    if request.has_key("history"):
        page_info.revisions = idb.GetAllRevisions(iid, issue.GetClass())
    # If we're showing an old revision, grab the current revision too.
    if request.has_key("revision"):
        page_info.current_revision = idb.GetIssue(iid)
    # Generate HTML.
    return web.generate_html_from_dtml("show.dtml", page_info)


def handle_new(request):
    """Generate a form for a new issue."""

    idb = qm.track.get_idb()

    # If an issue class was specified, use it; otherwise, assume the
    # default class.
    if request.has_key("class"):
        issue_class_name = request["class"]
    else:
        issue_class_name = qm.track.get_configuration()["default_class"]
    issue_class = idb.GetIssueClass(issue_class_name)
    # Create a new issue.
    issue = qm.track.Issue(issue_class, "")

    request["style"] = "new"

    page_info = ShowPageInfo(request, issue)
    return web.generate_html_from_dtml("show.dtml", page_info)


def handle_submit(request):
    """Process a submission of a new or modified issue."""

    iid = request["iid"]
    requested_revision = int(request["revision"])
    idb = qm.track.get_idb()
    issue_class = idb.GetIssueClass(request["class"])
        
    if requested_revision == 0:
        # It's a new issue submission.  Create a new issue instance.
        issue = qm.track.Issue(issue_class, iid)
    else:
        # It's a new revision of an existing issue.
        issue = idb.GetIssue(iid)
        # Make sure the requested revision is one greater than the
        # most recent stored revision for this issue.  If it's not,
        # this probably indicates that this issue was modified while
        # this new revision was being formulated by the user.
        if issue.GetRevision() + 1 != requested_revision:
            # FIXME: Handle this more gracefully.
            raise RuntimeError, "issue revision incoherency"

    for name, value in request.items():
        if name[:6] == "field-":
            field_name = name[6:]
        else:
            continue
        issue.SetField(field_name, value)

    if requested_revision == 0:
        # Add the new issue.
        idb.AddIssue(issue)
    else:
        # Add the new revision.
        idb.AddRevision(issue)

    # Don't respond directly with the show page for the newly-created
    # or -modified issue.  Instead, redirect to it.  That way, if the
    # user reloads the page or backs up to it, the issue form will not
    # be resubmitted.
    request = qm.web.WebRequest("show", iid=iid)
    raise qm.web.HttpRedirect, (qm.web.make_url_for_request(request))


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

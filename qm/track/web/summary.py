########################################################################
#
# File:   summary.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Web form to summarize issues in a table.
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

"""Web form to print a table of issues.

The form is generated from the DTML template summary.dtml, using
code in this module.

The form recognizes the following query arguments:

'sort' -- The name of the field by which to sort the issues, prefixed
with a hyphen for reverse sort.

'query' -- If specified, show the issues matching this query.
Otherwise, show all issues."""

########################################################################
# imports
########################################################################

import qm.web
import string
import web

########################################################################
# classes
########################################################################

class SummaryPageInfo(web.PageInfo):
    """DTML context for generating 'summary.dtml'.

    The following attributes are available as DTML variables.

    'field_names' -- A sequence of field names to display in the
    table.

    'issues' -- A sequence of issues to display in the table."""

    def __init__(self, request, issues, field_names):
        """Create a new page.

        'request' -- A 'WebRequest' object containing the page
        request.

        'issues' -- A sequence of issues to summarize."""

        qm.web.PageInfo.__init__(self, request)

        self.field_names = field_names

        # Partition issues by issue class.  'self.issue_map' is a map
        # from issue class onto a sequence of issues.
        self.issue_map = {}
        for issue in issues:
            issue_class = issue.GetClass()
            if self.issue_map.has_key(issue_class):
                self.issue_map[issue_class].append(issue)
            else:
                self.issue_map[issue_class] = [ issue ]

        # Did the request specify a sort order?
        if self.request.has_key("sort"):
            # Yes.  Sort each list of issues accordingly.
            sort_field = self.request["sort"]
            # If the first character of the sort field is a hyphen, that
            # indicates a reverse sort.
            if sort_field[0] == "-":
                reverse = 1
                # The rest is the field name.
                sort_field = sort_field[1:]
            else:
                reverse = 0
            sort_predicate = qm.track.IssueSortPredicate(sort_field,
                                                         reverse)
            for issue_list in self.issue_map.values():
                issue_list.sort(sort_predicate)

        # Extract a list of issue classes we need to show.
        self.issue_classes = self.issue_map.keys()
        # Put them into dictionary order by title.
        sort_predicate = lambda cl1, cl2: \
                         cmp(cl1.GetTitle(), cl2.GetTitle())
        self.issue_classes.sort(sort_predicate)

        # Generate the HTML page for the popup window for selecting
        # display options.
        display_options_page_info = DisplayOptionsPageInfo(
            request,
            self.issue_map.keys(),
            self.field_names)
        display_options_page = web.generate_html_from_dtml(
            "summary-display-options.dtml",
            display_options_page_info)
        # Construct the Display Options button, which pops up a window
        # showing this page.
        self.display_options_button = qm.web.make_button_for_popup(
            "Change Display Options...",
            display_options_page,
            request=self.request,
            window_width=640,
            window_height=320)


    def IsIssueShown(self, issue):
        """Return a true value if 'issue' should be displayed."""

        return 1


    def GetBackgroundColor(self, issue):
        """Return the color, in HTML syntax, for the row showing 'issue'."""

        return "#e0e0e0"


    def GetForegroundColor(self, issue):
        """Return the text color, in HTML syntax, for displaying 'issue'."""

        if issue.GetField("state") >= 0:
            return "black"
        else:
            return "#808080"


    def FormatFieldValue(self, issue, field_name):
        """Generate a rendering of a field value.

        'issue' -- The issue from which to obtain the value.

        'field_name' -- The name of the field whose value to render.

        returns -- The field value, formatted for HTML."""

        field = issue.GetClass().GetField(field_name)
        value = issue.GetField(field_name)
        return field.FormatValueAsHtml(value, style="brief")


    def MakeResortUrl(self, field_name):
        """Generate a URL for the same page, but sorted by 'field_name'."""

        # Take all the previous field values.
        new_request = self.request.copy()
        # If the previous key had a sort field, and this is the same
        # field, prepend a dash, which indicates reverse sort.
        if self.request.has_key("sort") \
           and self.request["sort"] == field_name:
            field_name = "-" + field_name
        # Add a sort specificaiton.
        new_request["sort"] = field_name
        # Generate the new URL.
        return qm.web.make_url_for_request(new_request)


    def MakeIssueUrl(self, issue):
        """Generate a URL to show an individual issue."""

        request = self.request.copy("show", iid=issue.GetId())
        return qm.web.make_url_for_request(request)



class DisplayOptionsPageInfo(web.PageInfo):
    """DTML context for generating 'summary-display-options.dtml'.

    The following attributes are availablet as DTML variables.

    'field_controls' -- The HTML controls for selecting the fields to
    display.

    'base_url' -- The base URL to redisplay the issue summary."""

    def __init__(self, request, issue_classes, included_field_names):
        """Create a new page info context.

        'request' -- A 'WebRequest' object.

        'issue_classes' -- A sequence of all issue classes available in
        the issue summary.

        'included_field_names' -- A sequence of names of all fields
        currently included in the issue summary display."""

        # Initialize the base class.
        qm.web.PageInfo.__init__(self, request)

        # Construct a map from field name to field object for all fields
        # in all issue classes.
        fields = {}
        for issue_class in issue_classes:
            for field in issue_class.GetFields():
                if not field.IsAttribute("hidden"):
                    fields[field.GetName()] = field
        # Find all field names that aren't in 'included_field_names'.
        excluded_field_names = []
        for field_name in fields.keys():
            if not field_name in included_field_names:
                excluded_field_names.append(field_name)

        # This function returns the title of the field whose name is
        # 'field_name'.  If it isn't a field we know about here, just
        # return the field name.
        def get_title(field_name, fields=fields):
            if fields.has_key(field_name):
                return fields[field_name].GetTitle()
            else:
                return field_name

        # Construct the controls for selecting fields to display.
        self.fields_controls = qm.web.make_choose_control(
            "fields",
            "Show Fields",
            included_field_names,
            "Don't Show Fields",
            excluded_field_names,
            item_to_text=get_title,
            ordered=1)

        # Build the base URL for redisplaying the issue summary.  The
        # form will add fields to this URL to reflect the display
        # options selected in the form.  Blank out the fields that the
        # form will add.
        redisplay_request = request.copy()
        if redisplay_request.has_key("fields"):
            del redisplay_request["fields"]
        self.base_url = qm.web.make_url_for_request(redisplay_request)



########################################################################
# functions
########################################################################

def handle_summary(request):
    """Generate the summary page.

    'request' -- A 'WebRequest' object."""

    user = request.GetSession().GetUser()

    idb = qm.track.get_idb()
    if request.has_key("query"):
        # This page is a response to a query.
        query = request["query"]

        try:
            issues = []
            # Query all issue classes successively.
            for issue_class in idb.GetIssueClasses():
                issues = issues + idb.Query(query, issue_class.GetName())
        except NameError, name:
            msg = """
            %s cannot understand the name %s in the query you specified:

              '%s'
            """ % (qm.track.get_name(), name, query)
            return qm.web.generate_error_page(request, msg)
        except SyntaxError:
            msg = """
            %s encountered a syntax error while processing the query
            you specified:

              '%s'
            """ % (qm.track.get_name(), query)
            return qm.web.generate_error_page(request, msg)

    else:
        # No query was specified; show all issues...
        issues = idb.GetIssues()
        # ... that aren't deleted.
        issues = filter(lambda iss: not iss.IsDeleted(), issues)

    # The request may specify the fields to display in the summary.  Are
    # they specified?
    if request.has_key("fields"):
        # Yes; use them.
        field_names = request["fields"]
        # Save them as the default for next time in the user record.
        user.SetConfigurationProperty("summary_fields", field_names)
    else:
        # No.  Retrieve the fields to show from the user record, or use
        # a default if they're not listed there.
        field_names = user.GetConfigurationProperty(
            "summary_fields", "iid,summary,timestamp,state")
    # Split field names into a sequence.
    field_names = string.split(field_names, ",")
    # Make sure the IID field is in there somewhere.
    if not "iid" in field_names:
        field_names.insert(0, "iid")

    page_info = SummaryPageInfo(request, issues, field_names)
    return web.generate_html_from_dtml("summary.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

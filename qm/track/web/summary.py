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
Otherwise, show all issues.

'last_query' -- If this argument is included, use the query expression
from the last query run by this user.  The argument value is ignored.

'open_only' -- Either 0 or 1, indicating whether only open issues should
be shown.  If omitted, the value 0 is impled."""

########################################################################
# imports
########################################################################

import qm.web
import string
import sys
import web

########################################################################
# classes
########################################################################

class SummaryPage(web.DtmlPage):
    """Page summarizing multiple issues in a table, as for query results.

    The following attributes are available as DTML variables.

      'issues' -- A sequence of issues to display in the table."""

    def __init__(self,
                 issues,
                 field_names,
                 sort_order,
                 open_only=0):
        """Create a new page.

        'issues' -- A sequence of issues to summarize.

        'field_names' -- A comma-separated list of field names to
        display.

        'sort_order' -- The name of the field by which to sort entries.
        If prefixed with a minus sign, sort in reverse order.

        'open_only' -- If true, show only issues in an open state."""

        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "summary.dtml",
                              field_names=field_names,
                              open_only=open_only)

        # If requested, limit the issues to open issues only.
        if open_only:
            issues = filter(lambda i: i.IsOpen(), issues)

        # Partition issues by issue class.  'self.issue_map' is a map
        # from issue class onto a sequence of issues.
        self.issue_map = {}
        for issue in issues:
            issue_class = issue.GetClass()
            if self.issue_map.has_key(issue_class):
                self.issue_map[issue_class].append(issue)
            else:
                self.issue_map[issue_class] = [ issue ]

        # If the first character of the sort order is a hyphen, that
        # indicates a reverse sort.
        if sort_order[0] == "-":
            reverse = 1
            # The rest is the field name.
            sort_field = sort_order[1:]
        else:
            reverse = 0
            sort_field = sort_order
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


    def MakeDisplayOptionsButton(self):
        """Construct the button that pops up the display options page."""

        # Generate the HTML page for the popup window for selecting
        # display options.
        display_options_page = DisplayOptionsPage(
            self.issue_map.keys(),
            self.field_names,
            self.open_only)
        display_options_page = display_options_page(self.request)
        # Construct the Display Options button, which pops up a window
        # showing this page.
        return qm.web.make_button_for_popup(
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

        issue_class = issue.GetClass()
        try:
            field = issue_class.GetField(field_name)
        except KeyError:
            # This issue does not have a field by this name.  Skip it.
            return "&nbsp;"
        else:
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
        return new_request.AsUrl()


    def MakeIssueUrl(self, issue):
        """Generate a URL to show an individual issue."""

        return self.request.copy("show", iid=issue.GetId()).AsUrl()



class DisplayOptionsPage(web.DtmlPage):
    """Popup page for setting summary display options.

    The following attributes are availablet as DTML variables.

      'field_controls' -- The HTML controls for selecting the fields to
      display.

      'base_url' -- The base URL to redisplay the issue summary."""

    def __init__(self,
                 issue_classes,
                 included_field_names,
                 open_only):
        """Create a new page info context.

        'issue_classes' -- A sequence of all issue classes available in
        the issue summary.

        'included_field_names' -- A sequence of names of all fields
        currently included in the issue summary display.

        'open_only' -- True if only open issues are currently
        displayed."""

        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "summary-display-options.dtml",
                              show_decorations=0)

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

        self.open_only = open_only
        # Construct a list of names of open states in the state model
        # for these issue classes.
        if len(issue_classes) > 0:
            issue_class = issue_classes[0]
            state_model = issue_class.GetField("state").GetStateModel()
            self.open_state_names = state_model.GetOpenStateNames()
        else:
            self.open_state_names = []


    def MakeBaseUrl(self):
        """Build the base URL for redisplaying the issue summary.

        The form will add fields to this URL to reflect the display
        options selected in the form."""

        redisplay_request = self.request.copy()
        # Blank out the fields that the form will add.
        for field_name in ["fields", "open_only"]:
            if redisplay_request.has_key(field_name):
                del redisplay_request[field_name]
        return redisplay_request.AsUrl()



########################################################################
# functions
########################################################################

def handle_summary(request):
    """Generate the summary page.

    'request' -- A 'WebRequest' object."""

    user = request.GetSession().GetUser()
    idb = qm.track.get_idb()

    if request.has_key("last_query"):
        # Retrieve the last query performed by the user.
        query = user.GetConfigurationProperty("summary_last_query", "1")
    elif request.has_key("query"):
        # Use the query specified in the request.
        query = request["query"]
    else:
        query = "1"

    if query == "1":
        # Trivial query -- get all issues.
        issues = idb.GetIssues()
    else:
        # Run a normal query.
        try:
            issues = []
            # Query all issue classes successively.
            for issue_class in idb.GetIssueClasses():
                issues = issues + idb.Query(query, issue_class.GetName())
        except NameError, name:
            msg = qm.error("query name error", name=name, query=query)
            return qm.web.generate_error_page(request, msg)
        except SyntaxError:
            msg = qm.error("query syntax error", query=query)
            return qm.web.generate_error_page(request, msg)
        except:
            # Don't let other exceptions slip through either.
            exception = sys.exc_info()[1]
            msg = qm.error("query misc error", query=query,
                           error=str(exception))
            return qm.web.generate_error_page(request, msg)

    # Store the query so the user can repeat it easily.
    user.SetConfigurationProperty("summary_last_query", query)

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
            "summary_fields", "iid,summary,state,categories")

    # The request may specify the sort order.  Is it specified?
    if request.has_key("sort"):
        # Yes; use it.
        sort_order = request["sort"]
        # Save it for next time.
        user.SetConfigurationProperty("summary_sort", sort_order)
    else:
        # No.  Retrieve the sort order from the user record, or use a
        # default if it's not listed there.
        sort_order = user.GetConfigurationProperty("summary_sort", "iid")

    # The request may specify that only open issues are to be
    # displayed.  Is the flag specified?
    if request.has_key("open_only"):
        # Yes; use it.
        open_only = int(request["open_only"])
        # Save it for next time.
        user.SetConfigurationProperty("summary_open_only", str(open_only))
    else:
        # No.  Retrieve the state from the user record, or use a default
        # if it's not listed there.
        open_only = int(
            user.GetConfigurationProperty("summary_open_only", 0))

    # Split field names into a sequence.
    field_names = string.split(field_names, ",")
    # Make sure the IID field is in there somewhere.
    if not "iid" in field_names:
        field_names.insert(0, "iid")

    page = SummaryPage(issues, field_names, sort_order, open_only)
    return page(request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

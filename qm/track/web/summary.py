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

    def __init__(self, request, issues):
        """Create a new page.

        'request' -- A 'WebRequest' object containing the page
        request.

        'issues' -- A sequence of issues to summarize."""

        qm.web.PageInfo.__init__(self, request)

        # FIXME: For now, show these fields.
        self.field_names = [ "iid", "summary", "timestamp", "state" ]

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


    def IsLinkToIssue(self, issue, field_name):
        """Return true if the value of this field should link to the issue."""

        return field_name == "iid" or field_name == "summary"


    def MakeIssueUrl(self, issue):
        """Generate a URL to show an individual issue."""

        request = qm.web.WebRequest("show", iid=issue.GetId())
        return qm.web.make_url_for_request(request)



########################################################################
# functions
########################################################################

def handle_summary(request):
    """Generate the summary page.

    'request' -- A 'WebRequest' object."""

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
            return web.generate_error_page(request, msg)
        except SyntaxError:
            msg = """
            %s encountered a syntax error while processing the query
            you specified:

              '%s'
            """ % (qm.track.get_name(), query)
            return web.generate_error_page(request, msg)

    else:
        # No query was specified; show all issues...
        issues = idb.GetIssues()
        # ... that aren't deleted.
        issues = filter(lambda iss: not iss.IsDeleted(), issues)
        
    page_info = SummaryPageInfo(request, issues)
    return web.generate_html_from_dtml("summary.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

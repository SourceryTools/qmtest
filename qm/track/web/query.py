########################################################################
#
# File:   query.py
# Author: Alex Samue,
# Date:   2001-02-21
#
# Contents:
#   Web form for initiating queries.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""Web form for initiating queries.

This form is generated from the DTML template query.dtml."""

########################################################################
# imports
########################################################################

import qm.diagnostic
import qm.track
import qm.web
import web

########################################################################
# classes
########################################################################

class QueryPage(web.DtmlPage):
    """Page for initiating queries."""

    def __init__(self):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "query.dtml")


    def MakeQueryForm(self, form_name):
        """Generate HTML markup to open a query form."""

        request = self.request.copy("summary")
        return request.AsForm(name=form_name)


    def MakePythonQueryHelp(self):
        """Construct a link to popup help about Python queries."""

        # To construct help information about fields in all issue
        # classes, and present this in a way that would make sense to
        # users, would be quite difficult.  For now, we punt and show
        # information only about fields in the default class.
        try:
            default_class = \
                self.request.GetSession().idb.GetDefaultIssueClass()
        except KeyError:
            fields = []
        else:
            fields = default_class.GetFields()

        # First, some general help about Python queries.
        help_text = qm.diagnostic.help_set.Generate("query help")
        help_text = qm.web.format_structured_text(help_text)
        # Append a list of names of fields available in expressions.
        help_text = help_text + '''
        <p>You may use the names listed below in your query to refer to 
        issue field values.  (Note that issues in some issue classes may
        have different fields.)</p>
        <div align="center"><table>
         <thead>
          <tr>
           <th>Field Name</th>
           <th>Value Type</th>
          </tr>
         </thead>
         <tbody>
         '''
        for field in fields:
            description = field.GetTypeDescription()
            description = qm.web.format_structured_text(description)
            help_text = help_text + '''
          <tr valign="top">
           <td><tt>%s</tt></td>
           <td>%s</td>
          </tr>
           ''' % (field.GetName(), description)
        help_text = help_text + '''
         </tbody>
        </table></div>
        '''

        # Construct the help link.
        return qm.web.make_help_link_html(help_text, "Help")


    def MakeCategorySelect(self):
        """Make a list control displaying available categories."""

        # Punt on listing categories for all issue classes.  Show only
        # those for the default issue class.
        try:
            default_class = \
                self.request.GetSession().idb.GetDefaultIssueClass()
        except KeyError:
            return "&nbsp;"
        else:
            field = default_class.GetField("categories")
            categories = field.GetContainedField().GetEnumerals() 
            categories.sort()
            return qm.web.make_select(field_name="category",
                                      form_name="browse_category",
                                      items=categories,
                                      default_value=categories[0]) 
                           

    def MakeStateSelect(self):
        """Make a list control displaying available states."""

        # Punt on listing states for all issue classes.  Show only those
        # for the default issue class.
        try:
            default_class = \
                self.request.GetSession().idb.GetDefaultIssueClass()
        except KeyError:
            return "&nbsp;"
        else:
            field = default_class.GetField("state")
            states = field.GetEnumerals()
            states.sort()
            return qm.web.make_select(field_name="state",
                                      form_name="browse_state",
                                      items=states,
                                      default_value=states[0]) 



########################################################################
# functions
########################################################################

# Nothing to do other than generate the query page.
handle_query = QueryPage()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

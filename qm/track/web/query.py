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

"""Web form for initiating queries.

This form is generated from the DTML template query.dtml."""

########################################################################
# imports
########################################################################

import qm.diagnostic
import qm.track
import qm.track.sql_idb
import qm.web
import web

########################################################################
# classes
########################################################################

class QueryPageInfo(web.PageInfo):
    """DTML context for generating 'query.dtml'."""

    def __init__(self, request):
        # Perform base class initialization.
        web.PageInfo.__init__(self, request)


    def MakeQueryForm(self, name):
        """Construct a form for submitting a query.

        'name' -- The HTML name of the form."""

        request = self.request.copy("summary")
        return request.AsForm(name=name)


    def MakePythonQueryHelp(self):
        """Construct a link to popup help about Python queries."""

        # FIXME: These are only the fields for the default issue class.
        default_class = qm.track.get_default_class()
        fields = default_class.GetFields()

        # First, some general help about Python queries.
        help_text = qm.diagnostic.help_set.Generate("query help")
        help_text = qm.web.format_structured_text(help_text)
        # Append a list of names of fields available in expressions.
        help_text = help_text + '''
        <p>You may use the following names in your query to refer to 
        issue field values:</p>
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

        # FIXME.
        default_class = qm.track.get_default_class()
        field = default_class.GetField("categories")
        categories = field.GetContainedField().GetEnumeration().keys()
        categories.sort()
        return qm.web.make_select(field_name="category",
                                  form_name="browse_category",
                                  items=categories,
                                  default_value=categories[0]) 
                           

    def MakeStateSelect(self):
        """Make a list control displaying available states."""

        # FIXME.
        default_class = qm.track.get_default_class()
        field = default_class.GetField("state")
        states = field.GetEnumeration().keys()
        states.sort()
        return qm.web.make_select(field_name="state",
                                  form_name="browse_state",
                                  items=states,
                                  default_value=states[0]) 



########################################################################
# functions
########################################################################

def handle_query(request):
    """Generate the query page."""

    page_info = QueryPageInfo(request)
    return web.generate_html_from_dtml("query.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

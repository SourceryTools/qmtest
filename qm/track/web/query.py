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
        # Grab the list of fields available in a query.
        # FIXME: For now use, fields of the default class.
        default_class = qm.track.get_default_class()
        self.fields = default_class.GetFields()


    def MakeQueryForm(self):
        request = qm.web.WebRequest("summary")
        return qm.web.make_form_for_request(request)


    def GetFieldTypeDescription(self, field):
        """Return a description of how to use this field."""

        description = qm.track.get_field_type_description_for_query(field)
        return qm.web.format_structured_text(description)
            


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

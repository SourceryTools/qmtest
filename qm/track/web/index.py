########################################################################
#
# File:   index.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Web form for main QMTrack web page.
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

"""Web form for QMTrack menu page."""

########################################################################
# imports
########################################################################

import qm.web
import web

########################################################################
# classes
########################################################################

class IndexPageInfo(web.PageInfo):
    """DTML context for generating DTML template index.dtml."""

    def __init__(self, request):
        # Initialize the base class.
        qm.web.PageInfo.__init__(self, request)

        # Retrieve and store all the issues available in this issue
        # class.
        idb = qm.track.get_idb()
        self.issue_classes = idb.GetIssueClasses()
        # Store the name of the default issue class.
        default_name = qm.track.get_configuration()["default_class"]
        self.default_issue_class = idb.GetIssueClass(default_name)


    def MakeNewForm(self):
        request = self.request.copy("new")
        return qm.web.make_form_for_request(request)


    def MakeShowForm(self):
        request = self.request.copy("show")
        return qm.web.make_form_for_request(request)


    def MakeEditForm(self):
        request = self.request.copy("show")
        request["style"] = "edit"
        return qm.web.make_form_for_request(request)


    def MakeShowAllForm(self):
        request = self.request.copy("summary")
        return qm.web.make_form_for_request(request)


    def MakeQueryForm(self):
        request = self.request.copy("summary")
        return qm.web.make_form_for_request(request)


    def MakeQueryUrl(self):
        request = self.request.copy("query")
        return qm.web.make_url_for_request(request)


    def MakeShutdownForm(self):
        request = self.request.copy("shutdown")
        return qm.web.make_form_for_request(request)


    def MakeLogoutForm(self):
        request = qm.web.WebRequest("logout", base=self.request)
        return qm.web.make_form_for_request(request)



########################################################################
# functions
########################################################################

def handle_index(request):
    """Generate the index page.

    'request' -- A 'WebRequest' object."""

    page_info = IndexPageInfo(request)
    return web.generate_html_from_dtml("index.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

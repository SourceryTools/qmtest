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

import qm.track
import web

########################################################################
# classes
########################################################################

class ShowPageInfo(web.PageInfo):

    def __init__(self, request, issue_class):
        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        self.issue_class = issue_class
        


########################################################################
# functions
########################################################################

def handle_show(request):
    try:
        issue_class_name = request["class"]
    except KeyError:
        msg = "You must specify an issue class name."
        return qm.web.generate_error_page(msg)

    idb = qm.track.get_idb()
    issue_class = idb.GetIssueClass(issue_class_name)

    page_info = ShowPageInfo(request, issue_class)
    return web.generate_html_from_dtml("issue-class.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   suite.py
# Author: Alex Samuel
# Date:   2001-04-20
#
# Contents:
#   Web GUI for editing test suites.
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

import qm.label
import qm.test.base
import qm.web
import string
import web

########################################################################
# classes
########################################################################

class ShowPageInfo(web.PageInfo):

    def __init__(self, request, suite, edit):
        database = qm.test.base.get_database()

        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        # Set up attributes.
        self.suite = suite
        self.test_ids = suite.GetRawTestIds()
        self.suite_ids = suite.GetRawSuiteIds()
        self.edit = edit

        if edit:
            # Find the directory path containing this suite.
            dir_id = qm.label.split(suite.GetId())[0]
            # Construct a list of all test IDs, relative to the suite,
            # that are not explicitly included in the suite.
            excluded = database.GetTestIds(path=dir_id)
            for test_id in self.test_ids:
                if test_id in excluded:
                    excluded.remove(test_id)
            self.excluded_test_ids = excluded
            # Likewise for suite IDs.
            excluded = database.GetSuiteIds(path=dir_id, implicit=1)
            # Don't show the suite as a candidate for inclusion in
            # itself. 
            excluded.remove(suite.GetId())
            for suite_id in self.suite_ids:
                if suite_id in excluded:
                    excluded.remove(suite_id)
            self.excluded_suite_ids = excluded
            # Construct the form-encoded lists of selected test and
            # suite IDs.
            self.encoded_test_ids = string.join(self.test_ids, ",")
            self.encoded_suite_ids = string.join(self.suite_ids, ",")



########################################################################
# functions
########################################################################

def handle_show(request, edit=0):

    database = qm.test.base.get_database()

    try:
        # Determine the suite ID.
        suite_id = request["id"]
    except KeyError:
        # No suite ID was given.
        message = qm.error("no id for show")
        return qm.web.generate_error_page(request, message)

    suite = database.GetSuite(suite_id)
    page_info = ShowPageInfo(request, suite, edit)
    return web.generate_html_from_dtml("suite.dtml", page_info)
    

def handle_edit(request):
    return handle_show(request, edit=1)


def handle_submit(request):
    database = qm.test.base.get_database()

    suite_id = request["id"]
    test_ids = string.split(request["test_ids"], ",")
    suite_ids = string.split(request["suite_ids"], ",")
    suite = qm.test.base.Suite(suite_id, test_ids, suite_ids)
    database.WriteSuite(suite)

    # Redirect to a page that displays the newly-edited item.
    raise qm.web.HttpRedirect, \
          qm.web.make_url("show-suite", id=suite_id)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

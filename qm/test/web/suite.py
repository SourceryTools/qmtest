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
    """DTML context for generating DTML template suite.dtml."""

    def __init__(self, request, suite, edit):
        """Construct a new DTML context.

        'suite' -- The 'Suite' instance to display.

        'edit' -- If true, display controls for editing the suite."""
        
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
            for suite_id in self.suite_ids:
                if suite_id in excluded:
                    excluded.remove(suite_id)
            # Don't show the suite as a candidate for inclusion in
            # itself. 
            self_suite_id = qm.label.split(suite.GetId())[1]
            if self_suite_id in excluded:
                excluded.remove(self_suite_id)
            self.excluded_suite_ids = excluded
            # Construct the form-encoded lists of selected test and
            # suite IDs.
            self.encoded_test_ids = string.join(self.test_ids, ",")
            self.encoded_suite_ids = string.join(self.suite_ids, ",")


    def MakeDeleteScript(self):
        """Make a script to confirm deletion of the suite.

        returns -- JavaScript source for a function, 'delete_script',
        which shows a popup confirmation window."""

        suite_id = self.suite.GetId()
        delete_url = qm.web.make_url("delete-suite",
                                     base_request=self.request,
                                     id=suite_id)
        message = """
        <p>Are you sure you want to delete the suite %s?</p>
        """ % suite_id
        return qm.web.make_confirmation_dialog_script(
            "delete_script", message, delete_url)



class NewPageInfo(web.PageInfo):
    """DTML context for generating DTML template new-suite.dtml."""

    def __init__(self, request, suite_id="", field_errors={}):
        """Create a new DTML context.

        'request' -- A 'WebRequest' object.

        'suite_id' -- Initial value for the new test suite ID field.

        'field_errors' -- A mapping of error messages to fields.  If
        empty, there are no errors."""

        # Initialize the base class.
        web.PageInfo.__init__(self, request)
        # Set up attributes.
        self.suite_id = suite_id
        self.field_errors = field_errors



########################################################################
# functions
########################################################################

def handle_show(request, edit=0):
    """Generate the page for displaying or editing a test suite.

    'request' -- A 'WebRequest' object.

    'edit' -- If true, display the page for editing the suite.
    Otherwise, just display the suite.

    The request has the following fields:

      'id' -- The ID of the suite to display or edit."""

    database = qm.test.base.get_database()

    try:
        # Determine the suite ID.
        suite_id = request["id"]
    except KeyError:
        # No suite ID was given.
        message = qm.error("no id for show")
        return qm.web.generate_error_page(request, message)
    else:
        suite = database.GetSuite(suite_id)
    # Generate HTML.
    page_info = ShowPageInfo(request, suite, edit)
    return web.generate_html_from_dtml("suite.dtml", page_info)
    

def handle_edit(request):
    """Generate the page for editing a test suite."""
    
    return handle_show(request, edit=1)


def handle_submit(request):
    """Handle a test suite edit submission.

    'request' -- A 'WebRequest' object.

    The request object has these fields:

      'id' -- The ID of the test suite being edited.  If a suite with
      this ID exists, it is replaced (it must not be an implicit suite
      though).  Otherwise a new suite is edited.

      'test_ids' -- A comma-separated list of test IDs to include in the
      suite, relative to the suite's own ID.

      'suite_ids' -- A comma-separated list of other test suite IDs to
      include in the suite, relative to the suite's own ID.
    """

    database = qm.test.base.get_database()
    # Extract fields from the request.
    suite_id = request["id"]
    test_ids = request["test_ids"]
    if string.strip(test_ids) == "":
        test_ids = []
    else:
        test_ids = string.split(test_ids, ",")
    suite_ids = request["suite_ids"]
    if string.strip(suite_ids) == "":
        suite_ids = []
    else:
        suite_ids = string.split(suite_ids, ",")
    # Construct a new suite.
    suite = qm.test.base.Suite(suite_id, test_ids, suite_ids)
    # Store it.
    database.WriteSuite(suite)
    # Redirect to a page that displays the newly-edited item.
    raise qm.web.HttpRedirect, \
          qm.web.make_url("show-suite", id=suite_id)


def handle_new(request):
    """Handle a request for the new test suite page.

    'request' -- A 'WebRequest' object."""

    page_info = NewPageInfo(request)
    return web.generate_html_from_dtml("new-suite.dtml", page_info)


def handle_create(request):
    """Handle a submission of a new test suite.

    'request' -- A 'WebRequest' object."""

    field_errors = {}
    database = qm.test.base.get_database()

    # Extract the suite ID of the new suite from the request.
    suite_id = request["id"]
    # Check that the ID is valid.
    try:
        qm.test.base.validate_id(suite_id)
    except RuntimeError, diagnostic:
        field_errors["_id"] = diagnostic
    else:
        # Check that the ID doesn't already exist.
        if database.HasSuite(suite_id):
            field_errors["_id"] = qm.error("suite already exists",
                                           suite_id=suite_id)
    
    # Were there any validation errors?
    if len(field_errors) > 0:
        # Yes.  Instead of showing the page for editing the suite,
        # redisplay the new suite page with error messages.
        page_info = NewPageInfo(request, suite_id, field_errors)
        return web.generate_html_from_dtml("new-suite.dtml", page_info)
    else:
        # Everything looks good.  Make an empty test.
        suite = qm.test.base.Suite(suite_id)
        # Show the editing page.
        page_info = ShowPageInfo(request, suite, edit=1)
        return web.generate_html_from_dtml("suite.dtml", page_info)


def handle_delete(request):
    """Handle delete requests.

    'request' -- A 'WebRequest' object.

    The ID of the suite to delete is specified in the 'id' field of the
    request."""

    database = qm.test.base.get_database()
    # Extract the suite ID.
    suite_id = request["id"]
    database.RemoveSuite(suite_id)
    # Redirect to the main page.
    request = qm.web.WebRequest("dir", base=request)
    raise qm.web.HttpRedirect, qm.web.make_url_for_request(request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

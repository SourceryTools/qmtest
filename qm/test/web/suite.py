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

class ShowPage(web.DtmlPage):
    """Page for displaying the contents of a test suite."""

    def __init__(self, suite, edit):
        """Construct a new DTML context.

        'suite' -- The 'Suite' instance to display.

        'edit' -- If true, display controls for editing the suite."""
        
        database = qm.test.base.get_database()

        # Initialize the base class.
        web.DtmlPage.__init__(self, "suite.dtml")
        # Set up attributes.
        self.suite = suite
        self.test_ids = suite.GetTestIds()
        self.suite_ids = suite.GetSuiteIds()
        self.edit = edit

        if not suite.IsImplicit():
            self.edit_menu_items.append(("Edit Suite", "edit_isuite();"))
            self.edit_menu_items.append(("Delete Suite", "delete_suite();"))

        if not edit:
            self.run_menu_items.append(("This Suite", "run_suite();"))
            
        if edit:
            # Find the directory path containing this suite.
            dir_id = qm.label.split(suite.GetId())[0]

            # Construct a list of all test IDs, relative to the suite,
            # that are not explicitly included in the suite.
            excluded_test_ids = database.GetTestIds(dir_id)
            for test_id in self.test_ids:
                if test_id in excluded_test_ids:
                    excluded_test_ids.remove(test_id)
            # Make controls for adding or removing test IDs.
            self.test_id_controls = qm.web.make_choose_control(
                "test_ids",
                "Included Tests",
                self.test_ids,
                "Available Tests",
                excluded_test_ids)

            # Likewise for suite IDs.
            excluded_suite_ids = database.GetSuiteIds(dir_id)
            for suite_id in self.suite_ids:
                if suite_id in excluded_suite_ids:
                    excluded_suite_ids.remove(suite_id)
            # Don't show the suite as a candidate for inclusion in
            # itself. 
            self_suite_id = qm.label.split(suite.GetId())[1]
            if self_suite_id in excluded_suite_ids:
                excluded_suite_ids.remove(self_suite_id)
            # Make controls for adding or removing suite IDs.
            self.suite_id_controls = qm.web.make_choose_control(
                "suite_ids",
                "Included Suites",
                self.suite_ids,
                "Available Suites",
                excluded_suite_ids)


    def MakeAbsoluteId(self, raw_id):
        return qm.label.join(self.suite.GetId(), raw_id)


    def MakeEditUrl(self):
        """Return the URL for editing this suite."""

        return qm.web.WebRequest("edit-suite",
                                 base=self.request,
                                 id=self.suite.GetId()) \
               .AsUrl()

        
    def MakeRunUrl(self):
        """Return the URL for running this suite."""

        return qm.web.WebRequest("run-tests",
                                 base=self.request,
                                 ids=self.suite.GetId()) \
               .AsUrl()

    
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
        return qm.web.make_confirmation_dialog(message, delete_url)



class NewPage(web.DtmlPage):
    """Page for creating a new test suite."""

    def __init__(self, suite_id="", field_errors={}):
        """Create a new DTML context.

        'request' -- A 'WebRequest' object.

        'suite_id' -- Initial value for the new test suite ID field.

        'field_errors' -- A mapping of error messages to fields.  If
        empty, there are no errors."""

        # Initialize the base class.
        web.DtmlPage.__init__(self, "new-suite.dtml")
        # Set up attributes.
        self.suite_id = suite_id
        self.field_errors = field_errors



########################################################################
# functions
########################################################################

# Nothing to do besides generating the page.
handle_new = NewPage()


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
    return ShowPage(suite, edit)(request)
    

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
    suite = qm.test.base.Suite(suite_id,
                               test_ids=test_ids,
                               suite_ids=suite_ids)
    # Store it.
    database.WriteSuite(suite)
    # Redirect to a page that displays the newly-edited item.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-suite", base=request, id=suite_id)


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
        return NewPage(suite_id, field_errors)(request)
    else:
        # Everything looks good.  Make an empty test.
        suite = qm.test.base.Suite(suite_id)
        # Show the editing page.
        return ShowPage(suite, edit=1)(request)


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
    raise qm.web.HttpRedirect, qm.web.WebRequest("dir", base=request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

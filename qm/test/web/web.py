########################################################################
#
# File:   web.py
# Author: Alex Samuel
# Date:   2001-04-09
#
# Contents:
#   Common code for QMTest web user interface.
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

import os
import qm
import qm.attachment
from   qm.test.result import *
from   qm.test.result_stream import *
from   qm.test.xml_result_stream import *
import qm.web
import string
import StringIO

########################################################################
# classes
########################################################################

class DefaultDtmlPage(qm.web.DtmlPage):
    """Subclass of DTML page class for QMTest pages."""

    html_generator = "QMTest"


    def __init__(self, dtml_template, **attributes):
        # Set up the menus first; the attributes might override them.
        self.file_menu_items = [
            ('New Test', "location = 'new-test';"),
            ('New Suite', "location = 'new-suite';"),
            ('New Resource', "location = 'new-resource';"),
            ('Load Results', "load_results();"),
            ('Save Results', "location = 'save-results';"),
            ('Load Expectations', "load_expected_results();"),
            ('Save Expectations', "location = 'save-expectations';"),
            ('Exit', 'shutdown')
            ]
        self.edit_menu_items = [
            ('Edit Context', "location = 'edit-context';"),
            ('Edit Expectations', "location = 'edit-expectations';")
            ]
        self.view_menu_items = [
            ('View Results', "location = 'show-results';")
            ]
        self.run_menu_items = [
            ('All Tests', "location = 'run-tests';")
            ]

        # Initialize the base class.
        apply(qm.web.DtmlPage.__init__, (self, dtml_template), attributes)


    def GetName(self):
        """Return the name of the application."""

        return self.html_generator


    def MakeListingUrl(self):
        return qm.web.WebRequest("dir", base=self.request).AsUrl()


    def GenerateStartBody(self, decorations=1):
        if decorations:
            # Include the navigation bar.
            navigation_bar = DtmlPage("navigation-bar.dtml",
                                      file_menu_items=self.file_menu_items,
                                      edit_menu_items=self.edit_menu_items,
                                      view_menu_items=self.view_menu_items,
                                      run_menu_items=self.run_menu_items)
            return "<body>%s<br>" % navigation_bar(self.request)
        else:
            return "<body>"


    def GetMainPageUrl(self):
        return self.MakeListingUrl()


    def FormatId(self, id, type, style="basic"):
        script = "show-" + type
        request = qm.web.WebRequest(script, base=self.request, id=id)
        url = request.AsUrl()
        parent_suite_id, name = qm.label.split(id)
        if name == "":
            name = "."
            
        if style == "plain":
            return '<span class="id">%s</span>' % id

        elif style == "basic":
            return '<a href="%s"><span class="id">%s</span></a>' % (url, id)

        elif style == "navigation":
            if parent_suite_id == qm.label.root:
                parent = ""
            else:
                parent = self.FormatId(parent_suite_id, "dir", style) \
                         + qm.label.sep
            return parent \
                   + '<a href="%s"><span class="id">%s</span></a>' \
                   % (url, name)

        elif style == "tree":
            return '<a href="%s"><span class="id">%s</span></a>' \
                   % (url, name)

        else:
            assert style



class DtmlPage(DefaultDtmlPage):
    """Convenience DTML subclass that finds QMTest page templates.

    Use this 'DtmlPage' subclass for QMTest-specific pages.  This class
    automatically looks for template files in the 'test' subdirectory."""

    def __init__(self, dtml_template, **attributes):
        # QMTest DTML templates are in the 'test' subdirectory.
        dtml_template = os.path.join("test", dtml_template)
        # Initialize the base class.
        apply(DefaultDtmlPage.__init__, (self, dtml_template), attributes)



class AddPrerequisitePage(DtmlPage):
    """Page for specifying a prerequisite test to add."""

    outcomes = Result.outcomes
    """The list of possible test outcomes."""


    def __init__(self, base_path):
        # Initialize the base class.
        DtmlPage.__init__(self, "add-prerequisite.dtml")
        # Extract a list of all test IDs in the specified path. 
        db = qm.test.base.get_database()
        test_ids = db.GetTestIds(base_path)
        test_ids.sort()
        # Store it for the DTML code.
        self.test_ids = test_ids



class AddResourcePage(DtmlPage):
    """Page for specifying an resource to add."""

    def __init__(self, resource_path):
        # Initialize the base class.
        DtmlPage.__init__(self, "add-resource.dtml")
        # Extract a list of all resource IDs in the specified path.
        db = qm.test.base.get_database()
        resource_ids = db.GetResourceIds(resource_path)
        resource_ids.sort()
        # Store it for the DTML code.
        self.resource_ids = resource_ids
        


class ContextPage(DtmlPage):
    """DTML page for setting the context."""

    def __init__(self, server):
        """Construct a new 'ContextPage'.

        'server' -- The 'QMTestServer' creating this page."""

        DtmlPage.__init__(self, "context.dtml")
        
        self.__server = server
        self.context = server.GetContext()
        


class DirPage(DtmlPage):
    """A test database directory page.

    These attributes are available in DTML:

    'path' -- The label directory that is being displayed.

    'subdirs' -- A sequence of labels giving the subdirectories of
    this directory.
    
    'test_ids' -- A sequence of labels giving the tests in this
    directory.
    
    'suite_ids' -- A sequence of labels giving the suites in this
    directory.

    'resource_ids' -- A sequence of labels giving the resources in
    this directory."""

    def __init__(self, path):
        """Construct a 'DirPage'.

        'path' -- The label directory to display."""
        
        # Initialize the base class.
        DtmlPage.__init__(self, "dir.dtml")
        
        database = qm.test.base.get_database()

        self.path = path
        self.subdir_ids = database.GetSubdirectories(path)
        self.subdir_ids = map(qm.label.AsAbsolute(path), self.subdir_ids)
        self.test_ids = database.GetTestIds(path, scan_subdirs=0)
        self.suite_ids = database.GetSuiteIds(path, scan_subdirs=0)
        self.resource_ids = database.GetResourceIds(path, scan_subdirs=0)

        # We include the root testsuite in the root directory, as
        # a special case.
        if path == qm.label.sep:
            self.suite_ids = [ "." ] + self.suite_ids



class ExpectationsPage(DtmlPage):
    """DTML page for editing expected outcomes."""

    def __init__(self, server):
        """Construct a new 'ExpectationsPage'.

        'server' -- The 'QMTestServer' creating this page."""

        DtmlPage.__init__(self, "expectations.dtml")
        
        self.__server = server
        self.expected_outcomes = server.GetExpectedOutcomes()
        self.outcomes = Result.outcomes
        self.test_ids = qm.test.base.expand_ids(".")[0]
        self.test_ids.sort()

        
class LoadExpectedResultsPage(DtmlPage):
    """DTML page for uploading expected results."""

    def __init__(self):
        """Construct a new 'LoadExpectedResultsPage'."""

        DtmlPage.__init__(self, "load-expected-results.dtml")



class LoadResultsPage(DtmlPage):
    """DTML page for uploading results."""

    def __init__(self):
        """Construct a new 'LoadResultsPage'."""

        DtmlPage.__init__(self, "load-results.dtml")


        
class NewItemPage(DtmlPage):
    """Page for creating a new test or resource."""

    def __init__(self,
                 type,
                 item_id="",
                 class_name="",
                 field_errors={}):
        """Create a new DTML context.

        'type' -- Either "test" or "resource".

        'item_id' -- The item ID to show.

        'class_name' -- The class name to show.

        'field_errors' -- A mapping of error messages for fields.  Keys
        may be "_id" or "_class"."""

        # Initialize the base class.
        DtmlPage.__init__(self, "new.dtml")
        # Set up attributes.
        assert type in ["test", "resource"]
        self.type = type
        self.item_id = item_id
        self.class_name = class_name
        if type == "test":
            self.class_names = qm.test.base.get_database().GetTestClasses()
        elif type == "resource":
            self.class_names = qm.test.base.get_database().GetResourceClasses()
        self.field_errors = field_errors


    def GetTitle(self):
        """Return the title this page."""

        return "Create a New %s" % string.capwords(self.type)


    def MakeSubmitUrl(self):
        """Return the URL for submitting the form.

        The URL is for the script 'create-test' or 'create-resource' as
        appropriate."""

        return qm.web.WebRequest("create-" + self.type,
                                 base=self.request) \
               .AsUrl()



class NewSuitePage(DtmlPage):
    """Page for creating a new test suite."""

    def __init__(self, suite_id="", field_errors={}):
        """Create a new DTML context.

        'request' -- A 'WebRequest' object.

        'suite_id' -- Initial value for the new test suite ID field.

        'field_errors' -- A mapping of error messages to fields.  If
        empty, there are no errors."""

        # Initialize the base class.
        DtmlPage.__init__(self, "new-suite.dtml")
        # Set up attributes.
        self.suite_id = suite_id
        self.field_errors = field_errors


class ResultPage(DtmlPage):
    """DTML page for showing result detail."""

    def __init__(self, result):
        """Construct a new 'ResultPage'

        'result' -- The result to display."""

        DtmlPage.__init__(self, "result.dtml")
        self.result = result
        
        
class ShowItemPage(DtmlPage):
    """DTML page for showing and editing tests and resources."""

    def __init__(self, item, edit, new, type, field_errors={}):
        """Construct a new DTML context.
        
        These parameters are also available in DTML under the same name:

        'item' -- The 'Test' or 'Resource' instance.

        'edit' -- True for editing the item; false for displaying it
        only.

        'new' -- True for editing a newly-created item ('edit' is then
        also true).

        'type' -- Either "test" or "resource".

        'field_errors' -- A map from field names to corresponding error
        messages.  The values "_prerequisites", "_resources", and
        "_categories" may also be used as keys."""

        # Initialize the base class.
        DtmlPage.__init__(self, "show.dtml")
        # Set up attributes.
        self.item = item
        self.fields = item.GetClass().arguments
        self.edit = edit
        self.new = new
        assert type in ["test", "resource"]
        self.type = type
        self.field_errors = field_errors

        self.edit_menu_items.append(("Edit %s" % string.capitalize(type),
                                     "edit_item();"))
        self.edit_menu_items.append(("Delete %s" % string.capitalize(type),
                                     "delete_item();"))

        if type == "test" and not edit:
            self.run_menu_items.append(("This Test", "run_test();"))
        
        # Some extra attributes that don't apply to resources.
        if self.type is "test":
            self.prerequisites = item.GetPrerequisites()
            self.resources = item.GetResources()
            self.categories = item.GetCategories()


    def GetTitle(self):
        """Return the page title for this page."""

        # Map the scriptname to a nicely-formatted title.
        url = self.request.GetScriptName()
        title = {
            "show-test":       "Show Test",
            "edit-test":       "Edit Test",
            "create-test":     "New Test",
            "show-resource":   "Show Resource",
            "edit-resource":   "Edit Resource",
            "create-resource": "New Resource",
            }[url]
        # Show the item's ID too.
        title = title + " " + self.item.GetId()
        return title


    def FormatFieldValue(self, field):
        """Return an HTML rendering of the value for 'field'."""

        # Extract the field value.
        arguments = self.item.GetArguments()
        field_name = field.GetName()
        try:
            value = arguments[field_name]
        except KeyError:
            # Use the default value if none is provided.
            value = field.GetDefaultValue()
        # Format it appropriately.
        if self.edit:
            if field.IsProperty("hidden"):
                return field.FormatValueAsHtml(value, "hidden")
            elif field.IsProperty("read_only"):
                # For read-only fields, we still need a form input, but
                # the user shouldn't be able to change anything.  Use a
                # hidden input, and display the contents as if this
                # wasn't an editing form.
                return field.FormatValueAsHtml(value, "hidden") \
                       + field.FormatValueAsHtml(value, "full")
            else:
                return field.FormatValueAsHtml(value, "edit")
        else:
            return field.FormatValueAsHtml(value, "full")


    def GetClassDescription(self):
        """Return a full description of the test or resource class.

        returns -- The description, formatted as HTML."""

        # Extract the class's doc string.
        doc_string = self.item.GetClass().__doc__
        if doc_string is not None:
            return qm.web.format_structured_text(doc_string)
        else:
            return "&nbsp;"


    def GetBriefClassDescription(self):
        """Return a brief description of the test or resource class.

        returns -- The brief description, formatted as HTML."""

        # Extract the class's doc string.
        doc_string = self.item.GetClass().__doc__
        if doc_string is not None:
            doc_string = qm.structured_text.get_first(doc_string)
            return qm.web.format_structured_text(doc_string)
        else:
            return "&nbsp;"


    def MakeEditUrl(self):
        """Return the URL for editing this item."""

        return qm.web.WebRequest("edit-" + self.type,
                                 base=self.request,
                                 id=self.item.GetId()) \
               .AsUrl()

        
    def MakeRunUrl(self):
        """Return the URL for editing this item."""

        return qm.web.WebRequest("run-tests",
                                 base=self.request,
                                 ids=self.item.GetId()) \
               .AsUrl()


    def MakeShowUrl(self):
        """Return the URL for showing this item."""

        return qm.web.WebRequest("show-" + self.type,
                                 base=self.request,
                                 id=self.item.GetId()) \
               .AsUrl()


    def MakeSubmitUrl(self):
        """Return the URL for submitting edits."""

        return self.request.copy("submit-" + self.type).AsUrl()


    def MakePrerequisitesControl(self):
        """Make controls for editing test prerequisites."""

        # Encode the current prerequisites.  The first element of each
        # option is user-visible; the second is the option value which
        # we can parse back later.
        options = []
        for test_id, outcome in self.prerequisites.items():
            options.append(("%s (%s)" % (test_id, outcome),
                            "%s;%s" % (test_id, outcome)))
        # Generate the page for selecting the prerequisite test to add.
        test_path = qm.label.dirname(self.item.GetId())
        add_page = AddPrerequisitePage(test_path)(self.request)
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="prerequisites",
                                       select_name="_set_prerequisites",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=480)


    def MakeResourcesControl(self):
        """Make controls for editing the resources associated with a test."""

        # Encode the current resource values.
        options = map(lambda ac: (ac, ac), self.resources)
        # Generate the page for selecting the resource to add.
        test_path = qm.label.dirname(self.item.GetId())
        add_page = AddResourcePage(test_path)(self.request)
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="resources",
                                       select_name="_set_resources",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=360)


    def MakeCategoriesControl(self):
        """Make controls for editing a test's categories."""

        # Encode the current categories.
        options = map(lambda cat: (cat, cat), self.categories)
        # Generate the page for selecting the category to add.
        add_page = DtmlPage("add-category.dtml")
        add_page = add_page(self.request) 
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="categories",
                                       select_name="_set_categories",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=240)


    def MakeDeleteScript(self):
        """Make a script to confirm deletion of the test or resource.

        returns -- JavaScript source to handle deletion of the
        test or resource."""

        item_id = self.item.GetId()
        delete_url = qm.web.make_url("delete-" + self.type,
                                     base_request=self.request,
                                     id=item_id)
        message = """
        <p>Are you sure you want to delete the %s %s?</p>
        """ % (self.type, item_id)
        return qm.web.make_confirmation_dialog(message, delete_url)



class ShowSuitePage(DtmlPage):
    """Page for displaying the contents of a test suite."""

    def __init__(self, suite, edit):
        """Construct a new DTML context.

        'suite' -- The 'Suite' instance to display.

        'edit' -- If true, display controls for editing the suite."""
        
        database = qm.test.base.get_database()

        # Initialize the base class.
        DtmlPage.__init__(self, "suite.dtml")
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



class StorageResultsStream(ResultStream):
    """A 'StorageResultsStream' stores results.

    A 'StorageResultsStream' does not write any output.  It simply
    stores the results for future display."""

    def __init__(self):
        """Construct a 'StorageResultsStream'."""

        ResultStream.__init__(self)
        self.test_results = {}
        self.resource_results = {}
        

    def WriteResult(self, result):
        """Output a test result.

        'result' -- A 'Result'."""

        if result.GetKind() == Result.TEST:
            self.test_results[result.GetId()] = result
        else:
            self.resource_results[result.GetId()] = result

            

class TestResultsPage(DtmlPage):
    """DTML page for displaying test results."""

    def __init__(self, test_results, expected_outcomes):
        """Construct a new 'TestResultsPage'.

        'test_results' -- A map from test IDs to 'Result' objects.

        'expected_outcomes' -- A map from test IDs to outcomes."""
        
        # Initialize the base classes.
        DtmlPage.__init__(self, "results.dtml")

        self.test_results = test_results
        self.expected_outcomes = expected_outcomes
        

    def Summarize(self):
        """Output summary information about the results.

        When this method is called, the test run is complete.  Summary
        information should be displayed for the user, if appropriate.
        Any finalization, such as the closing of open files, should
        also be performed at this point."""

        ResultStream.Summarize(self)

      
    def FormatResult(self, result):
         """Return HTML for displaying a test result.

         'result' -- A 'Result'.

         returns -- HTML displaying the result."""

         text = result.AsStructuredText("full")
         return qm.structured_text.to_html(text)

         
    def GetClassForResult(self, result):
        """Return the CSS class for displaying a 'result'.

        returns -- The name of a CSS class.  These are used with <span>
        elements.  See 'qm.css'."""

        outcome = result.GetOutcome()
        return {
            Result.PASS: "pass",
            Result.FAIL: "fail",
            Result.UNTESTED: "untested",
            Result.ERROR: "error",
            }[outcome]


    def GetOutcomes(self):
        """Return the list of result outcomes.

        returns -- A sequence of result outcomes."""

        return Result.outcomes


    def GetTotal(self):
        """Return the total number of tests.

        returns -- The total number of tests."""

        return len(self.test_results)


    def GetTotalUnexpected(self):
        """Return the total number of unexpected results.

        returns -- The total number of unexpected results."""

        return len(self.GetRelativeResults(self.test_results.values(),
                                           0))


    def GetResultsWithOutcome(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The results with the given 'outcome'."""

        return filter(lambda r, o=outcome: r.GetOutcome() == o,
                          self.test_results.values())
    
        
    def GetCount(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The number of tests with the given 'outcome'."""

        return len(self.GetResultsWithOutcome(outcome))


    def GetUnexpectedCount(self, outcome):
        """Return the number of tests with the given 'outcome'.

        'outcome' -- One of the 'Result.outcomes'.

        returns -- The number of tests with the given 'outcome' that
        were expected to have some other outcome."""

        results = self.GetResultsWithOutcome(outcome)
        results = self.GetRelativeResults(results, 0)
        return len(results)

    
    def GetTestIds(self, expected):
        """Return a sequence of test IDs whose results are to be shown.

        returns -- The test ids for tests whose outcome is as expected,
        if 'expected' is true, or unexpected, if 'expected' is false."""

        results = self.GetRelativeResults(self.test_results.values(),
                                          expected)
        return map(lambda r: r.GetId(), results)


    def GetRelativeResults(self, results, expected):
        """Return the results that match, or fail to match, expectations.

        'results' -- A sequence of 'Result' objects.

        'expected' -- A boolean.  If true, expected results are
        returned.  If false, unexpected results are returned."""

        if expected:
            return filter(lambda r, er=self.expected_outcomes: \
                              r.GetOutcome() == er.get(r.GetId(),
                                                        Result.PASS),
                          results)
        else:
            return filter(lambda r, er=self.expected_outcomes: \
                              r.GetOutcome() != er.get(r.GetId(),
                                                        Result.PASS),
                          results)


    def GetDetailUrl(self, test_id):
        """Return the detail URL for a test.

        'test_id' -- The name of the test.

        returns -- The URL that contains details about the 'test_id'."""

        return qm.web.WebRequest("show-result",
                                 base = self.request,
                                 id=test_id).AsUrl()


    
class QMTestServer(qm.web.WebServer):
    """A 'QMTestServer' is the web GUI interface to QMTest."""

    def __init__(self, database, port, address, log_file=None):
        """Create and bind an HTTP server.

        'database' -- The test database to serve.

        'port' -- The port number on which to accept HTTP requests.

        'address' -- The local address to which to bind the server.  An
        empty string indicates all local addresses.

        'log_file' -- A file object to which the server will log requests.
        'None' for no logging.

        returns -- A web server.  The server is bound to the specified
        address.  Call its 'Run' method to start accepting requests."""

        qm.web.WebServer.__init__(self, port, address, log_file=log_file)

        # Base URL path for QMTest stuff.
        script_base = "/test/"
        # Register all our web pages.
        for name, function in [
            ( "create-resource", self.HandleShowItem ),
            ( "create-suite", self.HandleCreateSuite ),
            ( "create-test", self.HandleShowItem ),
            ( "delete-resource", self.HandleDeleteItem ),
            ( "delete-suite", self.HandleDeleteSuite ),
            ( "delete-test", self.HandleDeleteItem ),
            ( "dir", self.HandleDir ),
            ( "edit-context", self.HandleEditContext ),
            ( "edit-expectations", self.HandleEditExpectations ),
            ( "edit-resource", self.HandleShowItem ),
            ( "edit-suite", self.HandleEditSuite ),
            ( "edit-test", self.HandleShowItem ),
            ( "load-expected-results", self.HandleLoadExpectedResults ),
            ( "load-results", self.HandleLoadResults ),
            ( "new-resource", self.HandleNewResource ),
            ( "new-suite", self.HandleNewSuite ),
            ( "new-test", self.HandleNewTest ),
            ( "run-tests", self.HandleRunTests ),
            ( "save-expectations", self.HandleSaveExpectations ),
            ( "save-results", self.HandleSaveResults ),
            ( "show-dir", self.HandleDir ),
            ( "show-resource", self.HandleShowItem ),
            ( "show-result", self.HandleShowResult ),
            ( "show-results", self.HandleShowResults ),
            ( "show-suite", self.HandleShowSuite ),
            ( "show-test", self.HandleShowItem ),
            ( "shutdown", self.HandleShutdown ),
            ( "submit-context", self.HandleSubmitContext ),
            ( "submit-resource", self.HandleSubmitItem ),
            ( "submit-expectations", self.HandleSubmitExpectations ),
            ( "submit-expectations-form", self.HandleSubmitExpectationsForm ),
            ( "submit-results", self.HandleSubmitResults ),
            ( "submit-suite", self.HandleSubmitSuite ),
            ( "submit-test", self.HandleSubmitItem ),
            ]:
            self.RegisterScript(script_base + name, function)
        self.RegisterPathTranslation(
            "/stylesheets", qm.get_share_directory("web", "stylesheets"))
        self.RegisterPathTranslation(
            "/images", qm.get_share_directory("web", "images"))
        self.RegisterPathTranslation(
            "/static", qm.get_share_directory("web", "static"))
        # Register the QM manual.
        self.RegisterPathTranslation(
            "/manual", qm.get_doc_directory("manual", "html"))

        # The global temporary attachment store processes attachment data
        # uploads.
        temporary_attachment_store = qm.attachment.temporary_store
        self.RegisterScript(qm.fields.AttachmentField.upload_url,
                            temporary_attachment_store.HandleUploadRequest)
        # The DB's attachment store processes download requests for
        # attachment data.
        attachment_store = database.GetAttachmentStore()
        self.RegisterScript(qm.fields.AttachmentField.download_url,
                            attachment_store.HandleDownloadRequest)

        # Create an empty context.
        self.__context = qm.test.base.Context()

        # There are no results yet.
        self.__expected_outcomes = {}
        self.__results_stream = StorageResultsStream()

        # Bind the server to the specified address.
        try:
            self.Bind()
        except qm.web.AddressInUseError, address:
            raise RuntimeError, qm.error("address in use", address=address)
        except qm.web.PrivilegedPortError:
            raise RuntimeError, qm.error("privileged port", port=port)


    def GetContext(self):
        """Return the 'Context' in which tests will be run.

        returns -- The 'Context' in which tests will be run."""

        return self.__context

    
    def GetExpectedOutcomes(self):
        """Return the current expected outcomes for the test database.

        returns -- A map from test IDs to outcomes.  Some tests may have
        not have an entry in the map."""

        return self.__expected_outcomes


    def HandleCreateSuite(self, request):
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
            return NewSuitePage(suite_id, field_errors)(request)
        else:
            # Everything looks good.  Make an empty test.
            suite = qm.test.base.Suite(suite_id)
            # Show the editing page.
            return ShowSuitePage(suite, edit=1)(request)


    def HandleDeleteItem(self, request):
        """Handle a request to delete a test or resource.

        This function handles the script requests 'delete-test' and
        'delete-resource'.

        'request' -- A 'WebRequest' object.

        The ID of the test or resource to delete is specified in the 'id'
        field of the request."""

        database = qm.test.base.get_database()
        # Extract the item ID.
        item_id = request["id"]
        # The script name determines whether we're deleting a test or an
        # resource. 
        script_name = request.GetScriptName()
        if script_name == "delete-test":
            database.RemoveTest(item_id)
        elif script_name == "delete-resource":
            database.RemoveResource(item_id)
        else:
            raise RuntimeError, "unrecognized script name"
        # Redirect to the main page.
        request = qm.web.WebRequest("dir", base=request)
        raise qm.web.HttpRedirect, request


    def HandleDeleteSuite(self, request):
        """Handle a request to delete a test suite.

        'request' -- A 'WebRequest' object.

        The ID of the suite to delete is specified in the 'id' field of the
        request."""

        database = qm.test.base.get_database()
        # Extract the suite ID.
        suite_id = request["id"]
        database.RemoveSuite(suite_id)
        # Redirect to the main page.
        raise qm.web.HttpRedirect, qm.web.WebRequest("dir", base=request)


    def HandleDir(self, request):
        """Generate a directory page.

        'request' -- A 'WebRequest' object.

        The request has these fields:

        'path' -- A path in test/resource/suite ID space.  If specified,
        only tests and resources in this subtree are displayed, and their
        IDs are displayed relative to this path.  If omitted, the entire
        contents of the test database are shown."""

        path = request.get("id", ".")
        return DirPage(path)(request)


    def HandleEditContext(self, request):
        """Handle a request to edit the context.

        'request' -- The 'WebRequest' that caused the event."""

        context_page = ContextPage(self)
        return context_page(request)
        

    def HandleEditExpectations(self, request):
        """Handle a request to edit the context.

        'request' -- The 'WebRequest' that caused the event."""

        return ExpectationsPage(self)(request)


    def HandleEditSuite(self, request):
        """Generate the page for editing a test suite."""

        return self.HandleShowSuite(request, edit=1)


    def HandleLoadExpectedResults(self, request):
        """Handle a request to upload results.
        
        'request' -- The 'WebRequest' that caused the event."""

        return LoadExpectedResultsPage()(request)

        
    def HandleLoadResults(self, request):
        """Handle a request to upload results.
        
        'request' -- The 'WebRequest' that caused the event."""

        return LoadResultsPage()(request)


    def HandleNewResource(self, request):
        """Handle a request to create a new test.

        'request' -- The 'WebRequest' that caused the event."""

        return NewItemPage(type="resource")(request)


    def HandleNewTest(self, request):
        """Handle a request to create a new test.

        'request' -- The 'WebRequest' that caused the event."""

        return NewItemPage(type="test")(request)


    def HandleNewSuite(self, request):
        """Handle a request to create a new suite.

        'request' -- The 'WebRequest' that caused the event."""

        return NewSuitePage()(request)


    def HandleRunTests(self, request):
        """Handle a request to run tests.

        'request' -- The 'WebRequest' that caused the event.

        These fields in 'request' are used:

          'ids' -- A comma-separated list of test and suite IDs.  These IDs
          are expanded into the list of IDs of tests to run.

        """
        
        # Extract and expand the IDs of tests to run.
        if request.has_key("ids"):
            ids = string.split(request["ids"], ",")
        else:
            ids = ["."]
        test_ids, suite_ids = qm.test.base.expand_ids(ids)

        context = self.__context
        # Run in a single local subprocess.  As yet, we don't support
        # target configuration when running tests from the web GUI.
        target_specs = [
            qm.test.run.TargetSpec("local",
                                   "qm.test.run.SubprocessTarget",
                                   "",
                                   1,
                                   {}),
            ]

        # Flush existing results.
        self.__results_stream = StorageResultsStream()
        # Run the tests.
        qm.test.run.test_run(test_ids, self.__context, target_specs,
                             [self.__results_stream])

        # Display the results.
        return self.HandleShowResults(request)


    def HandleSaveExpectations(self, request):
        """Handle a request to save expectations to a file.

        'request' -- The 'WebRequest' that caused the event."""
        
        # Create a string stream to store the results.
        s = StringIO.StringIO()
        # Create an XML results stream for storing the results.
        rs = XMLResultStream(s)
        # Write all the results.
        for (id, outcome) in self.__expected_outcomes.items():
            r = Result(Result.TEST, id, qm.test.base.Context(),
                       outcome)
            rs.WriteResult(r)
        # Terminate the stream.
        rs.Summarize()
        # Extract the data.
        data = s.getvalue()
        # Close the stream.
        s.close()
        
        return ("application/x-qmtest-results", data)
        

    def HandleSaveResults(self, request):
        """Handle a request to save results to a file.

        'request' -- The 'WebRequest' that caused the event."""

        # Create a string stream to store the results.
        s = StringIO.StringIO()
        # Create an XML results stream for storing the results.
        rs = XMLResultStream(s)
        # Write all the results.
        for r in self.__results_stream.test_results.values():
            rs.WriteResult(r)
        for r in self.__results_stream.resource_results.values():
            rs.WriteResult(r)
        # Terminate the stream.
        rs.Summarize()
        # Extract the data.
        data = s.getvalue()
        # Close the stream.
        s.close()
        
        return ("application/x-qmtest-results", data)
    
                
    def HandleShowItem(self, request):
        """Handle a request to show a test or resource.

        'request' -- A 'WebRequest' object.

        This function generates pages to handle these requests:

          'create-test' -- Generate a form for initial editing of a test
          about to be created, given its test ID and test class.

          'create-resource' -- Likewise for an resource.

          'show-test' -- Display a test.

          'show-resource' -- Likewise for an resource.

          'edit-test' -- Generate a form for editing an existing test.

          'edit-resource' -- Likewise for an resource.

        This function distinguishes among these cases by checking the script
        name of the request object.

        The request must have the following fields:

          'id' -- A test or resource ID.  For show or edit pages, the ID of an
          existing item.  For create pages, the ID of the item being
          created.

          'class' -- For create pages, the name of the test or resource
          class.

        """

        # Paramaterize this function based on the request's script name.
        url = request.GetScriptName()
        edit, create, type = {
            "show-test":       (0, 0, "test"),
            "edit-test":       (1, 0, "test"),
            "create-test":     (1, 1, "test"),
            "show-resource":   (0, 0, "resource"),
            "edit-resource":   (1, 0, "resource"),
            "create-resource": (1, 1, "resource"),
            }[url]

        database = qm.test.base.get_database()

        try:
            # Determine the ID of the item.
            item_id = request["id"]
        except KeyError:
            # The user probably submitted the form without entering an ID.
            message = qm.error("no id for show")
            return qm.web.generate_error_page(request, message)

        if create:
            # We're in the middle of creating a new item.  
            class_name = request["class"]

            # First perform some validation.
            field_errors = {}
            # Check that the ID is valid.
            try:
                qm.test.base.validate_id(item_id)
            except RuntimeError, diagnostic:
                field_errors["_id"] = diagnostic
            else:
                # Check that the ID doesn't already exist.
                if type is "resource":
                    if database.HasResource(item_id):
                        field_errors["_id"] = qm.error("resource already exists",
                                                       resource_id=item_id)
                elif type is "test":
                    if database.HasTest(item_id):
                        field_errors["_id"] = qm.error("test already exists",
                                                       test_id=item_id)
            # Check that the class exists.
            try:
                qm.test.base.get_extension_class(class_name, type)
            except ValueError:
                # The class name was incorrectly specified.
                field_errors["_class"] = qm.error("invalid class name",
                                                  class_name=class_name)
            except ImportError:
                # Can't find the class.
                field_errors["_class"] = qm.error("class not found",
                                                  class_name=class_name)
            # Were there any errors?
            if len(field_errors) > 0:
                # Yes.  Instead of showing the edit page, re-show the new
                # item page.
                page = NewItemPage(type=type,
                                   item_id=item_id,
                                   class_name=class_name,
                                   field_errors=field_errors)
                return page(request)

            # Construct an test with default argument values, as the
            # starting point for editing.
            if type is "resource":
                item = qm.test.base.make_new_resource(class_name, item_id)
            elif type is "test":
                item = qm.test.base.make_new_test(class_name, item_id)
        else:
            # We're showing or editing an existing item.
            # Look it up in the database.
            if type is "resource":
                try:
                    item = database.GetResource(item_id)
                except qm.test.database.NoSuchTestError:
                    # An test with the specified test ID was not fount.
                    # Show a page indicating the error.
                    message = qm.error("no such test", test_id=item_id)
                    return qm.web.generate_error_page(request, message)
            elif type is "test":
                try:
                    item = database.GetTest(item_id)
                except qm.test.database.NoSuchResourceError:
                    # An test with the specified resource ID was not fount.
                    # Show a page indicating the error.
                    message = qm.error("no such resource", resource_id=item_id)
                    return qm.web.generate_error_page(request, message)

        # Generate HTML.
        return ShowItemPage(item, edit, create, type)(request)


    def HandleShowResult(self, request):
        """Handle a request to show result detail.

        'request' -- The 'WebRequest' that caused the event."""

        result = self.__results_stream.test_results[request["id"]]
        return ResultPage(result)(request)
    

    def HandleShowResults(self, request):
        """Handle a request to show results.

        'request' -- The 'WebRequest' that caused the event."""

        # Display the results.
        results_page = TestResultsPage(self.__results_stream.test_results,
                                       self.__expected_outcomes)
        return results_page(request)


    def HandleShowSuite(self, request, edit=0):
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
        return ShowSuitePage(suite, edit)(request)


    def HandleShutdown(self, request):
        """Handle a request to shut down the server.

        'request' -- The 'WebRequest' that caused the event."""

        raise SystemExit, None


    def HandleSubmitContext(self, request):
        """Handle a context submission.

        'request' -- The 'WebRequest' that caused the event.  The
        'request' must have a 'context_vars' key, whose value is the
        the context variables."""

        vars = qm.web.decode_properties(request["context_vars"])
        self.__context = qm.test.base.Context()
        for k in vars.keys():
            self.__context[k] = vars[k]

        # Redirect to the main page.
        request = qm.web.WebRequest("dir", base=request)
        raise qm.web.HttpRedirect, request


    def HandleSubmitExpectations(self, request):
        """Handle uploading expected results.

        'request' -- The 'WebRequest' that caused the event."""

        # Get the results file data.
        data = request["expected_results"]
        # Create a file object from the data.
        f = StringIO.StringIO(data)
        # Read the results.
        self.__expected_outcomes = qm.test.base.load_outcomes(f)
        # Close the upload popup window, and redirect the main window
        # to a view of the results.
        return """<html><body><script language="JavaScript">
                  window.opener.location = 'edit-expectations';
                  window.close();</script></body></html>"""
        

    def HandleSubmitExpectationsForm(self, request):
        """Handle uploading expected results.

        'request' -- The 'WebRequest' that caused the event."""

        # Clear out the current set of expected outcomes; the entire
        # set of new 
        self.__expected_outcomes = {}
        
        # Loop over all the tests.
        for id in qm.test.base.expand_ids(".")[0]:
            outcome = request[id]
            if outcome != "None":
                self.__expected_outcomes[id] = outcome

        # Redirect to the main page.
        request = qm.web.WebRequest("dir", base=request)
        raise qm.web.HttpRedirect, request
    
        
    def HandleSubmitItem(self, request):
        """Handle a test or resource submission.

        This function handles submission of the test or resource editing form
        generated by 'handle_show'.  The script name in 'request' should be
        'submit-test' or 'submit-resource'.  It constructs the appropriate
        'Test' or 'Resource' object and writes it to the database, either as a
        new item or overwriting an existing item.

        The request must have the following form fields:

        'id' -- The test or resource ID of the item being edited or created.

        'class' -- The name of the test or resource class of this item.

        arguments -- Argument values are encoded in fields whose names start
        with 'qm.fields.Field.form_field_prefix'.

        'prerequisites' -- For tests, a set-encoded collection of
        prerequisites.  Each prerequisite is of the format
        'test_id;outcome'.

        'resources' -- For tests, a set-encoded collection of resource IDs.

        'categories' -- For tests, a set-encoded collection of categories."""

        if request.GetScriptName() == "submit-test":
            type = "test"
        elif request.GetScriptName() == "submit-resource":
            type = "resource"

        # Make sure there's an ID in the request, and extract it.
        try:
            item_id = request["id"]
        except KeyError:
            message = qm.error("no id for submit")
            return qm.web.generate_error_page(request, message)

        database = qm.test.base.get_database()
        # Extract the class and field specification.
        item_class_name = request["class"]
        item_class = qm.test.base.get_extension_class(item_class_name, type)
        fields = item_class.arguments

        # We'll perform various kinds of validation as we extract form
        # fields.  Errors are placed into this map; later, if it's empty, we
        # know there were no validation errors.
        field_errors = {}

        # Loop over fields of the class, looking for arguments in the
        # submitted request.
        arguments = {}
        field_prefix = qm.fields.Field.form_field_prefix
        for field in fields:
            # Construct the name we expect for the corresponding argument.
            field_name = field.GetName()
            form_field_name = field_prefix + field_name
            try:
                # Try to get the argument value.
                value = request[form_field_name]
            except KeyError:
                # The value for this field is missing.
                message = qm.error("missing argument",
                                   title=field.GetTitle())
                return qm.web.generate_error_page(request, message)
            # Parse the value for this field.
            try:
                value = field.ParseFormValue(value)
            except:
                # Something went wrong parsing the value.  Associate an
                # error message with this field.
                message = str(sys.exc_info()[1])
                field_errors[field_name] = message
            else:
                # All is well with this field.
                arguments[field_name] = value

        properties = qm.web.decode_properties(request["properties"])

        if type is "test":
            # Extract prerequisite tests.  
            preqs = request["prerequisites"]
            preqs = qm.web.decode_set_control_contents(preqs)
            # Prerequisite tests are encoded as 'test_id:outcome'.  Unencode
            # them and build a map from test ID to expected outcome.
            prerequisites = {}
            for preq in preqs:
                # Unencode.
                test_id, outcome = string.split(preq, ";", 1)
                # Make sure this outcome is one we know about.
                if not outcome in Result.outcomes:
                    raise RuntimeError, "invalid outcome"
                # Store it.
                prerequisites[test_id] = outcome

            # Extract resources.
            resources = request["resources"]
            resources = qm.web.decode_set_control_contents(resources)

            # Extract categories.
            categories = request["categories"]
            categories = qm.web.decode_set_control_contents(categories)

            # Create a new test.
            item = qm.test.base.TestDescriptor(test_id=item_id,
                                               test_class_name=item_class_name,
                                               arguments=arguments,
                                               prerequisites=prerequisites,
                                               categories=categories,
                                               resources=resources,
                                               properties=properties)

        elif type is "resource":
            # Create a new resource.
            item = qm.test.base.ResourceDescriptor(item_id,
                                                   item_class_name,
                                                   arguments,
                                                   properties)

        # Were there any validation errors?
        if len(field_errors) > 0:
            # Yes.  Instead of processing the submission, redisplay the form
            # with error messages.
            request = request.copy(url="edit-" + type)
            return ShowItemPage(item, 1, 0, type, field_errors)(request)

        # Store it in the database.
        if type is "test":
            database.WriteTest(item)
        elif type is "resource":
            database.WriteResource(item)

        # Remove any attachments located in the temporary store as they
        # have now been copied to the store associated with the database.
        for field in fields:
            if isinstance(field, qm.fields.AttachmentField):
                attachment = arguments[field.GetName()]
                if attachment is not None \
                   and attachment.GetStore() == temporary_store:
                    temporary_store.Remove(attachment.GetLocation())
            elif isinstance(field, qm.fields.SetField) \
                 and isinstance(field.GetContainedField(),
                                qm.fields.AttachmentField):
                for attachment in arguments[field.GetName()]:
                    if attachment is not None \
                       and attachment.GetStore() == temporary_store:
                        temporary_store.Remove(attachment.GetLocation())

        # Redirect to a page that displays the newly-edited item.
        request = qm.web.WebRequest("show-" + type, base=request, id=item_id)
        raise qm.web.HttpRedirect, request


    def HandleSubmitResults(self, request):
        """Handle uploading results.

        'request' -- The 'WebRequest' that caused the event."""

        # Get the results file data.
        data = request["results"]
        # Create a file object from the data.
        f = StringIO.StringIO(data)
        # Read the results.
        results = qm.test.base.load_results(f)
        # Enter them into a new results stream.
        self.__results_stream = StorageResultsStream()
        for r in results:
            self.__results_stream.WriteResult(r)
        self.__results_stream.Summarize()
        # Close the upload popup window, and redirect the main window
        # to a view of the results.
        return """<html><body><script language="JavaScript">
                  window.opener.location = 'show-results';
                  window.close();</script></body></html>"""


    def HandleSubmitSuite(self, request):
        """Handle test suite submission.

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


########################################################################
# initialization
########################################################################

# Use our 'DtmlPage' subclass even when generating generic
# (non-QMTest) pages.
qm.web.DtmlPage.default_class = DefaultDtmlPage

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

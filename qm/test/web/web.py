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



class ContextPage(DtmlPage):
    """DTML page for setting the context."""

    def __init__(self, server):
        """Construct a new 'ContextPage'.

        'server' -- The 'QMTestServer' creating this page."""

        DtmlPage.__init__(self, "context.dtml")
        
        self.__server = server
        self.context = server.GetContext()
        


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


        
class ResultPage(DtmlPage):
    """DTML page for showing result detail."""

    def __init__(self, result):
        """Construct a new 'ResultPage'

        'result' -- The result to display."""

        DtmlPage.__init__(self, "result.dtml")
        self.result = result
        
        
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

        import qm.test.web.dir
        import qm.test.web.run
        import qm.test.web.show
        import qm.test.web.suite

        qm.web.WebServer.__init__(self, port, address, log_file=log_file)

        # Base URL path for QMTest stuff.
        script_base = "/test/"
        # Register all our web pages.
        for name, function in [
            ( "create-resource", qm.test.web.show.handle_show ),
            ( "create-suite", qm.test.web.suite.handle_create ),
            ( "create-test", qm.test.web.show.handle_show ),
            ( "delete-resource", qm.test.web.show.handle_delete ),
            ( "delete-suite", qm.test.web.suite.handle_delete ),
            ( "delete-test", qm.test.web.show.handle_delete ),
            ( "dir", qm.test.web.dir.handle_dir ),
            ( "edit-context", self.HandleEditContext ),
            ( "edit-expectations", self.HandleEditExpectations ),
            ( "edit-resource", qm.test.web.show.handle_show ),
            ( "edit-suite", qm.test.web.suite.handle_edit ),
            ( "edit-test", qm.test.web.show.handle_show ),
            ( "load-expected-results", self.HandleLoadExpectedResults ),
            ( "load-results", self.HandleLoadResults ),
            ( "new-resource", qm.test.web.show.handle_new_resource ),
            ( "new-suite", qm.test.web.suite.handle_new ),
            ( "new-test", qm.test.web.show.handle_new_test ),
            ( "run-tests", self.HandleRunTests ),
            ( "save-expectations", self.HandleSaveExpectations ),
            ( "save-results", self.HandleSaveResults ),
            ( "show-dir", qm.test.web.dir.handle_dir ),
            ( "show-resource", qm.test.web.show.handle_show ),
            ( "show-result", self.HandleShowResult ),
            ( "show-results", self.HandleShowResults ),
            ( "show-suite", qm.test.web.suite.handle_show ),
            ( "show-test", qm.test.web.show.handle_show ),
            ( "shutdown", self.HandleShutdown ),
            ( "submit-context", self.HandleSubmitContext ),
            ( "submit-resource", qm.test.web.show.handle_submit ),
            ( "submit-expectations", self.HandleSubmitExpectations ),
            ( "submit-expectations-form", self.HandleSubmitExpectationsForm ),
            ( "submit-results", self.HandleSubmitResults ),
            ( "submit-suite", qm.test.web.suite.handle_submit ),
            ( "submit-test", qm.test.web.show.handle_submit ),
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


    def HandleEditContext(self, request):
        """Handle a request to edit the context.

        'request' -- The 'WebRequest' that caused the event."""

        context_page = ContextPage(self)
        return context_page(request)
        

    def HandleEditExpectations(self, request):
        """Handle a request to edit the context.

        'request' -- The 'WebRequest' that caused the event."""

        return ExpectationsPage(self)(request)


    def HandleLoadExpectedResults(self, request):
        """Handle a request to upload results.
        
        'request' -- The 'WebRequest' that caused the event."""

        return LoadExpectedResultsPage()(request)

        
    def HandleLoadResults(self, request):
        """Handle a request to upload results.
        
        'request' -- The 'WebRequest' that caused the event."""

        return LoadResultsPage()(request)

    
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
    
                
    def HandleShowResult(self, request):
        """Handle a request to show result detail.

        'request' -- The 'WebRequest' that caused the event."""

        result = self.__results_stream.test_results[request["id"]]
        return ResultPage(result)(request)
    

    def HandleShowResults(self, request):
        """Handle a request to show results.

        'request' -- The 'WebRequest' that caused the event."""

        # Display the results.
        results_page = \
            qm.test.web.run.TestResultsPage(self.__results_stream.test_results,
                                            self.__expected_outcomes)
        return results_page(request)


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
    
        
########################################################################
# initialization
########################################################################

def __initialize_module():
    # Use our 'DtmlPage' subclass even when generating generic
    # (non-QMTest) pages.
    qm.web.DtmlPage.default_class = DefaultDtmlPage


__initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

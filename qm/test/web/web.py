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
import qm.web

########################################################################
# classes
########################################################################

class DtmlPage(qm.web.DtmlPage):
    """Subclass of DTML page class for QMTest pages."""

    html_generator = "QMTest"


    def __init__(self, dtml_template, **attributes):
        # QMTest DTML templates are in the 'test' subdirectory.
        dtml_template = os.path.join("test", dtml_template)
        # Initialize the base class.
        apply(qm.web.DtmlPage.__init__, (self, dtml_template), attributes)


    def GetName(self):
        """Return the name of the application."""

        return self.html_generator


    def MakeListingUrl(self):
        return qm.web.WebRequest("dir", base=self.request).AsUrl()


    def GenerateStartBody(self):
        if self.show_decorations:
            # Include the navigation bar.
            navigation_bar = DtmlPage("navigation-bar.dtml")
            return "<body>%s<br>" % navigation_bar(self.request)
        else:
            return "<body>"


    def GetMainPageUrl(self):
        return self.MakeListingUrl()


    def FormatTestId(self, test_id, relative_to=None, within=None):
        """Return markup for 'test_id'."""

        if relative_to is not None:
            absolute_test_id = qm.label.join(qm.label.dirname(relative_to),
                                             test_id)
        elif within is not None:
            absolute_test_id = qm.label.join(within, test_id)
        else:
            absolute_test_id = test_id

        request = qm.web.WebRequest("show-test",
                                    base=self.request,
                                    id=absolute_test_id)
        return '<a href="%s"><span class="test_id">%s</span></a>' \
               % (request.AsUrl(), test_id)


    def FormatActionId(self, action_id, relative_to=None, within=None):
        """Return markup for 'action_id'."""

        if relative_to is not None:
            absolute_action_id = qm.label.join(qm.label.dirname(relative_to),
                                               action_id)
        elif within is not None:
            absolute_action_id = qm.label.join(within, action_id)
        else:
            absolute_action_id = action_id

        request = qm.web.WebRequest("show-action",
                                    base=self.request,
                                    id=absolute_action_id)
        return '<a href="%s"><span class="action_id">%s</span></a>' \
               % (request.AsUrl(), action_id)


    def FormatSuiteId(self, suite_id, within=None):
        """Return markup for 'suite_id'."""

        if within is not None:
            absolute_suite_id = qm.label.join(within, suite_id)
        else:
            absolute_suite_id = suite_id

        request = qm.web.WebRequest("show-suite",
                                    base=self.request,
                                    id=absolute_suite_id)
        return '<a href="%s"><span class="suite_id">%s</span></a>' \
               % (request.AsUrl(), suite_id)
    


########################################################################
# functions
########################################################################

def make_server(port, address="", log_file=None):
    """Create and bind an HTTP server.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    returns -- A web server.  The server is bound to the specified
    address.  Call its 'Run' method to start accepting requests."""

    import qm.test.web.dir
    import qm.test.web.show
    import qm.test.web.suite

    # Base URL path for QMTest stuff.
    script_base = "/test/"
    # Create a new server instance.  Enable XML-RPM.
    server = qm.web.WebServer(port,
                              address,
                              log_file=log_file)
    qm.attachment.register_attachment_upload_script(server)
    # Register all our web pages.
    for name, function in [
        ( "create-action", qm.test.web.show.handle_show ),
        ( "create-suite", qm.test.web.suite.handle_create ),
        ( "create-test", qm.test.web.show.handle_show ),
        ( "delete-action", qm.test.web.show.handle_delete ),
        ( "delete-suite", qm.test.web.suite.handle_delete ),
        ( "delete-test", qm.test.web.show.handle_delete ),
        ( "dir", qm.test.web.dir.handle_dir ),
        ( "edit-action", qm.test.web.show.handle_show ),
        ( "edit-suite", qm.test.web.suite.handle_edit ),
        ( "edit-test", qm.test.web.show.handle_show ),
        ( "new-action", qm.test.web.show.handle_new_action ),
        ( "new-suite", qm.test.web.suite.handle_new ),
        ( "new-test", qm.test.web.show.handle_new_test ),
        ( "show-action", qm.test.web.show.handle_show ),
        ( "show-suite", qm.test.web.suite.handle_show ),
        ( "show-test", qm.test.web.show.handle_show ),
        ( "shutdown", handle_shutdown ),
        ( "submit-action", qm.test.web.show.handle_submit ),
        ( "submit-suite", qm.test.web.suite.handle_submit ),
        ( "submit-test", qm.test.web.show.handle_submit ),
        ]:
        server.RegisterScript(script_base + name, function)
    server.RegisterPathTranslation(
        "/stylesheets", qm.get_share_directory("web", "stylesheets"))
    server.RegisterPathTranslation(
        "/images", qm.get_share_directory("web", "images"))
    server.RegisterPathTranslation(
        "/static", qm.get_share_directory("web", "static"))
    # Register the QM manual.
    server.RegisterPathTranslation(
        "/manual", qm.get_doc_directory("manual", "html"))
    
    # Bind the server to the specified address.
    try:
        server.Bind()
    except qm.web.AddressInUseError, address:
        raise RuntimeError, qm.error("address in use", address=address)
    except qm.web.PrivilegedPortError:
        raise RuntimeError, qm.error("privileged port", port=port)

    return server


def handle_shutdown(request):
    """Handle a request to shut down the server."""

    raise SystemExit, None


########################################################################
# initialization
########################################################################

def __initialize_module():
    # Use our 'DtmlPage' subclass even when generating generic
    # (non-QMTest) pages.
    qm.web.DtmlPage.default_class = DtmlPage


__initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

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

class PageInfo(qm.web.PageInfo):
    """Subclass of DTML context class, for generating pages from DTML."""

    html_generator = "QMTest"


    def GetName(self):
        """Return the name of the application."""

        return self.html_generator


    def MakeListingUrl(self):
        dir_request = qm.web.WebRequest("dir", base=self.request)
        return qm.web.make_url_for_request(dir_request)


    def GenerateStartBody(self):
        return \
'''
<body>
<table width="100%%" border="0" cellspacing="0" cellpadding="0" bgcolor="black">
 <tr bgcolor="black">
  <td>&nbsp;<a href="http://www.software-carpentry.com/"><img border="0"
  src="/images/sc-logo.png"></a></td>
  <td align="right">
   <a href="%s" class="reverse">Full Listing</a>
   &nbsp;&nbsp;
  </td>
 </tr>
</table>
<br>
''' % self.MakeListingUrl() 


    def FormatTestId(self, test_id):
        """Return markup for 'test_id'."""

        request = qm.web.WebRequest("show-test",
                                    base=self.request,
                                    id=test_id)
        link_target = qm.web.make_url_for_request(request)
        return '<a href="%s"><span class="test_id">%s</span></a>' \
               % (link_target, test_id)


    def FormatActionId(self, action_id):
        """Return markup for 'action_id'."""

        request = qm.web.WebRequest("show-action",
                                    base=self.request,
                                    id=action_id)
        link_target = qm.web.make_url_for_request(request)
        return '<a href="%s"><span class="action_id">%s</span></a>' \
               % (link_target, action_id)


    def FormatSuiteId(self, suite_id):
        """Return markup for 'suite_id'."""

        request = qm.web.WebRequest("show-suite",
                                    base=self.request,
                                    id=suite_id)
        link_target = qm.web.make_url_for_request(request)
        return '<a href="%s"><span class="suite_id">%s</span></a>' \
               % (link_target, suite_id)
    


########################################################################
# functions
########################################################################

def generate_html_from_dtml(template_name, page_info):
    """Return HTML generated from a DTML tempate.

    'template_name' -- The name of the DTML template file.

    'page_info' -- A 'PageInfo' instance to use as the DTML namespace.

    returns -- The generated HTML source."""
    
    template_path = os.path.join("test", template_name)
    return qm.web.generate_html_from_dtml(template_path, page_info)


def start_server(port, address="", log_file=None):
    """Start an HTTP server.

    'port' -- The port number on which to accept HTTP requests.

    'address' -- The local address to which to bind the server.  An
    empty string indicates all local addresses.

    'log_file' -- A file object to which the server will log requests.
    'None' for no logging.

    Does not return until the server shuts down."""

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
        ( "add-action", qm.test.web.show.handle_add_action ),
        ( "add-category", qm.test.web.show.handle_add_category ),
        ( "add-prerequisite", qm.test.web.show.handle_add_prerequisite ),
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
        "/manual", qm.get_doc_directory("manual", "html"))
    
    # Bind the server to the specified address.
    try:
        server.Bind()
    except qm.web.AddressInUseError, address:
        raise RuntimeError, qm.error("address in use", address=address)
    except qm.web.PrivilegedPortError:
        raise RuntimeError, qm.error("privileged port", port=port)

    try:
        # Start the server.
        server.Run()
    finally:
        # Clean up the URL file.
        os.remove(url_path)


########################################################################
# initialization
########################################################################

def __initialize_module():
    # Use our 'PageInfo' subclass even when generating generic
    # (non-QMTest) pages.
    qm.web.PageInfo.default_class = PageInfo


__initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   web.py
# Author: Alex Samuel
# Date:   2001-02-08
#
# Contents:
#   Common code for QMTrack web interface.
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

"""Common code for QMTrack web interface.

This module contains functions for generating HTML to represent
QMTrack elements in the web interface.

Issue fields are formatted according to styles.  The supported styles
are,

  full -- A full representation of the field value.

  brief -- A shorter representation of the field value, used to
  display the value as a cell in a table.

  edit -- An editable representation of the field, consisting of HMTL
  form controls.

  new -- Similar to edit, for entering new issues.

"""

########################################################################
# imports
########################################################################

import DocumentTemplate
import os
import qm.fields
import qm.web
import re
import string
import urllib

########################################################################
# classes
########################################################################

class PageInfo(qm.web.PageInfo):
    """Subclass of DTML context class, for generating pages from DTML."""

    html_generator = "QMTrack"

    html_stylesheet = "stylesheets/qmtrack.css"


    def GetName(self):
        """Return the name of the application."""

        return qm.track.get_name()


    def GenerateStartBody(self):
        return \
'''
<body>
<table width="100%%" border="0" cellspacing="0" cellpadding="0" bgcolor="black">
 <tr bgcolor="black">
  <td>&nbsp;<a href="http://www.software-carpentry.com/"><img border="0"
  src="/images/sc-logo.png"></a></td>
  <td align="right"><font color="white">
   <a href="/track/"><span id="colhead">%s</span></a>
   &nbsp;&nbsp;
   <a href="/track/new"><span id="colhead">New Issue</span></a>
   &nbsp;&nbsp;
   <a href="/track/summary"><span id="colhead">All Issues</span></a>
   &nbsp;&nbsp;
   <a href="/track/query"><span id="colhead">Query</span></a>
   &nbsp;
  </font></td>
 </tr>
</table>
<br>
''' % self.GetName()



class HistoryPageInfo(PageInfo):
    """Context for genering revision history HTML fragment.

    This 'PageInfo' class is used with 'history.dtml', which generates
    an HTML fragment displaying the revision history of an issue."""
    

    def __init__(self, revisions, current_revision_number=None):
        """Initialize a new info object.

        'revisions' -- A sequenceo of revision of the issue, in
        revision number order.

        'current_revision_number' -- If not 'None', the revision with
        this number is indicated specially."""

        # We want the revisions from newest to oldest, so reverse the
        # list. 
        revisions = revisions[:]
        revisions.reverse()
        # Store stuff.
        self.revisions = revisions
        self.current_revision_number = current_revision_number
    

    def FormatRevisionDiff(self, revision1, revision2):
        """Generate HTML fir differences between two revisions.

        'revision1' -- The newer revision.

        'revision2' -- The older revision."""

        # Find the fields that differ between the revisions.
        fields = qm.track.get_differing_fields(revision1, revision2)
        # Certain fields we expect to differ or are irrelevant to the
        # revision history; supress these from the list.
        ignore_fields = ("revision", "timestamp", "user")
        filter_function = lambda field, ignore_fields=ignore_fields: \
                          field.GetName() not in ignore_fields
        fields = filter(filter_function, fields)
        
        # Build a list of strings describing differences.
        differences = []
        for field in fields:
            field_name = field.GetName()
            value = revision1.GetField(field_name)
            formatted_value = field.FormatValueAsHtml(value, "brief")
            description = "%s changed to %s" % (field_name, formatted_value)
            differences.append(description)
        # Build a complete string.
        return string.join(differences, "<br>\n")



class UploadAttachmentPageInfo(PageInfo):
    """DTML context for generating upload-attachment.dtml."""

    def __init__(self, request):
        """Create a new 'PageInfo' object."""

        PageInfo.__init__(self, request)
        # Use a brand-new location for the attachment data.
        idb = qm.track.get_idb()
        self.location = idb.GetNewAttachmentLocation()


    def MakeSubmitUrl(self):
        """Return the URL for submitting this form."""

        request = qm.web.WebRequest("submit-attachment")
        return qm.web.make_url_for_request(request)



########################################################################
# functions
########################################################################

def handle_upload_attachment(request):
    """Generate the attachment upload popup form.

    The form is generated from the DTML template
    upload-attachment.dtml. 

    See 'format_attachment_field_value', which generates code that
    instigates the popup."""

    page_info = UploadAttachmentPageInfo(request)
    return generate_html_from_dtml("upload-attachment.dtml", page_info)
    

def handle_submit_attachment(request):
    """Process submission of attachment data.

    This submission is generated by the attachment data popup form
    produced by 'handle_upload_attachment'."""
    
    # The location at which to store the attachment data is stored in
    # the form and submitted in the request.
    location = request["location"]
    # Store the attachment data in the IDB.
    idb = qm.track.get_idb()
    data = request["file_data"]
    idb.SetAttachmentData(location, data)

    # Return a page that closes the popup window.
    return '''
    <html>
     <body>
      <script language="JavaScript">
      window.close();
      </script>
     </body>
    </html>
    '''


def handle_download_attachment(request):
    """Process a request to download attachment data."""

    # Get the attachment location and MIME type from the request.
    location = request["location"]
    mime_type = request["mime_type"]
    # Get the attachment data.
    idb = qm.track.get_idb()
    data = idb.GetAttachmentData(location)
    # Send it back to the client.
    return (mime_type, data)


def generate_html_from_dtml(template_name, page_info):
    """Return HTML generated from a DTML tempate.

    'template_name' -- The name of the DTML template file.

    'page_info' -- A 'PageInfo' instance to use as the DTML namespace.

    returns -- The generated HTML source."""
    
    # Construct the path to the template file.  DTML templates are
    # stored in qm/qm/track/web/templates. 
    template_path = os.path.join(qm.get_base_directory(),
                                 "track", "web", "templates",
                                 template_name)
    # Generate HTML from the template.
    html_file = DocumentTemplate.HTMLFile(template_path)
    return html_file(page_info)


def generate_error_page(request, error_text):
    """Generate a page to indicate a user error.

    'request' -- The request that was being processed when the error
    was encountered.

    'error_text' -- A description of the error, as structured text.

    returns -- The generated HTML source for the page."""

    page_info = PageInfo(request)
    page_info.error_text = qm.web.format_structured_text(error_text)
    return generate_html_from_dtml("error.dtml", page_info)


def make_url_for_attachment(field, attachment):
    """Return a URL to download 'attachment'."""

    request = qm.web.WebRequest("download-attachment",
                                location=attachment.GetLocation(),
                                mime_type=attachment.GetMimeType())
    return qm.web.make_url_for_request(request)


# The generic 'AttachmentField' implementation needs to know about our
# URLs for downloading attachments.
qm.fields.AttachmentField.MakeDownloadUrl = make_url_for_attachment


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

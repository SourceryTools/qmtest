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
import qm.track
import qm.web
import re
import string
import urllib

########################################################################
# classes
########################################################################

class DtmlPage(qm.web.DtmlPage):
    """Subclass of DTML page class for QMTrack pages."""

    html_generator = "QMTrack"


    def __init__(self, dtml_template, **attributes):
        # QMTrack DTML templates are in the 'track' subdirectory.
        dtml_template = os.path.join("track", dtml_template)
        # Initialize the base class.
        apply(qm.web.DtmlPage.__init__, (self, dtml_template), attributes)


    def GetName(self):
        """Return the name of the application."""

        return qm.track.get_name()


    def GenerateStartBody(self):
        if self.show_decorations:
            # Include the navigation bar.
            navigation_bar = DtmlPage("navigation-bar.dtml")
            return "<body>%s<br>" % navigation_bar(self.request)
        else:
            return "<body>"


    def GetMainPageUrl(self):
        return "/track/"


    def MakeIndexUrl(self):
        return qm.web.WebRequest("index", base=self.request).AsUrl()



class HistoryPageFragment(DtmlPage):
    """Revision history HTML fragment."""
    

    def __init__(self, revisions, current_revision_number=None):
        """Initialize a new info object.

        'revisions' -- A sequenceo of revision of the issue, in
        revision number order.

        'current_revision_number' -- If not 'None', the revision with
        this number is indicated specially."""

        # We want the revisions from newest to oldest, so reverse the
        # list. 
        revisions = list(revisions)
        revisions.reverse()
        # Initialize the base class.
        DtmlPage.__init__(
            self,
            "history.dtml",
            revisions=revisions,
            current_revision_number=current_revision_number)
    

    def GetRevisionTime(self, revision):
        """Return the timestamp on 'revision', formatted as HTML."""

        timestamp_field = revision.GetClass().GetField("timestamp")
        timestamp_value = revision.GetField("timestamp")
        return timestamp_field.FormatValueAsHtml(timestamp_value, "full")


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

            if isinstance(field, qm.fields.SetField):
                # Treat set fields differently.  Rather than showing the
                # entire field contents, show elements that have been
                # added and removed.
                previous_value = revision2.GetField(field_name)

                # Show all elements in the previous revision's value but
                # not in the current value, if any.
                removed_elements = []
                for el in previous_value:
                    if el not in value:
                        removed_elements.append(el)
                if len(removed_elements) > 0:
                    description = "removed from %s: " % field_name \
                        + field.FormatValueAsHtml(removed_elements, "brief")
                    differences.append(description)

                # Now the same thing for elements added to the current
                # revision. 
                new_elements = []
                for el in value:
                    if el not in previous_value:
                        new_elements.append(el)
                if len(new_elements) > 0:
                    description = "added to %s: " % field_name \
                        + field.FormatValueAsHtml(new_elements, "brief")
                    differences.append(description)

            else:
                # All other (non-set) field types.
                formatted_value = field.FormatValueAsHtml(value, "brief")
                description = "%s changed to %s" \
                              % (field_name, formatted_value)
                differences.append(description)

        # Build a complete string.
        return string.join(differences, "<br>\n")



########################################################################
# functions
########################################################################

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


def make_url_for_attachment(field, attachment):
    """Return a URL to download 'attachment'."""

    request = qm.web.WebRequest("download-attachment",
                                location=attachment.location,
                                mime_type=attachment.mime_type)
    url = request.AsUrl()
    # Here's a nice hack.  If the user saves the attachment to a file,
    # browsers (some at least) guess the default file name from the
    # URL by taking everything following the final slash character.  So,
    # we add this bogus-looking argument to fool the browser into using
    # our file name.
    url = url + "&=/" + urllib.quote_plus(attachment.file_name)
    return url


########################################################################
# initialization
########################################################################

def _initialize_module():
    # The generic 'AttachmentField' implementation needs to know about
    # our URLs for downloading attachments.
    qm.fields.AttachmentField.MakeDownloadUrl = make_url_for_attachment
    # Use our 'DtmlPage' subclass even when generating generic
    # (non-QMTrack) pages.
    qm.web.DtmlPage.default_class = DtmlPage


_initialize_module()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

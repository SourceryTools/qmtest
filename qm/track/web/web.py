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
import qm.web
import string

########################################################################
# classes
########################################################################

class PageInfo(qm.web.PageInfo):

    html_generator = "QMTrack"

    html_stylesheet = "stylesheets/qmtrack.css"


    def GenerateStartBody(self):
        return \
'''
<body>
<table width="100%%" %s>
 <tr bgcolor="black">
  <td><font color="white">
   <b>QMTrack</b>
  </font></td>
  <td align="right"><font color="white">
   <a href="/track/new"><span id="colhead">New Issue</span></a>
   &nbsp;&nbsp;
   <a href="/track/summary"><span id="colhead">All Issues</span></a>
  </font></td>
 </tr>
</table>
<br>
''' % qm.web.PageInfo.table_attributes



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
            # FIXME: We need specific support for sets and attachments.
            field_name = field.GetName()
            value = revision1.GetField(field_name)
            formatted_value = format_field_value(field, value, "brief")
            description = "%s changed to %s" % (field_name, formatted_value)
            differences.append(description)
        # Build a complete string.
        return string.join(differences, "<br>\n")



########################################################################
# functions
########################################################################

def make_form_field_name(field):
    """Return the form field name corresponding to 'field'.

    returns -- The name that is used for the control representing
    'field' in an HTML form."""

    name = field.GetName()
    if name == "iid" or name == "revision":
        # Use these field names unaltered.
        return name
    else:
        # Field names can't contain hyphens, so this name shouldn't
        # collide with anything.
        return "field-" + field.GetName()


def format_field_value(field, value, style):
    """Return an HTML representation of a field of an issue.

    'field' -- The field to represent.

    'value' -- The issue's value for that field.

    'style' -- The style in which to format the field.

    raises -- 'ValueError' if 'style' is not a known style."""

    # Don't show a control for a field whose value may not be changed
    # here. 
    if field.IsAttribute("read_only"):
        if style == "new" or style == "edit":
            style = "full"
    elif field.IsAttribute("initialize_only"):
        if style == "edit":
            style = "full"

    # Format based on field type.
    if isinstance(field, qm.track.IssueFieldEnumeration):
        return format_enum_field_value(field, value, style)
    elif isinstance(field, qm.track.IssueFieldInteger):
        return format_int_field_value(field, value, style)
    elif isinstance(field, qm.track.IssueFieldText):
        return format_text_field_value(field, value, style)
    elif isinstance(field, qm.track.IssueFieldSet):
        return format_set_field_value(field, value, style)
    else:
        # FIXME:
        # IssueFieldAttachment.
        # IssueFieldTime.
        raise NotImplementedError, \
              "Can't render a %s value." % field.__class__.__name__


def format_int_field_value(field, value, style):
    """Return an HTML representation of an integer field."""

    if style == "new" or style == "edit":
        return '<input type="text" size="8" name="%s" value="%d"/>' \
               % (make_form_field_name(field), value)
    elif style == "full" or style == "brief":
        return '<tt>%d</tt>' % value
    else:
        raise ValueError, style


def format_text_field_value(field, value, style):
    """Return an HTML representation of a text field."""

    if style == "new" or style == "edit":
        if field.IsAttribute("verbatim") or field.IsAttribute("structured"):
            return '<textarea cols="40" rows="16" name="%s">%s</textarea>' \
                   % (make_form_field_name(field), value)
        else:
            return '<input type="text" size="40" name="%s" value="%s"/>' \
                   % (make_form_field_name(field), value)

    elif style == "brief":
        if field.IsAttribute("verbatim"):
            # FIXME: What should we use here?
            return '<tt>%s</tt>' % qm.web.escape_for_html(value)
        elif field.IsAttribute("structured"):
            # Use only the first line of text.
            value = string.split(value, "\n", 1)
            result = qm.web.format_structured_text(value[0])
            if len(value) > 1:
                result = result + "..."
            return result
        else:
            return qm.web.escape(value)

    elif style == "full":
        if field.IsAttribute("verbatim"):
            # Place verbatim text in a <pre> element.
            return '<pre>%s</pre>' % value 
        elif field.IsAttribute("structured"):
            return qm.web.format_structured_text(value)
        else:
            return qm.web.escape(value)

    else:
        raise ValueError, style


def format_set_field_value(field, value, style):
    """Return an HTML representation of a set field."""

    contained = field.GetContainedField()
    formatted = []
    for element in value:
        formatted.append(format_field_value(field, value, style))
    if len(formatted) == 0:
        return "&nbsp;"
    else:
        return string.join(formatted, ", ")


def format_enum_field_value(field, value, style):
    """Return an HTML representation of an enumeration field."""

    if style == "new" or style == "edit":
        # If the field is editable, generate a '<select>' control.
        result = '<select name="%s">' % make_form_field_name(field)
        # Generate an '<option>' element for each enumeral.
        for en_name, en_val in field.GetEnumerals():
            # Specify the 'select' attribute if this enumeral
            # corresponds to the current field value.
            if en_val == value:
                is_selected = "selected"
            else:
                is_selected = ""
            result = result + '<option value="%s" %s>%s</option>' \
                     % (en_name, is_selected, en_name)
        result = result + '</select>'
        return result

    elif style == "full" or style == "brief":
        return field.ValueToName(value)

    else:
        raise ValueError, style


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


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

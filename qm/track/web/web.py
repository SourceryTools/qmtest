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
<table width="100%%" %s>
 <tr bgcolor="black">
  <td>
   <a href="/track/"><span id="colhead"><b>%s</b></span></a>
  </td>
  <td align="right"><font color="white">
   <a href="/track/new"><span id="colhead">New Issue</span></a>
   &nbsp;&nbsp;
   <a href="/track/summary"><span id="colhead">All Issues</span></a>
   &nbsp;&nbsp;
   <a href="/track/query"><span id="colhead">Query</span></a>
  </font></td>
 </tr>
</table>
<br>
''' % (qm.web.PageInfo.table_attributes, self.GetName(), )



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
            formatted_value = format_field_value(field, value, "brief")
            description = "%s changed to %s" % (field_name, formatted_value)
            differences.append(description)
        # Build a complete string.
        return string.join(differences, "<br>\n")



########################################################################
# functions
########################################################################

form_field_prefix = "_field_"


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
        return "_field_" + field.GetName()


def format_field_value(field, value, style, name=None):
    """Return an HTML representation of a field of an issue.

    'field' -- The field to represent.

    'value' -- The issue's value for that field.  The value may be
    'None', in which case a default is chosen appropriately.

    'style' -- The style in which to format the field.

    'name' -- The name to use for the name attribute of the HTML form
    element, if one is generated.  If 'name' is 'None', the
    appropriate name corresponding to 'field' will be generated with
    'make_form_field_name'.

    raises -- 'ValueError' if 'style' is not a known style."""

    # Don't show a control for a field whose value may not be changed
    # here. 
    if field.IsAttribute("read_only"):
        if style == "new" or style == "edit":
            style = "full"
    elif field.IsAttribute("initialize_only"):
        if style == "edit":
            style = "full"

    # Generate the form field name, if required.
    if name is None:
        name = make_form_field_name(field)

    # Format based on field type.
    if isinstance(field, qm.track.IssueFieldEnumeration):
        return format_enum_field_value(field, value, style, name)
    elif isinstance(field, qm.track.IssueFieldInteger):
        return format_int_field_value(field, value, style, name)
    elif isinstance(field, qm.track.IssueFieldText):
        return format_text_field_value(field, value, style, name)
    elif isinstance(field, qm.track.IssueFieldSet):
        return format_set_field_value(field, value, style, name)
    else:
        # FIXME:
        # IssueFieldAttachment.
        # IssueFieldTime.
        raise NotImplementedError, \
              "Can't render a %s value." % field.__class__.__name__


def format_int_field_value(field, value, style, name):
    """Return an HTML representation of an integer field."""

    # Use default value if requested.
    if value is None:
        value = 0

    if style == "new" or style == "edit":
        return '<input type="text" size="8" name="%s" value="%d"/>' \
               % (name, value)
    elif style == "full" or style == "brief":
        return '<tt>%d</tt>' % value
    else:
        raise ValueError, style


def format_text_field_value(field, value, style, name):
    """Return an HTML representation of a text field."""

    # Use default value if requested.
    if value is None:
        value = ""

    if style == "new" or style == "edit":
        if field.IsAttribute("verbatim") or field.IsAttribute("structured"):
            return '<textarea cols="40" rows="6" name="%s">%s</textarea>' \
                   % (name, value)
        else:
            return '<input type="text" size="40" name="%s" value="%s"/>' \
                   % (name, value)

    elif style == "brief":
        if field.IsAttribute("verbatim"):
            # Truncate to 80 characters, if it's longer.
            if len(value) > 80:
                value = value[:80] + "..."
            # Replace all whitespace with ordinary space.
            value = re.replace("\w", " ")
            # Put it in a <tt> element.
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


def format_set_field_value(field, value, style, name):
    """Return an HTML representation of a set field."""

    # Use default value if requested.
    if value is None:
        value = []

    contained_field = field.GetContainedField()

    if style == "brief" or style == "full":
        formatted = []
        for element in value:
            formatted.append(format_field_value(contained_field,
                                                element, "full"))
        if len(formatted) == 0:
            return "&nbsp;"
        else:
            return string.join(formatted, ", ")

    elif style == "new" or style == "edit":
        # To edit a set field, we generate form and script elements to
        # do most of the work on the client side.  We create a
        # multiline select element to show the contents of the set, a
        # button to delete the selected element, and another button
        # and an input field to add elements.  The values of options
        # in the select element are URL-encoded string representations
        # of the set elements themselves.
        #
        # In addition, we add an extra hidden field, which contains
        # the complete value of the field.  It is this hidden field
        # that carries the form field name for this field.  The field
        # value is updated automatically on the client side whenever
        # the set list elements are modified.  The value consists of
        # the URL-encoded elements separated by commas.
        #
        # The JavaScript scripts generated here assume the form
        # elements will be part of a form named "form".
        
        field_name = field.GetName()
        # Generate a table to arrange the form elements.
        form = '''
        <table border="0" cellpadding="0" cellspacing="0">
        <tr><td>'''
        # Create the hidden field that will carry the field value. 
        text_elements = map(lambda x: urllib.quote(str(x)), value)
        form = form \
               + '<input type="hidden" name="%s" value="%s"/>\n' \
               % (name, string.join(text_elements, ","))
        # Start a select control to show the set elements.
        form = form + '''
         <select size="6" name="_list_%s" width="200">
        ''' % field_name
        # Add an option element for each element of the set.
        for item in value:
            brief_item = format_field_value(contained_field, item, "brief")
            form = form + '<option value="%s">%s</option>\n' \
                   % (urllib.quote(str(item)), brief_item)
        # End the select control.  Put everything else next to it.
        form = form + '''
         </select>
        </td><td>
        '''
        # Build a button for deleting elements.  It calls a
        # JavaScript function to do the work.
        on_click = "_delete_selected_%s();" % field_name
        form = form \
               + qm.web.make_url_button(url=None,
                                        text="Delete Selected",
                                        on_click=on_click) \
               + "<br>"
        # Add a field with which the user specifies each new element
        # to add. 
        new_item_field_name = "_new_item_%s" % field_name
        form = form + format_field_value(contained_field, None, style,
                                         name=new_item_field_name)
        # Build the button that adds the element specified in this
        # control. 
        on_click = "_add_%s();" % field_name
        form = form \
               + qm.web.make_url_button(url=None, text="Add",
                                        on_click=on_click)
        # All done with the visiual elements.
        form = form + '''
        </td></tr>
        </table>
        '''
        # Generate JavaScript functions for adding and deleting
        # elements.  Also generate a function that updates the value
        # of the hidden field from the values in the select element.
        form = form + '''
        <script language="JavaScript">
        function _delete_selected_%s()
        {
          var list = document.form._list_%s;
          if(list.selectedIndex != -1)
            list.options[list.selectedIndex] = null;
          _update_%s();
          return false;
        }

        function _add_%s()
        {
          var options = document.form._list_%s.options;
          var input = document.form._new_item_%s;
          var text;
          var value;
          if(input.type == "select-one" || input.type == "select-multiple") {
            text = input.options[input.selectedIndex].text;
            value = input.options[input.selectedIndex].value;
          }
          else {
            text = input.value;
            value = escape(input.value);
          }
          for(var i = 0; i < options.length; ++i)
            if(options[i].value == value)
              return false;
          if(value != "")
            options[options.length] = new Option(text, value);
          input.value = "";
          input.focus();
          _update_%s();
          return false;
        }  

        function _update_%s()
        {
          var list = document.form._list_%s;
          var result = "";
          for(var i = 0; i < list.options.length; ++i) {
            if(i > 0)
              result += ",";
            result += list.options[i].value;
          }
          document.form.%s.value = result;
        }
        </script>
        ''' % (9 * (field_name, ) + (name, ))
        # All done.
        return form


def format_enum_field_value(field, value, style, name):
    """Return an HTML representation of an enumeration field."""

    # Use default value if requested.
    if value is None:
        value = field.GetEnumerals()[0][1]

    if style == "new" or style == "edit":
        # If the field is editable, generate a '<select>' control.
        result = '<select name="%s">\n' % name
        # Generate an '<option>' element for each enumeral.
        for en_name, en_val in field.GetEnumerals():
            # Specify the 'select' attribute if this enumeral
            # corresponds to the current field value.
            if en_val == value:
                is_selected = "selected"
            else:
                is_selected = ""
            result = result + '<option value="%d" %s>%s</option>\n' \
                     % (en_val, is_selected, en_name)
        result = result + '</select>\n'
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


def generate_error_page(request, error_text):
    """Generate a page to indicate a user error.

    'request' -- The request that was being processed when the error
    was encountered.

    'error_text' -- A description of the error, as structured text.

    returns -- The generated HTML source for the page."""

    page_info = PageInfo(request)
    page_info.error_text = qm.web.format_structured_text(error_text)
    return generate_html_from_dtml("error.dtml", page_info)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# End:

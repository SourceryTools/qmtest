########################################################################
#
# File:   fields.py
# Author: Alex Samuel
# Date:   2001-03-05
#
# Contents:
#   General type system for user-defied data constructs.
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

import attachment
import common
import label
import qm
import qm.xmlutil
import diagnostic
import string
import time
import urllib
import xml.dom
import xmlutil

########################################################################
# exceptions
########################################################################

class DomNodeError(Exception):
    """An error extracting a field value from an XML DOM node.

    See 'Field.GetValueFromDomNode'."""

    pass



########################################################################
# classes
########################################################################

class Field:
    """Base class for issue field types.

    The following attributes are recognized for all field types.

    read_only -- If true, the field may not be modified by users.

    initialize_only -- If true, the field may only be modified by a
    user when a new issue is created.

    hidden -- If true, the field is for internal purposes, and not
    shown in user interfaces."""

    def __init__(self, name, attributes={}):
        """Create a new (generic) field.

        'name' -- The value of the name attribute.  Must be a valid
        label.

        'attributes' -- A mapping of additional attribute assignments
        to set."""

        if not label.is_valid(name):
            raise ValueError, \
                  qm.error("invalid field name", field_name=name)

        self.__attributes = {
            "name" : name,
            "title" : name,
            "read_only" : "false",
            "initialize_only" : "false",
            "hidden" : "false",
            }
        self.__attributes.update(attributes)
        # Use the name as the title, if no other was specified.
        if not self.__attributes.has_key("title"):
            self.__attributes["title"]


    def __repr__(self):
        return "<%s %s>" % (self.__class__, self.GetName())


    def GetName(self):
        """Return the name of the field."""

        return self.GetAttribute("name")


    def GetTitle(self):
        """Return the user-friendly title of the field."""

        return self.GetAttribute("title")


    def GetDescription(self):
        """Return a description of this field."""

        return self.GetAttribute("description", "(no description)")


    def GetTypeDescription(self):
        """Return a structured text description of valid values."""

        raise qm.MethodShouldBeOverriddenError


    def SetDefaultValue(self, value):
        """Make 'value' the default value for this field."""

        # Validate the default value.
        value = self.Validate(value)
        self.default_value = value


    def UnsetDefaultValue(self):
        """Remove the default value for this field, if any.

        If a field has no default value, its value must be specified
        for every issue created with that field."""

        if hasattr(self, "default_value"):
            del self.default_value


    def HasDefaultValue(self):
        """Return true if this field has a default value."""

        return hasattr(self, "default_value")


    def GetDefaultValue(self):
        """Return the default value for this field."""

        return self.default_value


    def GetAttribute(self, attribute_name, default_value=""):
        """Return the value of an attribute.

        Return the value of the attribute named by 'attribute_name'.
        If that attribute is not set, return 'default_value'."""

        if self.__attributes.has_key(attribute_name):
            return self.__attributes[attribute_name]
        else:
            return default_value


    def IsAttribute(self, attribute_name):
        """Return a true value if an attribute has the value "true"."""

        return self.GetAttribute(attribute_name) == "true"


    def SetAttribute(self, attribute_name, value):
        """Set the value of an attribute."""

        self.__attributes[attribute_name] = value


    def UnsetAttribute(self, attribute_name):
        """Remove an attribute.

        If there is no attribute named 'attribute_name', does nothing."""

        if self.__attributes.has_key(attribute_name):
            del self.__attributes[attribute_name]


    def Validate(self, value):
        """Validate a field value.

        For an acceptable type and value, return the representation of
        'value' in the underlying field storage.

        'value' -- A value to validate for this field.

        returns -- The canonicalized representation of 'value'.

        raises -- 'ValueError' if 'value' is not a valid value for
        this field.

        Implementations of this method must be idempotent."""

        raise qm.MethodShouldBeOverriddenError, "Field.Validate"


    def ValuesAreEqual(self, value1, value2):
        """Return true if 'value1' and 'value2' are the same."""

        return value1 == value2


    form_field_prefix = "_field_"

    def GetHtmlFormFieldName(self):
        """Return the form field name corresponding this field.

        returns -- The name that is used for the control representing
        this field in an HTML form."""

        name = self.GetName()
        if name == "iid" or name == "revision":
            # Use these field names unaltered.
            return name
        else:
            # Field names can't contain hyphens, so this name shouldn't
            # collide with anything.
            return self.form_field_prefix + self.GetName()


    def FormatValueAsHtml(self, value, style, name=None):
        """Return an HTML rendering of a 'value' for this field.

        'value' -- The value for this field.  May be 'None', which
        renders a default value (useful for blank forms).

        'style' -- The rendering style.  Can be "full" or "brief" (both
        read-only), or "new" or "edit".

        'name' -- The name to use for the primary HTML form element
        containing the value of this field, if 'style' specifies the
        generation of form elements."""

        raise qm.MethodShouldBeOverriddenError, "Field.FormatValueAsHtml"


    def ParseFormValue(self, value):
        """Convert a value submitted from an HTML form.

        'value' -- A string representing the HTML form input's value.

        returns -- The corresponding field value."""

        raise qm.MethodShouldBeOverriddenError, \
              "Field.ParseForSubmittedValue"


    def FormEncodeValue(self, value):
        """Return an encoding for 'value' to store in HTML forms.

        The form-encoded value is used to represent a value when it is
        an element in a set.  The options in the HTML list element
        representing the set store these encodings as their values."""

        raise qm.MethodShouldBeOverriddenError, "Field.FormEncodeValue"


    def FormDecodeValue(self, encoding):
        """Unencode the HTML form-encoded 'encoding' and return a value."""

        raise qm.MethodShouldBeOverriddenError, "Field.FormDecodeValue"


    def GetValueFromDomNode(self, node):
        """Return a value for this field represented by DOM 'node'.

        This method does not validate the value for this particular
        instance; it only makes sure the node is well-formed, and
        returns a value of the correct Python type.

        raises -- 'DomNodeError' if the node's structure or contents are
        incorrect for this field."""

        raise qm.MethodShouldBeOverriddenError, "Field.GetValueFromDomNode"


    def MakeDomNodeForValue(self, value, document):
        """Generate a DOM element node for a value of this field.

        'value' -- The value to represent.

        'document' -- The containing DOM document node."""

        raise qm.MethodShouldBeOverriddenError, "Field.MakeDomNodeForValue"



########################################################################

class IntegerField(Field):

    def __init__(self, name, default_value=0):
        """Create an integer field.

        The field must be able to represent a 32-bit signed
        integer.

        'default_value' -- The default value for the field."""

        # Perform base class initialization.
        Field.__init__(self, name)
        # Set the default value.
        self.SetDefaultValue(default_value)


    def GetTypeDescription(self):
        return "an integer"


    def Validate(self, value):
        return int(value)


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = 0
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            return '<input type="text" size="8" name="%s" value="%d"/>' \
                   % (name, value)
        elif style == "full" or style == "brief":
            return '<tt>%d</tt>' % value
        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        return int(value)


    def FormEncodeValue(self, value):
        return "%d" % value
    

    def FormDecodeValue(self, encoding):
        return int(encoding)
    

    def GetValueFromDomNode(self, node):
        # Make sure 'node' is an '<integer>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "integer":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="integer",
                                   wrong_tag=node.tagName)
        # Retrieve the contained text.
        value = qm.xmlutil.get_dom_text(node)
        # Convert it to an integer.
        try:
            return int(value)
        except ValueError:
            raise DomNodeError, \
                  diagnostic.error("dom bad integer", value=value)


    def MakeDomNodeForValue(self, value, document):
        return qm.xmlutil.create_dom_text_element(document, "integer",
                                                  str(value))



########################################################################

class TextField(Field):
    """A field that contains text.  

    'default_value' -- The default value for this field.
    
    A text field uses the following attributes:

    structured -- If true, the field contains multiline structured
    text.

    verbatim -- If true, the contents of the field are quoted as a
    block when the field is externalized; otherwise, individual
    characters are quoted as required by the externalizaton mechanism.

    big -- This is a hint that, if true, recommends to issue database
    mechanisms that the contents of the field may be large and should
    be stored out-of-line.

    nonempty -- The value of this field is considered invalid if it
    consists of an empty string (after stripping)."""

    def __init__(self, name, default_value=""):
        """Create a text field."""

        # Perform base class initialization.
        Field.__init__(self, name)
        # Set default attribute values.
        self.SetAttribute("structured", "false")
        self.SetAttribute("verbatim", "false")
        self.SetAttribute("big", "false")
        self.SetAttribute("nonempty", "false")
        # Set the default field value.
        self.SetDefaultValue(default_value)


    def GetTypeDescription(self):
        return "a string"
    

    def Validate(self, value):
        # Be forgiving, and try to convert 'value' to a string if it
        # isn't one.
        value = str(value)
        # Clean up unless it's a verbatim string.
        if not self.IsAttribute("verbatim"):
            # Remove leading whitespace.
            value = string.lstrip(value)
        # If this field has the nonempty attribute set, make sure the
        # value complies.
        if self.IsAttribute("nonempty") and value == "":
            raise ValueError, \
                  qm.error("empty field value", field_name=self.GetTitle()) 
        return value


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = ""
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            if self.IsAttribute("verbatim") \
               or self.IsAttribute("structured"):
                return '<textarea cols="40" rows="6" name="%s">' \
                       '%s</textarea>' \
                       % (name, value)
            else:
                return '<input type="text" size="40" name="%s" value="%s"/>' \
                       % (name, value)

        elif style == "brief":
            if self.IsAttribute("verbatim"):
                # Truncate to 80 characters, if it's longer.
                if len(value) > 80:
                    value = value[:80] + "..."
                # Replace all whitespace with ordinary space.
                value = re.replace("\w", " ")
                # Put it in a <tt> element.
                return '<tt>%s</tt>' % qm.web.escape_for_html(value)
            elif self.IsAttribute("structured"):
                # Use only the first line of text.
                value = string.split(value, "\n", 1)
                result = qm.web.format_structured_text(value[0])
                if len(value) > 1:
                    result = result + "..."
                return result
            else:
                return qm.web.escape(value)

        elif style == "full":
            if self.IsAttribute("verbatim"):
                # Place verbatim text in a <pre> element.
                return '<pre>%s</pre>' % value 
            elif self.IsAttribute("structured"):
                return qm.web.format_structured_text(value)
            else:
                return qm.web.escape(value)

        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        # HTTP specifies text encodints are CR/LF delimited; convert to
        # the One True Text Format (TM).
        return qm.convert_from_dos_text(value)


    def FormEncodeValue(self, value):
        return urllib.quote(value)


    def FormDecodeValue(self, encoding):
        return urllib.unquote(encoding)


    def GetValueFromDomNode(self, node):
        # Make sure 'node' is a '<text>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "text":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="text",
                                   wrong_tag=node.tagName)
        # Just the text, ma'am.
        return qm.xmlutil.get_dom_text(node)


    def MakeDomNodeForValue(self, value, document):
        return qm.xmlutil.create_dom_text_element(document, "text", value)
       


########################################################################

class SetField(Field):
    """A field containing zero or more instances of some other field.

    All contents must be of the same field type.  A set field may not
    contain sets.

    The default field value is set to an empty set."""

    def __init__(self, contained):
        """Create a set field.

        The name of the contained field is taken as the name of this
        field.

        'contained' -- An 'Field' instance describing the
        elements of the set. 

        raises -- 'ValueError' if 'contained' is a set field.

        raises -- 'TypeError' if 'contained' is not an 'Field'."""

        # A set field may not contain a set field.
        if isinstance(contained, SetField):
            raise ValueError, \
                  "A set field may not contain a set field."
        if not isinstance(contained, Field):
            raise TypeError, "A set must contain another field."
        # Use the attributes from the contained field, rather than
        # making a different set.
        self._Field__attributes = contained._Field__attributes
        # Remeber the contained field type.
        self.__contained = contained
        # Set the default field value to any empty set.
        self.SetDefaultValue([])


    def GetTypeDescription(self):
        return "a sequence; each element is %s" \
               % self.GetContainedField().GetTypeDescription()
    

    def Validate(self, value):
        # Assume 'value' is a sequence.  Copy it, simultaneously
        # validating each element in the contained field.
        result = []
        for element in value:
            result.append(self.__contained.Validate(element))
        return result


    def GetContainedField(self):
        """Returns the field instance of the contents of the set."""

        return self.__contained


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = []
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        contained_field = self.GetContainedField()

        if style == "brief" or style == "full":
            if len(value) == 0:
                # An empty set.
                return "&nbsp;"
            formatted = []
            for element in value:
                # Format each list element in the indicated style.
                formatted.append(contained_field.FormatValueAsHtml(element,
                                                                   style))
            if style == "brief":
                # In the brief style, list elements separated by commas.
                separator = ", "
            else:
                # In the full style, list elements one per line.
                separator = "<br>\n"
            return string.join(formatted, separator)

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

            field_name = self.GetName()
            # Generate a table to arrange the form elements.
            form = '''
            <table border="0" cellpadding="0" cellspacing="0">
            <tr><td>'''
            # Create the hidden field that will carry the field value. 
            current_value = self.GenerateFormValue(value)
            form = form \
                   + '<input type="hidden" name="%s" value="%s"/>\n' \
                   % (name, current_value)
            # Start a select control to show the set elements.
            form = form + '''
             <select size="6" name="_list_%s" width="200">
            ''' % field_name
            # Add an option element for each element of the set.
            for item in value:
                item_text = contained_field.FormatValueAsHtml(item, "brief")
                item_value = contained_field.FormEncodeValue(item)
                form = form \
                       + '<option value="%s">%s</option>\n' \
                       % (item_value, item_text)
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
            form = form \
                   + contained_field.FormatValueAsHtml(None, style,
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

            # Now generate the scripts that make it all happen.
            form = form + '<script language="JavaScript">\n'

            # The script for removing an element is the same, no matter
            # what's in the set.
            form = form + '''
            function _delete_selected_%s()
            {
              var list = document.form._list_%s;
              if(list.selectedIndex != -1)
                list.options[list.selectedIndex] = null;
              _update_%s();
              return false;
            }
            ''' % (field_name, field_name, field_name)
            # Also a function to update the field that actually contains the
            # submitted value of the set.  That field contains a
            # comma-separated list of the values of the set's elements.
            form = form + '''
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
            ''' % (field_name, field_name, name, )

            # The function that adds an element to the list differs
            # depending on the set contents, since the values we submit in
            # the form vary.

            form = form + '''
            function _add_%s()
            {
              var options = document.form._list_%s.options;
              var text;
              var value;

              var input = document.form._new_item_%s;
            ''' % (field_name, field_name, field_name)
            if isinstance(contained_field, qm.fields.EnumerationField):
                # The value of an enum field is specified with a set
                # control.  Use the value of the currently-selected element.
                form = form + '''
                  text = input.options[input.selectedIndex].text;
                  value = input.options[input.selectedIndex].value;
                '''
            elif isinstance(contained_field, qm.fields.AttachmentField):
                # The value for an attachment field is a
                # semicolon-separated list.  The first element is the
                # attachment description, URL-encoded; use that as the
                # text in the list. 
                form = form + '''
                  value = input.value;
                  text = value.slice(0, value.indexOf(";"));
                  text = unescape(text);
                '''
            else:
                # Other fields use text controls.  The contents have to be
                # URL-encoded to protect them when we roll them into a list
                # of set items.
                form = form + '''
                  text = input.value;
                  value = escape(input.value);
                  // Clear the value, to prevent double additions.
                  input.value = "";
                '''
            # Now code that checks for duplicates in the list, adds the
            # option, and calls the update function to update the master set
            # value. 
            form = form + '''
              // Skip the addition if there is already another element in
              // the set with the same value.
              for(var i = 0; i < options.length; ++i)
                if(options[i].value == value)
                  return false;
              if(value != "")
                options[options.length] = new Option(text, value);
              // Give focus so that the user can add another element easily.
              input.focus();
              // Update the master set field value.
              _update_%s();
              return false;
            }  
            ''' % field_name

            form = form + '</script>\n'

            # All done.
            return form


    def ParseFormValue(self, value):
        contained_field = self.GetContainedField()
        # The value of a set field is is encoded as a comma-separated
        # list of URL-encoded elements.
        values = string.split(value, ",")
        if values == [""]:
            values = []
        # Now decode the individual elements.
        decoder = lambda value, field=contained_field: \
                  field.FormDecodeValue(value)
        return map(decoder, values)


    def GenerateFormValue(self, value):
        contained_field = self.GetContainedField()
        result = []
        for element in value:
            result.append(contained_field.FormEncodeValue(element))
        return string.join(result, ",")
    

    def FormEncodeValue(self, encoding):
        raise NotImplementedError


    def FormDecodeValue(self, encoding):
        raise NotImplementedError


    def GetValueFromDomNode(self, node):
        # Make sure 'node' is a '<set>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "set":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="set",
                                   wrong_tag=node.tagName)
        # Use the contained field to extract values for the children of
        # this node, which are the set elements.
        contained_field = self.GetContainedField()
        return map(contained_field.GetValueFromDomNode, node.childNodes)


    def MakeDomNodeForValue(self, value, document):
        # Create a set element.
        element = document.createElement("set")
        # Add a child node for each item in the set.
        contained_field = self.GetContainedField()
        for item in value:
            # The contained field knows how to make a DOM node for each
            # item in the set.
            item_node = contained_field.MakeDomNodeForValue(item, document)
            element.appendChild(item_node)
        return element



########################################################################

class AttachmentField(Field):
    """A field containing a file attachment."""

    MakeDownloadUrl = None
    """Function for generating a URL to download this attachment.

    This variable, if not 'None', contains a callable that returns a
    string containing the URL for dowloading an 'Attachment' object
    specified as its argument.  The URL is used when formatting field
    values as HTML."""


    def __init__(self, name):
        """Create an attachment field.

        Sets the default value of the field to 'None'."""

        # Perform base class initialization.
        Field.__init__(self, name)
        # Set the default value of this field.
        self.SetDefaultValue(None)


    def GetTypeDescription(self):
        return "an attachment"


    def Validate(self, value):
        # The value should be an instance of 'Attachment', or 'None'.
        if value != None and not isinstance(value, attachment.Attachment):
            raise ValueError, \
                  "the value of an attachment field must be an 'Attachment'"
        return value


    attachment_summary_prefix = "_attachment"

    def FormatValueAsHtml(self, value, style, name=None):
        field_name = self.GetName()

        if value is None:
            # The attachment field value may be 'None', indicating no
            # attachment. 
            pass
        elif isinstance(value, attachment.Attachment):
            location = value.location
            type = value.mime_type
            description = value.description
        else:
            raise ValueError, "'value' must be 'None' or an 'Attachment'"

        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "full" or style == "brief":
            if value is None:
                return "none"
            # Link the attachment description to the data itself.
            make_url = self.MakeDownloadUrl
            if make_url is None:
                result = "<tt>%s</tt>" % description
            else:
                download_url = make_url(value)
                result = '<a href="%s"><tt>%s</tt></a>' % (download_url,
                                                           description)
            # For the full style, display the MIME type.
            if style == "full":
                size = value.GetDataSize()
                size = qm.format_byte_count(size)
                result = result + ' (%s; %s)' % (type, size)
            return result

        elif style == "new" or style == "edit":

            # Some trickiness here.
            #
            # For attachment fields, the user specifies the file to
            # upload via a popup form, which is shown in a new browser
            # window.  When that form is submitted, the attachment data
            # is immediately uploaded to the server.
            #
            # The information that's stored for an attachment is made of
            # three parts: a description, a MIME type, and the location
            # of the data itself.  The user enters the description
            # directly here; the popup form is responsible for obtaining
            # the location and MIME type.  It fills these two values
            # into hidden fields on this form.
            #
            # Also, when the popup form is submitted, the attachment
            # data is uploaded and stored by the IDB.  By the time this
            # form is submitted, the attachment data should be uploaded
            # already.

            # Generate controls for this form.  These include,
            #
            #   - A text control for the description.
            # 
            #   - A button to pop up the upload form.  It calls the
            #     upload_file JavaScript function.
            #
            #   - A hidden control for the MIME type, whose value is set
            #     by the popup form.
            #
            #   - A hidden control for the attachment location, whose 
            #     value is set by the popup form.
            #
            #   - A hidden control for the uploaded file name.  This is 
            #     used to determine the file's MIME type automatically,
            #     if requested. 
            #

            summary_field_name = self.attachment_summary_prefix + name

            # Fill in the description if there's already an attachment.
            if value is None:
                summary_value = ''
                field_value = ''
            else:
                summary_value = 'value="%s"' % self.FormatSummary(value)
                field_value = 'value="%s"' % self.GenerateFormValue(value)
            result = '''
            <input type="text"
                   readonly
                   size="40"
                   name="%s"
                   %s>
            <input type="button"
                   name="_upload_%s"
                   size="20"
                   value=" Upload "
                   onclick="javascript: upload_file_%s()">
            <input type="hidden"
                   name="%s"
                   %s>
            ''' % (
                summary_field_name,
                summary_value,
                field_name,
                field_name,
                name,
                field_value,
                )

            # Now the JavaScript function that's called when the use
            # clicks the Upload button.  It opens a window showing the
            # upload form, and passes in the field names in this form,
            # which the popup form will fill in.
            result = result + '''
            <script language="JavaScript">
            function upload_file_%s()
            {
              var win = window.open("upload-attachment"
                                    + "?field_name=%s"
                                    + "&encoding_name=%s"
                                    + "&summary_field_name=%s",
                                    "upload_%s",
                                    "height=240,width=480");
            }
            </script>
            ''' % (field_name, field_name, name,
                   summary_field_name, field_name)

            # Phew!  All done.
            return result

        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        return self.FormDecodeValue(value)


    def GenerateFormValue(self, value):
        return self.FormEncodeValue(value)


    def FormEncodeValue(self, value):
        # We shouldn't have to form-encode a null attachment.
        assert value is not None

        # We'll encode all the relevant information.
        parts = (
            value.description,
            value.mime_type,
            value.location,
            value.file_name,
            )
        # Each part is URL-encoded.
        map(urllib.quote, parts)
        # The parts are joined into a semicolon-delimited list.
        return string.join(parts, ";")


    def FormDecodeValue(self, encoding):
        # An empty string represnts a missing attachment, which is OK.
        if string.strip(encoding) == "":
            return None
        # The encoding is a semicolon-separated triplet of description,
        # MIME type, and location.
        parts = string.split(encoding, ";")
        # Undo the URL encoding of each component.
        parts = map(urllib.unquote, parts)
        # Unpack the results.
        description, mime_type, location, file_name = parts
        # Create the attachment.
        return attachment.attachment_class(mime_type=mime_type,
                                           description=description,
                                           file_name=file_name,
                                           location=location)


    def FormatSummary(self, attachment):
        """Generate a user-friendly summary for 'attachment'.

        This value is used when generating the form.  It can't be
        editied."""

        if attachment is None:
            return ""
        else:
            return attachment.description


    def GetValueFromDomNode(self, node):
        # Make sure 'node' is an '<attachment>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "attachment":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="attachment",
                                   wrong_tag=node.tagName)
        return attachment.from_dom_node(node)


    def MakeDomNodeForValue(self, value, document):
        return value.MakeDomNode(document)
    


########################################################################

class EnumerationField(IntegerField):
    """A field that contains an enumeral value.

    The enumeral value is selected from an enumerated set of values.
    An enumeral field uses the following attributes:

    enumeration -- A mapping from enumeral names to enumeral values.
    Names are converted to strings, and values are stored as integers.

    ordered -- If non-zero, the enumerals are presented to the user
    ordered by value."""

    def __init__(self, name, enumeration, default_value=None):
        """Create an enumeral field.

        'enumeration' -- A mapping from names to integer values.

        'default_value' -- The default value for this enumeration.  If
        'None', the lowest-valued enumeral is used."""

        # Copy the enumeration mapping, and canonicalize it so that
        # keys are strings and values are integers.
        self.__enumeration = {}
        for key, value in enumeration.items():
            # Turn them into the right types.
            key = str(key)
            value = int(value)
            # Make sure the name is OK.
            if not label.is_valid(key):
                raise ValueError, qm.error("invalid enum key", key=key)
            # Store it.
            self.__enumeration[key] = value
        if len(self.__enumeration) == 0:
            raise ValueError, qm.error("empty enum")
        # If 'default_value' is 'None', use the lowest-numbered enumeral.
        if default_value == None:
            default_value = min(self.__enumeration.values())
        # Perform base class initialization.
        IntegerField.__init__(self, name, default_value)
        # Store the enumeration as an attribute.
        self.SetAttribute("enumeration", repr(enumeration))


    def GetTypeDescription(self):
        enumerals = self.GetEnumerals()
        enumerals = map(lambda en: "'%s'" % en[0], enumerals)
        return "an enumeration of " + string.join(enumerals, ", ")


    def Validate(self, value):
        # First check whether value is an enumeration key, i.e. the
        # name of an enumeral.
        if self.__enumeration.has_key(value):
            return self.__enumeration[value]
        # Also accept a value, i.e. an integer mapped by an enumeral.
        elif int(value) in self.__enumeration.values():
            return int(value)
        else:
            values = string.join(map(lambda k, v: "%s (%d)" % (k, v),
                                     self.__enumeration.items()),
                                 ", ")
            raise ValueError, \
                  qm.error("invalid enum value",
                           value=value,
                           field_name=self.GetTitle(),
                           values=values)


    def GetEnumerals(self):
        """Return a sequence of enumerals.

        returns -- A sequence consisting of (name, value) pairs, in
        the appropriate order.

        To obtain a map from enumeral name to value, use the
        enumeration attribute."""

        # Obtain a list of (name, value) pairs for enumerals.
        enumerals = self.__enumeration.items()
        # How should they be sorted?
        if self.IsAttribute("ordered"):
            # Sort by the second element, the enumeral value.
            sort_function = lambda e1, e2: cmp(e1[1], e2[1])
        else:
            # Sort by the first element, the enumeral name.
            sort_function = lambda e1, e2: cmp(e1[0], e2[0])
        enumerals.sort(sort_function)
        return enumerals


    def ValueToName(self, value):
        """Return the enumeral name corresponding to 'value'."""

        for en_name, en_val in self.__enumeration.items():
            if value == en_val:
                return en_name
        # No match was found; value must be invalid.
        values = string.join(map(lambda k, v: "%s (%d)" % (k, v),
                                 self.__enumeration.items()),
                             ", ")
        raise ValueError, qm.error("invalid enum value",
                                   value=str(value),
                                   field_name=self.GetTitle(),
                                   values=values)


    def GetEnumeration(self):
        """Get the enumeration mapping from this class.

        XXX: Another shameless hack by Benjamin Chelf.  We need to get
        the actual mapping (not the string found in the attribute)
        so we can set enumerals to their integer values.  Better suggestions
        to do this are appreciated.

        'returns' -- This function returns a mapping from enumerals to
        their integer values."""

        return self.__enumeration


    def FormatValueAsHtml(self, value, style, name=None):
        # Use the default field form field name if requested.
        if value is None:
            value = self.GetEnumerals()[0][1]
        # Use default value if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            # If the field is editable, generate a '<select>' control.
            result = '<select name="%s">\n' % name
            # Generate an '<option>' element for each enumeral.
            for en_name, en_val in self.GetEnumerals():
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
            return self.ValueToName(value)

        else:
            raise ValueError, style


    def GetValueFromDomNode(self, node):
        # Make sure 'node' is an '<enumeral>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "enumeral":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="enumeral",
                                   wrong_tag=node.tagName)
        # Extract the value.
        value = qm.xmlutil.get_dom_text(node)
        try:
            # The value might be a number.
            return int(value)
        except ValueError:
            # Not a number; assume it's an enumeral name.
            return value


    def MakeDomNodeForValue(self, value, document):
        # Store the name of the enumeral.
        enumeral_name = self.ValueToName(value)
        return qm.xmlutil.create_dom_text_element(document, "enumeral",
                                                  enumeral_name)



########################################################################

class TimeField(TextField):
    """A field containing a date and time."""

    __time_format = "%Y-%m-%d %H:%M"
    """The format, ala the 'time' module, used to represent field values."""

    def __init__(self, name):
        """Create a time field.

        The field is given a default value for this field is 'None', which
        causes the current time to be used when an issue is created if no
        field value is provided."""

        # Perform base class initalization.
        TextField.__init__(self, name, default_value=None)


    def GetTypeDescription(self):
        return "a date/time (right now, it is %s)" % self.GetCurrentTime()

    def Validate(self, value):
        # Parse and reformat the time value.
        if value == None:
            return value
        else:
            time_tuple = time.strptime(value, self.__time_format)
            return time.strftime(self.__time_format, time_tuple)


    def GetDefaultValue(self):
        default_value = TextField.GetDefaultValue(self)
        if default_value == None:
            default_value = self.GetCurrentTime() 
        return default_value


    def GetCurrentTime(self):
        now = time.localtime(time.time())
        return time.strftime(self.__time_format, now)
        


########################################################################

class UidField(TextField):
    """A field containing a user ID."""

    def __init__(self, name):
        # FIXME: For now, since we don't have a user model, use a
        # default value.
        TextField.__init__(self, name, default_value="default_user")

    def GetTypeDescription(self):
        return "a user ID"



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

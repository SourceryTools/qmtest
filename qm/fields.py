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
import diagnostic
import label
import os
import qm
import qm.xmlutil
import string
import structured_text
import sys
import time
import types
import urllib
import user
import web
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

    initialize_to_default -- Only the default value is available when
    the issue is created.  Other values may subsequently be specified
    when additional revisions are created.

    hidden -- If true, the field is for internal purposes, and not
    shown in user interfaces."""

    def __init__(self, name, **attributes):
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
            "initialize_to_default": "false",
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

        return common.copy(self.default_value)


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


    def GetAttributeNames(self):
        """Return a sequence of names of attributes defined for this field."""

        return self.__attributes.keys()


    def SetAttribute(self, attribute_name, value):
        """Set the value of an attribute."""

        self.__attributes[attribute_name] = value


    def SetAttributes(self, attributes):
        """Set the value of several attributes.

        'attributes' -- A map from attribute names to values."""

        self.__attributes.update(attributes)


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


    def FormatValueAsText(self, value, columns=72):
        """Return a plain text rendering of a 'value' for this field.

        'columns' -- The maximum width of each line of text."""

        raise qm.MethodShouldBeOverriddenError, "Field.FormatValueAsText"


    def FormatValueAsHtml(self, value, style, name=None):
        """Return an HTML rendering of a 'value' for this field.

        'value' -- The value for this field.  May be 'None', which
        renders a default value (useful for blank forms).

        'style' -- The rendering style.  Can be "full" or "brief" (both
        read-only), or "new" or "edit" or "hidden".

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


    def GetHelp(self):
        """Generate help text about this field in structured text format."""

        raise qm.MethodShouldBeOverriddenError, "GetHelp"
        

    def GetHtmlHelp(self, edit=0):
        """Generate help text about this field in HTML format.

        'edit' -- If true, display information about editing controls
        for this field."""

        description = structured_text.to_html(self.GetDescription())
        help = structured_text.to_html(self.GetHelp())

        return '''
        <h3>%s</h3>
        <h4>About This Field</h4>
        %s
        <hr noshade size="2">
        <h4>About This Field\'s Values</h4>
        %s
        <hr noshade size="2">
        <p><font size="-1">Refer to this field as <tt>%s</tt> in Python
        expressions such as queries.</font></p>
        ''' % (self.GetTitle(), description, help, self.GetName(), )



########################################################################

class IntegerField(Field):

    def __init__(self, name, default_value=0, **attributes):
        """Create an integer field.

        The field must be able to represent a 32-bit signed
        integer.

        'default_value' -- The default value for the field."""

        # Perform base class initialization.
        apply(Field.__init__, (self, name,), attributes)
        # Set the default value.
        self.SetDefaultValue(default_value)


    def GetTypeDescription(self):
        return "an integer"


    def Validate(self, value):
        return int(value)


    def FormatValueAsText(self, value, columns=72):
        return str(value)
    

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
        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%d"/>' \
                   % (name, value)            
        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        try:
            return int(value)
        except ValueError:
            raise ValueError, qm.error("invalid integer field value")


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


    def GetHelp(self):
        help = '''
            This field takes an integer value between %d and %d inclusive.
        ''' % (-sys.maxint - 1, sys.maxint)
        if self.HasDefaultValue():
            help = help + '''
            The default value of this field is %d.
            ''' % self.GetDefaultValue()
        return help
    


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

    def __init__(self, name, default_value="", **attributes):
        """Create a text field."""

        # Perform base class initialization.
        apply(Field.__init__, (self, name,))
        # Set default attribute values.
        self.SetAttribute("structured", "false")
        self.SetAttribute("verbatim", "false")
        self.SetAttribute("big", "false")
        self.SetAttribute("nonempty", "false")
        # Set the default field value.
        self.SetDefaultValue(default_value)
        # Set any provided attributes.
        self.SetAttributes(attributes)


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


    def FormatValueAsText(self, value, columns=72):
        if self.IsAttribute("structured"):
            return structured_text.to_text(value, width=columns)
        else:
            return common.wrap_lines(value, columns)
    

    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = ""
        else:
            value = str(value)
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            if self.IsAttribute("verbatim") \
               or self.IsAttribute("structured"):
                result = '<textarea cols="64" rows="8" name="%s">' \
                         '%s</textarea>' \
                         % (name, web.escape(value))
                # If this is a structured text field, add a note to that
                # effect, so users aren't surprised.
                if self.IsAttribute("structured"):
                    result = result \
                    + '<br><font size="-1">This is a ' \
                    + qm.web.make_help_link_html(
                        qm.structured_text.html_help_text,
                        "structured text") \
                    + 'field.</font>'
                return result
            else:
                return '<input type="text" size="40" name="%s" value="%s"/>' \
                       % (name, web.escape(value))

        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, web.escape(value))            

        elif style == "brief":
            if self.IsAttribute("verbatim"):
                # Truncate to 80 characters, if it's longer.
                if len(value) > 80:
                    value = value[:80] + "..."
                # Replace all whitespace with ordinary space.
                value = re.replace("\w", " ")
                # Put it in a <tt> element.
                return '<tt>%s</tt>' % web.escape(value)
            elif self.IsAttribute("structured"):
                # Use only the first line of text.
                value = string.split(value, "\n", 1)
                result = web.format_structured_text(value[0])
                if len(value) > 1:
                    result = result + "..."
                return result
            else:
                return web.escape(value)

        elif style == "full":
            if self.IsAttribute("verbatim"):
                # Place verbatim text in a <pre> element.
                return '<pre>%s</pre>' % web.escape(value)
            elif self.IsAttribute("structured"):
                return web.format_structured_text(value)
            else:
                if value == "":
                    # Browsers don't deal nicely with empty table cells,
                    # so put an extra space here.
                    return "&nbsp;"
                else:
                    return web.escape(value)

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


    def GetHelp(self):
        help = """
            A text field.  """
        if self.IsAttribute("structured"):
            help = help + '''
            The text is interpreted as structured text, and formatted
            appropriately for the output device.  See "Structured Text
            Formatting
            Rules":http://www.python.org/sigs/doc-sig/stext.html for
            more information.  '''
        elif self.IsAttribute("verbatim"):
            help = help + """
            The text is stored verbatim; whitespace and indentation are
            preserved.  """
        if self.IsAttribute("nonempty"):
            help = help + """
            This field may not be empty.  """
        if self.HasDefaultValue():
            help = help + """
            The default value of this field is "%s".
            """ % self.GetDefaultValue()
        return help



########################################################################

class SetPopupPageInfo(web.PageInfo):
    """DTML context for generating HTML from template set.dtml.

    The template 'set.dtml' is used to generate a popup HTML page for
    specifying a new element to add to a set field."""

    def __init__(self, set_field, control_name, select_name):
        """Construct a new context.

        'set_field' -- The 'SetField' instance for which the page is
        being generated.

        'control_name' -- The name of the hidden HTML input in which the
        encoded set contents are stored.

        'select_name' -- The name of the user-visible HTML select input
        displaying the set contents."""
        
        # Construct a null 'WebRequest' object, since we don't need it.
        request = web.WebRequest("")
        web.PageInfo.__init__(self, request)
        # Set attributes.
        self.field = set_field
        self.field_name = control_name
        self.select_name = select_name


    def MakeElementControl(self):
        """Make HTML controls for editing a value of the contained field."""

        contained_field = self.field.GetContainedField()
        default_value = contained_field.GetDefaultValue()
        return contained_field.FormatValueAsHtml(default_value, "new",
                                                 name="item")


    def MakeTitle(self):
        """Return the page title."""

        return "Add an Element to %s" % self.field.GetTitle()



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


    def FormatValueAsText(self, value, columns=72):
        # If the set is empty, indicate this specially.
        if len(value) == 0:
            return "None"
        # Format each element of the set, and join them into a
        # comma-separated list. 
        contained_field = self.GetContainedField()
        formatted_items = []
        for item in value:
            formatted_item = contained_field.FormatValueAsText(item, columns)
            formatted_items.append(formatted_item)
        result = string.join(formatted_items, ", ")
        return qm.common.wrap_lines(result, columns)


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
                return "None"
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

        elif style in ["new", "edit", "hidden"]:
            field_name = self.GetName()
            select_name = "_set_" + name

            # Construct a list of (text, value) pairs for the set's
            # elements. 
            initial_elements = []
            for element in value:
                element_value = contained_field.FormEncodeValue(element)
                if isinstance(contained_field, AttachmentField):
                    element_text = "%s (%s; %s)" \
                                   % (element.description,
                                      element.file_name,
                                      element.mime_type)
                else:
                    element_text = element_value
                initial_elements.append((element_text, element_value))

            if style == "hidden":
                initial_values = map(lambda x: x[1], initial_elements)
                value = web.encode_set_control_contents(initial_values)
                return '<input type="hidden" name="%s" value="%s"/>' \
                       % (name, value) 

            if isinstance(contained_field, AttachmentField):
                # Handle attachment fields specially.  For these, go
                # straight to the upload attachment popup page.
                page_info = UploadAttachmentPageInfo(
                    self.GetTitle(), name, select_name, in_set=1)
                add_page = qm.web.generate_html_from_dtml(
                    "attachment.dtml", page_info)
            else:
                # Generate the page to show when the user clicks the
                # "Add..." button.  Generate a popup page that contains
                # controls for designating a single value of the
                # contained field type, which is the element that is
                # being added to the set.
                page_info = SetPopupPageInfo(self, name, select_name)
                add_page = web.generate_html_from_dtml("set.dtml", page_info)
            
            # Construct the controls for manipulating the set.
            form = web.make_set_control("form",
                                        field_name=name,
                                        add_page=add_page,
                                        select_name=select_name,
                                        initial_elements=initial_elements,
                                        window_width=600,
                                        window_height=400)
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


    def GetHelp(self):
        return """
        A set field.  A set contains zero or more elements, all of the
        same type.  The elements of the set are described below:

        """ + self.GetContainedField().GetHelp()


    def GetHtmlHelp(self, edit=0):
        help = Field.GetHtmlHelp(self)
        if edit:
            # In addition to the standard generated help, include
            # additional instructions about using the HTML controls.
            help = help + """
            <hr noshade size="2">
            <h4>Modifying This Field</h4>
        
            <p>The list control shows the current elements of the set.
            Each element is listed on a separate line.  Add a new
            element to the set, click on the <i>Add...</i> button.  To
            remove an element from the set, select it by clicking on it
            in the list, and click on the <i>Remove</i> button.</p>
            """
        return help



########################################################################

class UploadAttachmentPageInfo(web.PageInfo):
    """DTML context for generating upload-attachment.dtml."""

    __next_temporary_location = 0

    def __init__(self, 
                 field_name,
                 encoding_name,
                 summary_field_name,
                 in_set=0):
        """Create a new 'PageInfo' object.

        'field_name' -- The user-visible name of the field for which an
        attachment is being uploaded.

        'encoding_name' -- The name of the HTML input that should
        contain the encoded attachment.

        'summary_field_name' -- The name of teh HTML input that should
        contain the user-visible summary of the attachment.

        'in_set' -- If true, the attachment is being added to an
        attachment set field."""

        request = web.WebRequest("")
        web.PageInfo.__init__(self, request)
        # Use a brand-new location for the attachment data.
        self.location = attachment.get_temporary_location()
        # Set up attributes.
        self.field_name = field_name
        self.encoding_name = encoding_name
        self.summary_field_name = summary_field_name
        self.in_set = in_set


    def MakeSubmitUrl(self):
        """Return the URL for submitting this form."""

        return self.request.copy(attachment.upload_url).AsUrl()



class AttachmentField(Field):
    """A field containing a file attachment.

    Note that the 'FormatValueAsHtml' method uses a popup upload form
    for uploading new attachment.  The web server must be configued to
    handle the attachment submission requests.  See
    'attachment.register_attachment_upload_script'."""

    MakeDownloadUrl = None
    """Function for generating a URL to download this attachment.

    This variable, if not 'None', contains a callable that returns a
    string containing the URL for dowloading an 'Attachment' object
    specified as its argument.  The URL is used when formatting field
    values as HTML."""


    def __init__(self, name, **attributes):
        """Create an attachment field.

        Sets the default value of the field to 'None'."""

        # Perform base class initialization. 
        apply(Field.__init__, (self, name,), attributes)
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


    def FormatValueAsText(self, value, columns=72):
        return self.FormatSummary(value)


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
                return "None"
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
            # four parts: a description, a MIME type, the file name, and
            # the location of the data itself.  The user enters these
            # values in the popup form, which sets a hidden field on
            # this form to an encoding of that information.
            #
            # Also, when the popup form is submitted, the attachment
            # data is uploaded.  By the time this form is submitted, the
            # attachment data should be uploaded already.  The uploaded
            # attachment data is stored in the temporary attachment
            # area; it's copied into the IDB when the issue revision is
            # submitted. 

            summary_field_name = "_attachment" + name

            # Fill in the description if there's already an attachment.
            summary_value = 'value="%s"' % self.FormatSummary(value)
            field_value = 'value="%s"' % self.GenerateFormValue(value)

            # Generate the popup upload page.
            page_info = UploadAttachmentPageInfo(self.GetTitle(), name,
                                                 summary_field_name)
            upload_page = qm.web.generate_html_from_dtml("attachment.dtml",
                                                         page_info)
            
            # Generate controls for this form.
            
            # A text control for the user-visible summary of the
            # attachment.  The "readonly" attribute isn't supported in
            # Netscape, so prevent the user from typing into the form by
            # forcing focus away from the control.
            text_control = '''
            <input type="text"
                   readonly
                   size="40"
                   name="%s"
                   onfocus="this.blur();"
                   %s>''' % (summary_field_name, summary_value)
            # A button to pop up the upload form.  It causes the upload
            # page to appear in a popup window.
            upload_button = qm.web.make_button_for_popup("Upload",
                                                         upload_page,
                                                         window_width=640,
                                                         window_height=320)
            # A button to clear the attachment.
            clear_button = '''
            <input type="button"
                   size="20"
                   value=" Clear "
                   name="_clear_%s"
                   onclick="document.form.%s.value = 'None';
                            document.form.%s.value = '';"/>
            ''' % (field_name, summary_field_name, name)
            # A hidden control for the encoded attachment value.  See
            # 'FormEncodeValue' and 'FormDecodeValue'.  The popup upload
            # form fills in this control.
            hidden_control = '''
            <input type="hidden"
                   name="%s"
                   %s>''' % (name, field_value)
            # Now assemble the controls with some layout bits.
            result = '''
            %s%s<br>
            %s%s
            ''' % (text_control, hidden_control, upload_button, clear_button)

            # Phew!  All done.
            return result

        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        return self.FormDecodeValue(value)


    def GenerateFormValue(self, value):
        if value is None:
            return ""
        else:
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
            return "None"
        else:
            return "%s (%s; %s)" \
                   % (attachment.description, attachment.file_name,
                      attachment.mime_type)


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
        if value is None:
            return attachment.make_dom_node(None, document)
        else:
            return value.MakeDomNode(document)


    def GetHelp(self):
        return """
        An attachment field.  An attachment consists of an uploaded
        file, which may be of any file type, plus a short description.
        The name of the file, as well as the file's MIME type, are also
        stored.  The description is a single line of plain text.

        An attachment need not be provided.  The field may be left
        empty."""


    def GetHtmlHelp(self, edit=0):
        help = Field.GetHtmlHelp(self)
        if edit:
            # In addition to the standard generated help, include
            # additional instructions about using the HTML controls.
            help = help + """
            <hr noshade size="2">
            <h4>Modifying This Field</h4>
        
            <p>The text control describes the current value of this
            field, displaying the attachment's description, file name,
            and MIME type.  If the field is empty, the text control
            displays "None".  The text control cannot be edited.</p>

            <p>To upload a new attachment (replacing the previous one,
            if any), click on the <i>Change...</i> button.  To clear the
            current attachment and make the field empty, click on the
            <i>Clear</i> button.</p>
            """
        return help
    


########################################################################

class EnumerationField(IntegerField):
    """A field that contains an enumeral value.

    The enumeral value is selected from an enumerated set of values.
    An enumeral field uses the following attributes:

    enumeration -- A mapping from enumeral names to enumeral values.
    Names are converted to strings, and values are stored as integers.

    ordered -- If non-zero, the enumerals are presented to the user
    ordered by value."""

    def __init__(self, name, enumeration, default_value=None, **attributes):
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
            default_value = common.Enumeral(self.__enumeration, default_value)
        # Perform base class initialization.
        apply(Field.__init__, (self, name, ), attributes)
        # Store the enumeration as an attribute.
        self.SetAttribute("enumeration", repr(enumeration))
        # Set the default value.
        self.SetDefaultValue(default_value)


    def GetTypeDescription(self):
        enumerals = map(str, self.GetEnumerals())
        return 'an enumeration of "%s"' % string.join(enumerals, '," "')


    def Validate(self, value):
        try:
            return common.Enumeral(self.__enumeration, value)
        except ValueError:
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

        returns -- A sequence consisting of 'Enumeration' objects, in
        the appropriate order.

        To obtain a map from enumeral name to value, use
        'GetEnumeration'."""

        # Obtain a list of (name, value) pairs for enumerals.
        enumerals = []
        for name in self.__enumeration.keys():
            enumerals.append(common.Enumeral(self.__enumeration, name))
        # How should they be sorted?
        if self.IsAttribute("ordered"):
            # Sort by the second element, the enumeral value.
            sort_function = lambda e1, e2: cmp(int(e1), int(e2))
        else:
            # Sort by the first element, the enumeral name.
            sort_function = lambda e1, e2: cmp(str(e1), str(e2))
        enumerals.sort(sort_function)
        return enumerals


    def GetEnumeration(self):
        """Get the enumeration mapping from this class.

        returns -- A mapping from enumerals to their integer values."""

        return self.__enumeration


    def ParseFormValue(self, value):
        return common.Enumeral(self.__enumeration, value)


    def FormEncodeValue(self, encoding):
        return str(encoding)


    def FormDecodeValue(self, encoding):
        return common.Enumeral(self.__enumeration, encoding)


    def FormatValueAsText(self, value, columns=72):
        return str(value)
    

    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = self.GetDefaultValue()
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            enumerals = self.__GetAvailableEnumerals(value)
            return qm.web.make_select(name, enumerals, value,
                                      str, self.FormEncodeValue)

        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, str(value)) 

        elif style == "full" or style == "brief":
            return str(value)

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
        return qm.xmlutil.create_dom_text_element(document, "enumeral",
                                                  str(value))


    def GetHelp(self):
        help = """
        An enumeration field.  The value of this field must be one of a
        preselected set of enumerals.  The enumerals for this field are,

        """
        for name, value in self.__enumeration.items():
            help = help + '            * "%s" (%d)\n\n' % (name, value)
        help = help + """
        An enumeral may be specified either by its name (a string) or by
        its numerical value.
        """
        if self.HasDefaultValue():
            default_value = self.GetDefaultValue()
            help = help + '''
        The default value of this field is "%s".
            ''' % str(default_value)
        return help


    def __GetAvailableEnumerals(self, value):
        """Return a limited sequence of enumerals."""

        return self.GetEnumerals()



########################################################################

class TimeField(IntegerField):
    """A field containing a date and time.

    The data and time is stored as seconds since the start of the UNIX
    epoch, UTC (the semantics of the standard 'time' function), with
    one-second precision.  User representations of 'TimeField' fields
    show one-minue precision."""

    def __init__(self, name, **attributes):
        """Create a time field.

        The field is given a default value for this field is 'None', which
        causes the current time to be used when an issue is created if no
        field value is provided."""

        # Perform base class initalization.
        apply(IntegerField.__init__, (self, name), attributes)
        # Set the default value.
        self.default_value = None


    def GetTypeDescription(self):
        return "a date/time (right now, it is %s)" % self.GetCurrentTime()


    def FormatValueAsText(self, value, columns=72):
        return qm.common.format_time(value, local_time_zone=1)


    def FormatValueAsHtml(self, value, style, name=None):
        value = self.FormatValueAsText(value)

        if style == "new" or style == "edit":
            return '<input type="text" size="8" name="%s" value="%s"/>' \
                   % (name, value)
        elif style == "full" or style == "brief":
            return value
        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, value)
        else:
            raise ValueError, style


    def ParseFormValue(self, value):
        return qm.common.parse_time(value, default_local_time_zone=1)


    def GetDefaultValue(self):
        default_value = IntegerField.GetDefaultValue(self)
        if default_value is None:
            return self.GetCurrentTime() 
        else:
            return default_value


    def GetCurrentTime(self):
        """Return a field value corresponding to the current time."""

        return int(time.time())


    def GetHelp(self):
        if time.daylight:
            time_zones = "%s or %s" % time.tzname
        else:
            time_zones = time.tzname[0]
        help = """
            This field contains a time and date.  The format for the
            time and date is 'YYYY-MM-DD HH:MM ZZZ'.  The 'ZZZ' field is
            the time zone, and may be the local time zone (%s) or
            "UTC".

            If the date component is omitted, today's date is used.  If
            the time component is omitted, midnight is used.  If the
            time zone component is omitted, the local time zone is
            used.
        """ % time_zones
        default_value = self.default_value
        if default_value is None:
            help = help + """
            The default value for this field is the current time.
            """
        else:
            help = help + """
            The default value for this field is %s.
            """ % self.FormatValueAsText(default_value)
        return help
        


########################################################################

class UidField(TextField):
    """A field containing a user ID."""

    def __init__(self, name, **attributes):
        attributes["default_value"] = user.database.GetDefaultUserId()
        apply(TextField.__init__, (self, name), attributes)


    def GetTypeDescription(self):
        return "a user ID"


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = self.GetDefaultValue()
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style in ["new", "edit"]:
            uids = qm.user.database.keys()
            return qm.web.make_select(name, uids, value)

        elif style in ["brief", "full"]:
            return web.format_user_id(value)

        else:
            raise ValueError, style



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   fields.py
# Author: Alex Samuel
# Date:   2001-03-05
#
# Contents:
#   General type system for user-defied data constructs.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

from   __future__ import nested_scopes
import attachment
import common
import cStringIO
import diagnostic
import formatter
import htmllib
import label
import os
import re
import qm
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
# constants
########################################################################

query_field_property_prefix = "_prop_"
# The prefix for names of query fields for field properties in web
# requests. 

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

class PropertyDeclaration:
    """A declaration of a property.

    A 'PropertyDeclaration' is used to declare a property, which
    consists of a string name and a string value, and provide auxiliary
    information, including a user-friendly description and a default
    value.

    The name of a property is composed of lower-case letters, digits,
    and underscores.  Properties are string-valued, but there are no
    typographic restriction on the value."""

    def __init__(self, name, description, default_value):
        """Declare a field property.

        'name' -- The property name.

        'description' -- A user-friendly description, in structured text
        format, of the property.

        'default_value' -- The default value for this property."""

        self.name = name
        self.description = description
        self.default_value = default_value



class FieldEditPage(web.DtmlPage):
    """DTML page for editing a field.

    The DTML template 'field.dtml' is used to generate a page for
    displaying and editing the configuration of a field.  The field's
    type and name may not be modified, but its other properties may.

    See 'Field.GenerateEditWebPage'."""

    def __init__(self, field, submit_request):
        """Create a new page info object.

        'request' -- The 'WebRequest' in response to which the page is
        being generated.

        'field' -- The field being edited.

        'submit_request' -- A 'WebRequest' object to which the field
        edit form is submitted."""
        
        # Initialize the base class.
        web.DtmlPage.__init__(self, "field.dtml")
        # Store properties for later.
        self.field = field
        self.property_controls = field.MakePropertyControls()
        self.submit_request = submit_request


    def MakeExtraPropertyInputs(self):
        """Construct form inputs for arbitrary field properties.

        These inputs are used for displaying and editing properties
        other than the standard properties understood by a field.  Any
        properties for which there are controls included in the field's
        'MakePropertyControls' are omitted from this control."""

        # Construct a map from property names to corresponding values.
        # Only include properties for which there is no control in
        # 'property_controls'. 
        properties = {}
        for name in self.field.GetPropertyNames():
            if not self.property_controls.has_key(name):
                value = self.field.GetProperty(name)
                properties[name] = value
        # Generate the inputs.
        return qm.web.make_properties_control(form_name="form",
                                              field_name="extra_properties",
                                              properties=properties)


    def GetFieldType(self, field):
        """Return the class name of this field."""
        
        if isinstance(field, SetField):
            return "<tt>%s</tt> of <tt>%s</tt>" \
                   % (field.__class__, field.GetContainedField().__class__)
        else:
            return "<tt>%s</tt>" % field.__class__


    def GetDocString(self, field):
        """Return the doc string for 'field', formatted as HTML."""

        doc_string = field.__class__.__doc__
        if doc_string is None:
            return "&nbsp;"
        else:
            return qm.web.format_structured_text(doc_string)


    def MakeDefaultValueControl(self, field):
        """Return a control for editing the default value of a field."""

        if field.IsProperty("read_only"):
            style = "full"
        else:
            style = "new"
        default_value = field.GetDefaultValue()
        return field.FormatValueAsHtml(default_value, style,
                                       name="_default_value")



class Field:
    """Base class for field types."""

    property_declarations = [
        PropertyDeclaration(
            name="name",
            description="""The internal name for this field. QM uses
            this name to identify the field. This name is also used when
            referring to the field in Python expressions.""",
            default_value=""
            ),

        PropertyDeclaration(
            name="title",
            description="""The name displayed for this field in user
            interfaces.""",
            default_value=""
            ),

        PropertyDeclaration(
            name="description",
            description="A description of this field's role or purpose.",
            default_value=""
            ),

        PropertyDeclaration(
            name="hidden",
            description="""If true, the field is for internal purposes,
            and not shown in user interfaces.""",
            default_value="false"
            ),

        PropertyDeclaration(
            name="read_only",
            description="If true, the field may not be modified by users.",
            default_value="false"
            ),

        PropertyDeclaration(
            name="computed",
            description="""If true, the field is computed automatically.
            All computed fields are implicitly hidden, and implicitly
            readonly.""",
            default_value="false"
            ),
        ]


    form_field_prefix = "_field_"
    

    def __init__(self, name, default_value, **properties):
        """Create a new (generic) field.

        'name' -- The value of the name property.  Must be a valid
        label.

        'default_value' -- The default value for this field.

        'properties' -- A mapping of additional property assignments
        to set."""

        self.__properties = {}
        # Initialize declared properties to their default values.
        for declaration in self.property_declarations:
            self.__properties[declaration.name] = \
                declaration.default_value
        # Set the name.
        self.__properties["name"] = name
        # Use the name as the title, if no other was specified.
        if not properties.has_key("title"):
            self.__properties["title"] = name
        # Make sure that all properties provided are actually declared.
        # Otherwise, typos in extension classes where the wrong
        # properties are set are hard to debug.  This is handled by an
        # exception, rather than an assert, because asserts are only
        # visible when running Python in debug mode.  We want to make
        # sure that these errors are always visible to extension class
        # programmers.
        declared_property_names = map(lambda pd: pd.name,
                                      self.property_declarations)
        for k in properties.keys():
            if k not in declared_property_names:
                raise qm.common.QMException, \
                      qm.error("unexpected extension argument",
                               name = k,
                               class_name = self.__class__)
        # Update any additional properties provided explicitly.
        self.__properties.update(properties)
        self.SetDefaultValue(default_value)

        # All computed fields are also read-only and hidden.
        if (self.IsComputed()):
            self.__properties.update({"read_only" : "true",
                                      "hidden" : "true"})


    def __repr__(self):
        return "<%s %s>" % (self.__class__, self.GetName())


    def GetName(self):
        """Return the name of the field."""

        return self.GetProperty("name")


    def GetTitle(self):
        """Return the user-friendly title of the field."""

        return self.GetProperty("title")


    def GetDescription(self):
        """Return a description of this field.

        This description is used when displaying detailed help
        information about the field."""

        return self.GetProperty("description")


    def GetBriefDescription(self):
        """Return a brief description of this field.

        This description is used when prompting for input, or when
        displaying the current value of the field."""

        # Get the complete description.
        description = self.GetDescription()
        # Return the first paragraph.
        return structured_text.get_first(description)

        
    def GetTypeDescription(self):
        """Return a structured text description of valid values."""

        raise NotImplementedError


    def SetDefaultValue(self, value):
        """Make 'value' the default value for this field."""

        self.default_value = value


    def GetDefaultValue(self):
        """Return the default value for this field."""

        return common.copy(self.default_value)


    def GetProperty(self, property_name, default_value=None):
        """Return the value of a property.

        Return the value of the property named by 'property_name'.
        If that property is not set, return 'default_value'."""

        if self.__properties.has_key(property_name):
            return self.__properties[property_name]
        else:
            if default_value is None:
                for declaration in self.property_declarations:
                    if declaration.name == property_name:
                        return declaration.default_value
                raise qm.common.QMException, \
                      "no default value for %s" % property_name
            else:
                return default_value


    def IsProperty(self, property_name):
        """Return a true value if a property has the value "true"."""

        return self.GetProperty(property_name, "false") == "true"


    def GetPropertyNames(self):
        """Return a sequence of names of properties defined for this field."""

        return self.__properties.keys()


    def SetProperty(self, property_name, value):
        """Set the value of a property."""

        self.__properties[property_name] = value


    def SetProperties(self, properties):
        """Set the value of several properties.

        'properties' -- A map from property names to values."""

        self.__properties.update(properties)


    def UnsetProperty(self, property_name):
        """Remove a property.

        If there is no property named 'property_name', does nothing."""

        if self.__properties.has_key(property_name):
            del self.__properties[property_name]


    def Validate(self, value):
        """Validate a field value.

        For an acceptable type and value, return the representation of
        'value' in the underlying field storage.

        'value' -- A value to validate for this field.

        returns -- The canonicalized representation of 'value'.

        raises -- 'ValueError' if 'value' is not a valid value for
        this field.

        Implementations of this method must be idempotent."""

        raise NotImplementedError


    def CompareValues(self, value1, value2):
        """Return a comparison of two values of this field.

        returns -- A comparison value, with the same interpretation as
        values of 'cmp'."""

        # In absence of a better comparison, use the Python built-in.
        return cmp(value1, value2)


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
            return "_field_" + self.GetName()


    def FormatValueAsText(self, value, columns=72):
        """Return a plain text rendering of a 'value' for this field.

        'columns' -- The maximum width of each line of text."""

        # Create a file to hold the result.
        text_file = cStringIO.StringIO()
        # Format the field as HTML.
        html_file = cStringIO.StringIO(self.FormatValueAsHtml(value,
                                                              "brief"))

        # Turn the HTML into plain text.
        parser = htmllib.HTMLParser(formatter.AbstractFormatter
                                    (formatter.DumbWriter(text_file,
                                                          maxcol = columns)))
        parser.feed(html_file)
        parser.close()
        text = text_file.getValue()

        # Close the files.
        text_file.close()
        html_file.close()
        
        return text
    

    def FormatValueAsHtml(self, value, style, name=None):
        """Return an HTML rendering of a 'value' for this field.

        'value' -- The value for this field.  May be 'None', which
        renders a default value (useful for blank forms).

        'style' -- The rendering style.  Can be "full" or "brief" (both
        read-only), or "new" or "edit" or "hidden".

        'name' -- The name to use for the primary HTML form element
        containing the value of this field, if 'style' specifies the
        generation of form elements."""

        raise NotImplementedError


    def ParseFormValue(self, request, name):
        """Convert a value submitted from an HTML form.

        'request' -- The 'WebRequest' containing a value corresponding
        to this field.

        'name' -- The name corresponding to this field in the 'request'.
        
        returns -- A pair '(value, redisplay)'.  'value' is the value
        for this field, as indicated in 'request'.  'redisplay' is true
        if and only if the form should be redisplayed, rather than
        committed.  If an error occurs, an exception is thrown."""

        return (self.ParseTextValue(request[name]), 0)


    def ParseTextValue(self, value):
        """Parse a value represented as a string.

        'value' -- A string representing the value.

        returns -- The corresponding field value."""

        raise NotImplemented
    
        
    def FormEncodeValue(self, value):
        """Return an encoding for 'value' to store in HTML forms.

        The form-encoded value is used to represent a value when it is
        an element in a set.  The options in the HTML list element
        representing the set store these encodings as their values."""

        return urllib.quote_plus(repr(value))


    def FormDecodeValue(self, encoding):
        """Decode the HTML form-encoded 'encoding' and return a value."""

        return eval(urllib.unquote_plus(value))


    def GetValueFromDomNode(self, node, attachment_store):
        """Return a value for this field represented by DOM 'node'.

        This method does not validate the value for this particular
        instance; it only makes sure the node is well-formed, and
        returns a value of the correct Python type.

        'node' -- The DOM node that is being evaluated.

        'attachment_store' -- For attachments, the store that should be
        used.
        
        raises -- 'DomNodeError' if the node's structure or contents are
        incorrect for this field."""

        raise NotImplementedError


    def MakeDomNodeForValue(self, value, document):
        """Generate a DOM element node for a value of this field.

        'value' -- The value to represent.

        'document' -- The containing DOM document node."""

        raise NotImplementedError


    def GetHelp(self):
        """Generate help text about this field in structured text format."""

        raise NotImplementedError
        

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
        <p>Refer to this field as <tt>%s</tt> in Python expressions.</p>
        ''' % (self.GetTitle(), description, help, self.GetName(), )


    def GenerateEditWebPage(self, request, submit_request):
        """Generate a web page for editing a field.

        'request' -- The request in response to which this page is being
        generated.

        'submit_request' -- The 'WebRequest' to which the field edit
        form should be submitted.

        The 'UpdateFromRequest' method should generally be used to
        process the submission request."""

        return FieldEditPage(self, submit_request)(request)


    def IsComputed(self):
        """Returns true if this field is computed automatically.

        returns -- True if this field is computed automatically.  A
        computed field is never displayed to users and is not stored
        should not be stored; the class containing the field is
        responsible for recomputing it as necessary."""

        return self.IsProperty("computed")
        
        
    def _MakeTextPropertyControl(self, property_name):
        """Generate HTML inputs for a text-valued property.

        'property_name' -- The name of the property.

        returns -- HTML text for form inputs suitable for use in
        'MakePropertyControls'."""

        return '<input type="text" name="%s%s" size="40" value="%s"/>' \
               % (query_field_property_prefix, property_name,
                  self.GetProperty(property_name))


    def _MakeBooleanPropertyControl(self, property_name):
        """Generate HTML inputs for a boolean-valued property.

        'property_name' -- The name of the property.

        returns -- HTML text for form inputs suitable for use in
        'MakePropertyControls'."""

        property_value = self.GetProperty(property_name)
        assert property_value in ["true", "false"]
        if property_value == "true":
            true_checked = "checked"
            false_checked = ""
        else:
            true_checked = ""
            false_checked = "checked"
        return '''
        <input type="radio" name="%s%s" value="true" %s />&nbsp;true
        &nbsp;&nbsp;&nbsp;
        <input type="radio" name="%s%s" value="false" %s />&nbsp;false
        ''' % (query_field_property_prefix, property_name, true_checked,
               query_field_property_prefix, property_name, false_checked)


    def MakePropertyControls(self):
        """Return controls for editing the properties of this field.

        returns -- A map from property names to strings containing HTML
        source for Web form controls for editing the corresponding
        property.

        Not all properties understood by the field need be included in
        the map.

        The names of the form inputs for property values should
        generally be of the form '"%s%s" % (query_field_property_prefix,
        field_name)'.

        A subclass which override this method should include map entries
        added by its base class version in its own return value."""

        return {
            "title":
                self._MakeTextPropertyControl("title"),

            # The name is made read-only here.  It should not be changed
            # after the field has been created, to preserve referential
            # integrity. 
            "name":
                self.GetProperty("name"),

            "description":
                '''<textarea name="%sdescription"
                             cols="40"
                             rows="8">%s</textarea>'''
                % (query_field_property_prefix, self.GetDescription()),

            "hidden":
                self._MakeBooleanPropertyControl("hidden"),

            "read_only":
                self._MakeBooleanPropertyControl("read_only"),

            }


    def MakeDomNode(self, document):
        """Construct a DOM element node describing this field.

        'document' -- A DOM document object in which to create the node.

        returns -- A DOM node for a "field" element."""

        # Construct the main element node.
        element = document.createElement("field")
        # Store the field name as an attribute.
        element.setAttribute("name", self.GetName())
        # Store the Python class name of this field.
        class_element = xmlutil.create_dom_text_element(
            document, "class", self.__class__.__name__)
        element.appendChild(class_element)
        # Store the default value.
        default_value = self.GetDefaultValue()
        default_value_element = \
            self.MakeDomNodeForValue(default_value, document)
        default_element = document.createElement("default-value")
        default_element.appendChild(default_value_element)
        element.appendChild(default_element)

        # Create an element for each property.
        for name, value in self.__properties.items():
            if name == "name":
                continue
            property_element = xmlutil.create_dom_text_element(
                document, "property", str(value))
            property_element.setAttribute("name", name)
            element.appendChild(property_element)

        return element



########################################################################

class IntegerField(Field):
    """A signed integer field."""

    def __init__(self, name, default_value=0, **properties):
        """Create an integer field.

        The field must be able to represent a 32-bit signed
        integer.

        'default_value' -- The default value for the field."""

        # Perform base class initialization.
        apply(Field.__init__, (self, name, default_value), properties)


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


    def ParseTextValue(self, value):
        try:
            return int(value)
        except:
            raise qm.common.QMException, \
                  qm.error("invalid integer field value")


    def GetValueFromDomNode(self, node, attachment_store):
        # Make sure 'node' is an '<integer>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "integer":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="integer",
                                   wrong_tag=node.tagName)
        # Retrieve the contained text.
        value = xmlutil.get_dom_text(node)
        # Convert it to an integer.
        try:
            return int(value)
        except ValueError:
            raise DomNodeError, \
                  diagnostic.error("dom bad integer", value=value)


    def MakeDomNodeForValue(self, value, document):
        return xmlutil.create_dom_text_element(document, "integer",
                                               str(value))


    def GetHelp(self):
        help = '''
            This field takes an integer value between %d and %d inclusive.

            The default value of this field is %d.
        ''' % (-sys.maxint - 1, sys.maxint, self.GetDefaultValue())
        return help
    


########################################################################

class TextField(Field):
    """A field that contains text."""

    property_declarations = Field.property_declarations + [
        PropertyDeclaration(
            name="multiline",
            description="""If false, a value for this field is a single
            line of text.  If true, multi-line text is allowed.""",
            default_value="false"
            ),

        PropertyDeclaration(
            name="structured",
            description="""If true, the field contains structured
            text.""",
            default_value="false"
            ),

        PropertyDeclaration(
            name="verbatim",
            description="""If true, the contents of the field are
            treated as preformatted text.""",
            default_value="false"
            ),

        PropertyDeclaration(
            name="not_empty_text",
            description="""The value of this field is considered invalid
            if it empty or composed only of whitespace.""",
            default_value="false"
            ),

        ]


    def __init__(self, name, default_value="", **properties):
        """Create a text field."""

        # Perform base class initialization.
        apply(Field.__init__, (self, name, default_value), properties)


    def CompareValues(self, value1, value2):
        # First, compare strings case-insensitively.
        comparison = cmp(string.lower(value1), string.lower(value2))
        if comparison == 0:
            # If the strings are the same ignoring case, re-compare them
            # taking case into account.
            return cmp(value1, value2)
        else:
            return comparison


    def GetTypeDescription(self):
        return "a string"
    

    def Validate(self, value):
        # Be forgiving, and try to convert 'value' to a string if it
        # isn't one.
        value = str(value)
        # Clean up unless it's a verbatim string.
        if not self.IsProperty("verbatim"):
            # Remove leading whitespace.
            value = string.lstrip(value)
        # If this field has the not_empty_text property set, make sure the
        # value complies.
        if self.IsProperty("not_empty_text") and value == "":
            raise ValueError, \
                  qm.error("empty text field value",
                           field_title=self.GetTitle()) 
        # If this is not a multi-line text field, remove line breaks
        # (and surrounding whitespace).
        if not self.IsProperty("multiline"):
            value = re.sub(" *\n+ *", " ", value)
        return value


    def FormatValueAsText(self, value, columns=72):
        if self.IsProperty("structured"):
            return structured_text.to_text(value, width=columns)
        elif self.IsProperty("verbatim"):
            return value
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
            if self.IsProperty("multiline"):
                result = '<textarea cols="64" rows="8" name="%s">' \
                         '%s</textarea>' \
                         % (name, web.escape(value))
            else:
                result = \
                    '<input type="text" size="40" name="%s" value="%s"/>' \
                    % (name, web.escape(value))
            # If this is a structured text field, add a note to that
            # effect, so users aren't surprised.
            if self.IsProperty("structured"):
                result = result \
                + '<br><font size="-1">This is a ' \
                + qm.web.make_help_link_html(
                    qm.structured_text.html_help_text,
                    "structured text") \
                + 'field.</font>'
            return result

        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, web.escape(value))            

        elif style == "brief":
            if self.IsProperty("structured"):
                # Use only the first line of text.
                value = string.split(value, "\n", 1)
                value = web.format_structured_text(value[0])
            else:
                # Replace all whitespace with ordinary space.
                value = re.sub(r"\s", " ", value)

            # Truncate to 80 characters, if it's longer.
            if len(value) > 80:
                value = value[:80] + "..."

            if self.IsProperty("verbatim"):
                # Put verbatim text in a <tt> element.
                return '<tt>%s</tt>' % web.escape(value)
            elif self.IsProperty("structured"):
                # It's already formatted as HTML; don't escape it.
                return value
            else:
                # Other text set normally.
                return web.escape(value)

        elif style == "full":
            if self.IsProperty("verbatim"):
                # Wrap lines before escaping special characters for
                # HTML.  Use a special tag to indicate line breaks.  If
                # we were to escape first, line lengths would be
                # computed using escape codes rather than visual
                # characters. 
                break_delimiter = "#@LINE$BREAK@#"
                value = common.wrap_lines(value, columns=80,
                                          break_delimiter=break_delimiter)
                # Now escape special characters.
                value = web.escape(value)
                # Replace the line break tag with visual indication of
                # the break.
                value = string.replace(value,
                                       break_delimiter, r"<blink>\</blink>")
                # Place verbatim text in a <pre> element.
                return '<pre>%s</pre>' % value
            elif self.IsProperty("structured"):
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


    def ParseFormValue(self, request, name):

        # HTTP specifies text encodints are CR/LF delimited; convert to
        # the One True Text Format (TM).
        return (self.ParseTextValue(qm.convert_from_dos_text(request[name])),
                0)
    

    def ParseTextValue(self, value):
        return value

    
    def GetValueFromDomNode(self, node, attachment_store):
        # Make sure 'node' is a '<text>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "text":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="text",
                                   wrong_tag=node.tagName)
        return xmlutil.get_dom_text(node)


    def MakeDomNodeForValue(self, value, document):
        return xmlutil.create_dom_text_element(document, "text", value)


    def GetHelp(self):
        help = """
            A text field.  """
        if self.IsProperty("structured"):
            help = help + '''
            The text is interpreted as structured text, and formatted
            appropriately for the output device.  See "Structured Text
            Formatting
            Rules":http://www.python.org/sigs/doc-sig/stext.html for
            more information.  '''
        elif self.IsProperty("verbatim"):
            help = help + """
            The text is stored verbatim; whitespace and indentation are
            preserved.  """
        if self.IsProperty("not_empty_text"):
            help = help + """
            This field may not be empty.  """
        help = help + """
            The default value of this field is "%s".
            """ % self.GetDefaultValue()
        return help


    def MakePropertyControls(self):
        # Start the with the base controls.
        controls = Field.MakePropertyControls(self)
        # Add controls for our own properties.
        controls.update({
            "multiline":
                self._MakeBooleanPropertyControl("multiline"),

            "structured":
                self._MakeBooleanPropertyControl("structured"),

            "verbatim":
                self._MakeBooleanPropertyControl("verbatim"),

            "not_empty_text":
                self._MakeBooleanPropertyControl("not_empty_text"),

            })

        return controls



########################################################################

class TupleField(Field):
    """A 'TupleField' contains zero or more other 'Field's.

    The contained fields may be of different types."""

    def __init__(self, name, fields, **properties):
        """Construct a new 'TupleField'.

        'fields' -- The fields contained in the tuple."""

        default_value = map(lambda f: f.GetDefaultValue(), fields)
        Field.__init__(self, name, default_value, **properties)
        self.__fields = fields


    def Validate(self, value):

        assert len(value) == len(self.__fields)
        map(lambda f, v: f.Validate(v),
            self.__fields, value)


    def FormatValueAsHtml(self, value, style, name = None):

        # Format the field as a multi-column table.
        html = '<table border="0" cellpadding="0"><tr>'
        for f, v in map(None, self.__fields, value):
            if name is not None:
                element_name = name + "_" + f.GetName()
            else:
                element_name = None
            html += "<td><b>" + f.GetTitle() + "</b>:</td>"
            html += ("<td>" 
                     + f.FormatValueAsHtml(v, style, element_name)
                     + "</td>")
        html += "</tr></table>"
        # Add a dummy field with the desired 'name'.
        if name is not None:
            html += '<input type="hidden" name="%s" />' % name
        return html


    def ParseFormValue(self, request, name):

        value = []
        redisplay = 0
        for f in self.__fields:
            v, r = f.ParseFormValue(request, name + "_" + f.GetName())
            value.append(v)
            if r:
                redisplay = 1

        return (value, redisplay)
            

    def GetValueFromDomNode(self, node, attachment_store):

        values = []
        for f, element in map(None, self.__fields, node.childNodes):
            values.append(f.GetValueFromDomNode(element, attachment_store))

        return values


    def MakeDomNodeForValue(self, value, document):

        element = document.createElement("tuple")
        for f, v in map(None, self.__fields, value):
            element.appendChild(f.MakeDomNodeForValue(v, document))

        return element
    

    def GetHelp(self):

        help = ""
        need_space = 0
        for f in self.__fields:
            if need_space:
                help += "\n"
            else:
                need_space = 1
            help += "** " + f.GetTitle() + " **\n\n"
            help += f.GetHelp()

        return help
    

    
class SetField(Field):
    """A field containing zero or more instances of some other field.

    All contents must be of the same field type.  A set field may not
    contain sets.

    The default field value is set to an empty set."""

    set_property_declarations = [
        PropertyDeclaration(
            name="not_empty_set",
            description="""If true, this field may not be empty,
            i.e. the value of this field must contain at least one
            element.""",
            default_value="false"
            ),
        
        ]

    def __init__(self, contained):
        """Create a set field.

        The name of the contained field is taken as the name of this
        field.

        'contained' -- An 'Field' instance describing the
        elements of the set. 

        raises -- 'ValueError' if 'contained' is a set field.

        raises -- 'TypeError' if 'contained' is not a 'Field'."""

        # A set field may not contain a set field.
        if isinstance(contained, SetField):
            raise ValueError, \
                  "A set field may not contain a set field."
        if not isinstance(contained, Field):
            raise TypeError, "A set must contain another field."
        # Use the properties from the contained field, rather than
        # making a different set.
        self._Field__properties = contained._Field__properties
        # Remeber the contained field type.
        self.__contained = contained
        # Masquerade property declarations as for contained field.
        self.property_declarations = contained.property_declarations \
                                     + self.set_property_declarations
        # Set the default field value to the empty set.
        self.SetDefaultValue([])


    def CompareValues(self, value1, value2):
        # Sort set values by length.
        comparison = cmp(len(value1), len(value2))
        # If they're the same length, compare the contents themselves.
        if comparison == 0:
            return cmp(value1, value2)
        else:
            return comparison


    def GetTypeDescription(self):
        return "a sequence; each element is %s" \
               % self.GetContainedField().GetTypeDescription()
    

    def Validate(self, value):
        # If this field has the not_empty_set property set, make sure
        # the value complies.
        if self.IsProperty("not_empty_set") and len(value) == 0:
            raise ValueError, \
                  qm.error("empty set field value",
                           field_title=self.GetTitle()) 
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
            formatted \
                = map(lambda v: contained_field.FormatValueAsHtml(v, style),
                      value)
            if style == "brief":
                # In the brief style, list elements separated by commas.
                separator = ", "
            else:
                # In the full style, list elements one per line.
                separator = "<br>\n"
            return string.join(formatted, separator)

        elif style in ["new", "edit", "hidden"]:
            # Create a table to represent the set.
            html = '''<table border="0" cellpadding="0" cellspacing="0">
                        <tbody>\n'''
            element_number = 0
            for element in value:
                html += "<tr><td>"
                element_name = name + "_%d" % element_number
                checkbox_name = element_name + "_remove"
                if style == "edit":
                    html += \
                       ('''<input type="checkbox" name="%s" /></td><td>'''
                        % checkbox_name)
                html += contained_field.FormatValueAsHtml(element,
                                                          style,
                                                          element_name)
                html += "</td></tr>\n"
                element_number += 1
            html += "</tbody></table>\n"
            if style == "edit":
                # The action field is used to keep track of whether the
                # "Add" or "Remove" button has been pushed.  It would be
                # much nice if we could use JavaScript to update the
                # table, but Netscape 4, and even Mozilla 1.0, do not
                # permit that.  Therefore, we have to go back to the server.
                action_field \
                    = '''<input type="hidden" name="%s" value=""
                            default_value=""  />''' % name
                add_button \
                    = '''<input type="button" value="Add Another"
                            onclick="%s.value = 'add'; submit();" />''' \
                      % name
                remove_button \
                    = '''<input type="button" value="Remove Selected"
                            onclick="%s.value = 'remove'; submit();" />''' \
                      % name
                button_table \
                    = ('''<table border="0" cellpadding="0" cellspacing="0">
                            <tbody>\n'''
                       + " <tr><td>" + add_button + "</td></tr>\n"
                       + " <tr><td>" + remove_button + "</td></tr>\n"
                       + "</tbody></table>")
                html += action_field + button_table
            return html


    def ParseFormValue(self, request, name):

        values = []

        contained_field = self.GetContainedField()

        # See if the user wants to add or remove elements to the set.
        action = request[name]

        # Loop over the entries for each of the elements, adding them to
        # the set.
        element = 0
        while 1:
            element_name = name + "_%d" % element
            if not request.has_key(element_name):
                break
            if not (action == "remove"
                    and request.get(element_name + "_remove") == "on"):
                v, r = contained_field.ParseFormValue(request, element_name)
                values.append(v)
                if r:
                    redisplay = 1
            element += 1

        # If the user requested another element, add to the set.
        if action == "add":
            redisplay = 1
            values.append(contained_field.GetDefaultValue())
        elif action == "remove":
            redisplay = 1
        else:
            redisplay = 0

        # Remove entries from the request that might cause confusion
        # when the page is redisplayed.
        names = []
        for n, v in request.items():
            if n[:len(name)] == name:
                names.append(n)
        for n in names:
            del request[n]
            
        return (values, redisplay)


    def GetValueFromDomNode(self, node, attachment_store):
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
        fn = lambda n, f=contained_field, s=attachment_store: \
             f.GetValueFromDomNode(n, s)
        return map(fn,
                   filter(lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE,
                          node.childNodes))


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
        
            <p>Add a new element to the set by clicking the
            <i>Add</i> button.  The new element will have a default
            value until you change it.  To remove elements from the
            set, select them by checking the boxes on the left side of
            the form.   Then, click the <i>Remove</i> button.</p>
            """
        return help


    def MakePropertyControls(self):
        # Use property controls for the contained field.
        controls = self.GetContainedField().MakePropertyControls()
        # Add controls for properties in 'set_property_declarations'.
        controls["not_empty_set"] = \
            self._MakeBooleanPropertyControl("not_empty_set")
        return controls


    def MakeDomNode(self, document):
        # Construct the basic 'Field' DOM node.
        node = Field.MakeDomNode(self, document)
        # Properties will be specified by the contained field, so remove
        # them here.
        for property_node in node.getElementsByTagName("property"):
            node.removeChild(property_node)
        # Construct an element for the contained field.
        contained_node = self.GetContainedField().MakeDomNode(document)
        node.appendChild(contained_node)

        return node
    


########################################################################

class UploadAttachmentPage(web.DtmlPage):
    """DTML context for generating upload-attachment.dtml."""

    __next_temporary_location = 0

    def __init__(self, 
                 field_name,
                 encoding_name,
                 summary_field_name,
                 in_set=0):
        """Create a new page object.

        'field_name' -- The user-visible name of the field for which an
        attachment is being uploaded.

        'encoding_name' -- The name of the HTML input that should
        contain the encoded attachment.

        'summary_field_name' -- The name of the HTML input that should
        contain the user-visible summary of the attachment.

        'in_set' -- If true, the attachment is being added to an
        attachment set field."""

        web.DtmlPage.__init__(self, "attachment.dtml")
        # Use a brand-new location for the attachment data.
        self.location = attachment.make_temporary_location()
        self.store = "%d" % attachment.temporary_store.GetIndex()
        # Set up properties.
        self.field_name = field_name
        self.encoding_name = encoding_name
        self.summary_field_name = summary_field_name
        self.in_set = in_set


    def MakeSubmitUrl(self):
        """Return the URL for submitting this form."""

        return self.request.copy(AttachmentField.upload_url).AsUrl()



class AttachmentField(Field):
    """A field containing a file attachment.

    Note that the 'FormatValueAsHtml' method uses a popup upload form
    for uploading new attachment.  The web server must be configured to
    handle the attachment submission requests.  See
    'attachment.register_attachment_upload_script'."""

    upload_url = "/attachment-upload"
    """The URL used to upload data for an attachment.

    The upload request will include these query arguments:

      'location' -- The location at which to store the attachment data.

      'file_data' -- The attachment data.

    """

    download_url = "/attachment-download"
    """The URL used to download an attachment.

    The download request will include this query argument:

      'location' -- The location in the attachment store from which to
      retrieve the attachment data.

    """


    def __init__(self, name, **properties):
        """Create an attachment field.

        Sets the default value of the field to 'None'."""

        # Perform base class initialization. 
        apply(Field.__init__, (self, name, None), properties)


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
            location = value.GetLocation() 
            mime_type = value.GetMimeType()
            description = value.GetDescription()
            file_name = value.GetFileName()
        else:
            raise ValueError, "'value' must be 'None' or an 'Attachment'"

        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "full" or style == "brief":
            if value is None:
                return "None"
            # Link the attachment description to the data itself.
            download_url = web.WebRequest(self.download_url,
                                          location=location,
                                          mime_type=mime_type).AsUrl()
            # Here's a nice hack.  If the user saves the attachment to a
            # file, browsers (some at least) guess the default file name
            # from the URL by taking everything following the final
            # slash character.  So, we add this bogus-looking argument
            # to fool the browser into using our file name.
            download_url = download_url + \
                           "&=/" + urllib.quote_plus(file_name)
            
            result = '<a href="%s">%s</a>' \
                     % (download_url, description)
            # For the full style, display the MIME type.
            if style == "full":
                result = result + ' (%s)' % (mime_type)
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
            upload_page = UploadAttachmentPage(self.GetTitle(),
                                               name,
                                               summary_field_name)()
            
            # Generate controls for this form.
            
            # A text control for the user-visible summary of the
            # attachment.  The "readonly" property isn't supported in
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
            upload_button \
                = qm.web.make_button_for_cached_popup("Upload",
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

            return result

        else:
            raise ValueError, style


    def ParseFormValue(self, request, name):

        return (self.FormDecodeValue(request[name]), 0)


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
            value.GetDescription(),
            value.GetMimeType(),
            value.GetLocation(),
            ("%d" % value.GetStore().GetIndex()),
            value.GetFileName(),
            )
        # Each part is URL-encoded.
        map(urllib.quote, parts)
        # The parts are joined into a semicolon-delimited list.
        return string.join(parts, ";")


    def FormDecodeValue(self, encoding):
        """Decode the HTML form-encoded 'encoding' and return a value."""

        # An empty string represnts a missing attachment, which is OK.
        if string.strip(encoding) == "":
            return None
        # The encoding is a semicolon-separated sequence indicating the
        # relevant information about the attachment.
        parts = string.split(encoding, ";")
        # Undo the URL encoding of each component.
        parts = map(urllib.unquote, parts)
        # Unpack the results.
        description, mime_type, location, store, file_name = parts
        # The store is reprsented by an index.  Retrieve the actual
        # store itself.
        store = attachment.get_attachment_store(string.atoi(store))
        # Create the attachment.
        return attachment.Attachment(mime_type, description,
                                     file_name, location, store)


    def FormatSummary(self, attachment):
        """Generate a user-friendly summary for 'attachment'.

        This value is used when generating the form.  It can't be
        editied."""

        if attachment is None:
            return "None"
        else:
            return "%s (%s; %s)" \
                   % (attachment.GetDescription(),
                      attachment.GetFileName(),
                      attachment.GetMimeType())


    def GetValueFromDomNode(self, node, attachment_store):
        # Make sure 'node' is an "attachment" element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "attachment":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="attachment",
                                   wrong_tag=node.tagName)
        return attachment.from_dom_node(node, attachment_store)


    def MakeDomNodeForValue(self, value, document):
        return attachment.make_dom_node(value, document)


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

class EnumerationField(TextField):
    """A field that contains an enumeral value.

    The enumeral value is selected from an enumerated set of values.
    An enumeral field uses the following properties:

    enumeration -- A mapping from enumeral names to enumeral values.
    Names are converted to strings, and values are stored as integers.

    ordered -- If non-zero, the enumerals are presented to the user
    ordered by value."""

    property_declarations = TextField.property_declarations + [
        PropertyDeclaration(
            name="enumerals",
            description="""The enumerals allowed for this field.
            Enumerals are presented in the order listed.""",
            default_value="[]"),

        ]

    def __init__(self,
                 name,
                 default_value=None,
                 enumerals=[],
                 **properties):
        """Create an enumeration field.

        'enumerals' -- A sequence of strings of available
        enumerals.

        'default_value' -- The default value for this enumeration.  If
        'None', the first enumeral is used."""

        # If we're handed an encoded list of enumerals, decode it.
        if isinstance(enumerals, types.StringType):
            enumerals = string.split(enumerals, ",")
        # Make sure the default value is legitimate.
        if not default_value in enumerals and len(enumerals) > 0:
            default_value = enumerals[0]
        # Perform base class initialization.
        apply(TextField.__init__, (self, name, default_value), properties)
        # Set the enumerals.
        self.SetEnumerals(enumerals)


    def CompareValues(self, value1, value2):
        # Sort enumerals by position in the enumeration.
        enumerals = self.GetEnumerals()
        if value1 not in enumerals or value2 not in enumerals:
            return 1
        return cmp(enumerals.index(value1), enumerals.index(value2))


    def GetTypeDescription(self):
        enumerals = self.GetEnumerals()
        return 'an enumeration of "%s"' % string.join(enumerals, '," "')


    def Validate(self, value):
        value = str(value)
        enumerals = self.GetEnumerals()
        if value in enumerals:
            return value
        else:
            values = map(lambda (k, v): "%s (%d)" % (k, v), enumerals)
            raise ValueError, \
                  qm.error("invalid enum value",
                           value=value,
                           field_title=self.GetTitle(),
                           values=string.join(values, ", "))


    def SetProperty(self, enumeral_name, value):
        # Call the base implementation.
        Field.SetProperty(self, enumeral_name, value)
            

    def SetEnumerals(self, enumerals):
        """Set the list of valid enumerals.

        'enumerals' -- A list of strings representing enumeral names."""

        self.SetProperty("enumerals", string.join(enumerals, ","))


    def GetEnumerals(self):
        """Return a sequence of enumerals.

        returns -- A sequence consisting of string enumerals objects, in
        the appropriate order."""

        enumerals = self.GetProperty("enumerals")
        if enumerals == "":
            return []
        else:
            return string.split(enumerals, ",")


    def FormatValueAsHtml(self, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = self.GetDefaultValue()
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            enumerals = self.GetEnumerals()
            if len(enumerals) == 0:
                # No available enumerals.  Don't let the user change
                # anything. 
                self.FormatValueAsHtml(value, "brief", name)
            else:
                return qm.web.make_select(name, enumerals, value, str, str)

        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, value) 

        elif style == "full" or style == "brief":
            return value

        else:
            raise ValueError, style


    def GetValueFromDomNode(self, node, attachment_store):
        # Make sure 'node' is an '<enumeral>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "enumeral":
            raise DomNodeError, \
                  diagnostic.error("dom wrong tag for field",
                                   name=self.GetName(),
                                   right_tag="enumeral",
                                   wrong_tag=node.tagName)
        # Extract the value.
        return xmlutil.get_dom_text(node)


    def MakeDomNodeForValue(self, value, document):
        # Store the name of the enumeral.
        return xmlutil.create_dom_text_element(
            document, "enumeral", str(value))


    def GetHelp(self):
        enumerals = self.GetEnumerals()
        help = """
        An enumeration field.  The value of this field must be one of a
        preselected set of enumerals.  The enumerals for this field are,

        """
        for enumeral in enumerals:
            help = help + '            * "%s"\n\n' % enumeral
        help = help + '''

        The default value of this field is "%s".
        ''' % str(self.GetDefaultValue())
        return help


    def MakePropertyControls(self):
        # Start with controls for base-class properties.
        controls = TextField.MakePropertyControls(self)
        # These text field controls aren't relevant to enumerations.
        controls["structured"] = None
        controls["verbatim"] = None
        controls["not_empty_text"] = None

        # Now to add controls for editing the set of available
        # enumerals.  Construct query field names.
        field_name = query_field_property_prefix + "enumerals"
        select_name = "_set_" + field_name
        # Generate the page for entering a new enumeral name.
        add_page = web.DtmlPage("add-enumeral.dtml",
                                field_name=field_name,
                                select_name=select_name)()
        url = qm.web.cache_page(add_page).AsUrl()
        # Start with the current set of enumerals.  'make_set_control'
        # expects pairs of elements.
        initial_elements = map(lambda e: (e, e), self.GetEnumerals())
        # Construct the controls.
        controls["enumerals"] = web.make_set_control(
            form_name="form",
            field_name=field_name,
            add_page=url,
            initial_elements=initial_elements,
            ordered=1)

        return controls



class BooleanField(EnumerationField):
    """A field containing a boolean value.

    The enumeration contains two values: true and false."""

    def __init__(self, name, default_value = None, **properties):

        # Construct the base class.
        EnumerationField.__init__(self, name, default_value,
                                  ["true", "false"], **properties)

        

class ChoiceField(TextField):
    """An 'ChoiceField' allows choosing one of several values.

    An 'ChoiceField' is similar to an 'EnumerationField' -- but the
    choices for an 'ChoiceField' are computed dynamically, rather than
    chosen statically."""

    def FormatValueAsHtml(self, value, style, name = None):

        if style not in ("new", "edit"):
            return qm.fields.TextField.FormatValueAsHtml(self, value,
                                                         style, name)

        # For an editable field, give the user a choice of available
        # resources.
        result = "<select"
        if name:
            result += ' name="%s"' % name
        result += ">"
        for r in self.GetItems():
            result += '<option value="%s"' % r
            if r == value:
                result += ' selected="1"'
            result += '>%s</option>' % r
        result += "</select>"

        return result
    

    def GetItems(self):
        """Return the options from which to choose.

        returns -- A sequence of strings, each of which will be
        presented as a choice for the user."""

        raise NotImplementedError
        
########################################################################

class TimeField(IntegerField):
    """A field containing a date and time.

    The data and time is stored as seconds since the start of the UNIX
    epoch, UTC (the semantics of the standard 'time' function), with
    one-second precision.  User representations of 'TimeField' fields
    show one-minue precision."""

    def __init__(self, name, **properties):
        """Create a time field.

        The field is given a default value for this field is 'None', which
        corresponds to the current time when the field value is first
        created."""

        # Perform base class initalization.
        apply(IntegerField.__init__, (self, name), properties)
        # Set the default value.
        self.default_value = None


    def GetTypeDescription(self):
        return "a date/time (right now, it is %s)" \
               % self.FormatValueAsText(self.GetCurrentTime())


    def FormatValueAsText(self, value, columns=72):
        if value is None:
            return "now"
        else:
            return qm.common.format_time(value, local_time_zone=1)


    def FormatValueAsHtml(self, value, style, name=None):
        value = self.FormatValueAsText(value)

        if style == "new" or style == "edit":
            return '<input type="text" size="8" name="%s" value="%s"/>' \
                   % (name, value)
        elif style == "full" or style == "brief":
            # The time is formatted in three parts: the date, the time,
            # and the time zone.  Replace the space between the time and
            # the time zone with a non-breaking space, so that if the
            # time is broken onto two lines, it is broken between the
            # date and the time.
            date, time, time_zone = string.split(value, " ")
            return date + " " + time + "&nbsp;" + time_zone
        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s"/>' \
                   % (name, value)
        else:
            raise ValueError, style


    def ParseTextValue(self, value):
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

    def __init__(self, name, **properties):
        default_user_id = user.database.GetDefaultUserId()
        apply(TextField.__init__,
              (self, name, default_user_id),
              properties)


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



class PythonField(Field):
    """A 'PythonField' stores a Python value.

    All 'PythonField's are computed; they are never written out, nor can
    they be specified directly by users.  They are used in situations
    where the value of the field is specified programatically by the
    system."""

    def __init__(self, name, default_value = None):

        Field.__init__(self, name, default_value, computed = "true")
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

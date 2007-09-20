########################################################################
#
# File:   fields.py
# Author: Alex Samuel
# Date:   2001-03-05
#
# Contents:
#   General type system for user-defined data constructs.
#
# Copyright (c) 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""A 'Field' determines how data is displayed and stored.

A 'Field' is a component of a data structure.  Every 'Field' has a type.
For example, an 'IntegerField' stores a signed integer while a
'TextField' stores a string.

The value of a 'Field' can be represented as HTML (for display in the
GUI), or as XML (when written to persistent storage).  Every 'Field' can
create an HTML form that can be used by the user to update the value of
the 'Field'.

Every 'Extension' class has a set of arguments composed of 'Field'.  An
instance of that 'Extension' class can be constructed by providing a
value for each 'Field' object.  The GUI can display the 'Extension'
object by rendering each of the 'Field' values as HTML.  The user can
change the value of a 'Field' in the GUI, and then write the 'Extension'
object to persistent storage.

Additional derived classes of 'Field' can be created for use in
domain-specific situations.  For example, the QMTest 'Test' class
defines a derived class which allows the user to select from among a set
of test names."""

########################################################################
# imports
########################################################################

import attachment
import common
import formatter
import htmllib
import os
import re
import qm
import string
import StringIO
import structured_text
import sys
import time
import tokenize
import types
import urllib
import web
import xml.dom
import xmlutil

########################################################################
# classes
########################################################################

class Field(object):
    """A 'Field' is a named, typed component of a data structure."""

    form_field_prefix = "_field_"
    
    def __init__(self,
                 name = "",
                 default_value = None,
                 title = "",
                 description = "",
                 hidden = "false",
                 read_only = "false",
                 computed = "false"):
        """Create a new (generic) field.

        'name' -- The name of the field.

        'default_value' -- The default value for this field.

        'title' -- The name given this field when it is displayed in
        user interfaces.

        'description' -- A string explaining the purpose of this field.
        The 'description' must be provided as structured text.  The
        first line of the structured text must be a one-sentence
        description of the field; that line is extracted by
        'GetBriefDescription'.

        'hidden' -- If true, this field is for internal puprpose only
        and is not shown in user interfaces.

        'read_only' -- If true, this field may not be modified by users.

        'computed' -- If true, this field is computed automatically.
        All computed fields are implicitly hidden and implicitly
        read-only.

        The boolean parameters (such as 'hidden') use the convention
        that true is represented by the string '"true"'; any other value
        is false.  This convention is a historical artifact."""

        self.__name = name
        # Use the name as the title, if no other was specified.
        if not title:
            self.__title = name
        else:
            self.__title = title
        self.__description = description
        self.__hidden = hidden == "true"
        self.__read_only = read_only == "true"
        self.__computed = computed == "true"

        # All computed fields are also read-only and hidden.
        if (self.IsComputed()):
            self.__read_only = 1
            self.__hidden = 1

        self.__default_value = default_value


    def SetName(self, name):
        """Set the name of the field."""

        # We assume that if title==name the title
        # was not given and so defaulted to name.
        # Keep it in sync with name in that case.
        if (self.__name == self.__title):
            self.__title = name
        self.__name = name


    def GetName(self):
        """Return the name of the field."""

        return self.__name


    def GetDefaultValue(self):
        """Return the default value for this field."""

        return common.copy(self.__default_value)


    def GetTitle(self):
        """Return the user-friendly title of the field."""

        return self.__title


    def GetDescription(self):
        """Return a description of this field.

        This description is used when displaying detailed help
        information about the field."""

        return self.__description


    def GetBriefDescription(self):
        """Return a brief description of this field.

        This description is used when prompting for input, or when
        displaying the current value of the field."""

        # Get the complete description.
        description = self.GetDescription()
        # Return the first paragraph.
        return structured_text.get_first(description)

        
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


    def GetSubfields(self):
        """Returns the sequence of subfields contained in this field.

        returns -- The sequence of subfields contained in this field.
        If there are no subfields, an empty sequence is returned."""

        return ()

        
    def IsComputed(self):
        """Returns true if this field is computed automatically.

        returns -- True if this field is computed automatically.  A
        computed field is never displayed to users and is not stored
        should not be stored; the class containing the field is
        responsible for recomputing it as necessary."""

        return self.__computed


    def IsHidden(self):
        """Returns true if this 'Field' should be hidden from users.

        returns -- True if this 'Field' should be hidden from users.
        The value of a hidden field is not displayed in the GUI."""

        return self.__hidden


    def IsReadOnly(self):
        """Returns true if this 'Field' cannot be modified by users.

        returns -- True if this 'Field' cannot be modified by users.
        The GUI does not allow users to modify a read-only field."""

        return self.__read_only

    ### Output methods.
    
    def FormatValueAsText(self, value, columns=72):
        """Return a plain text rendering of a 'value' for this field.

        'columns' -- The maximum width of each line of text.

        returns -- A plain-text string representing 'value'."""

        # Create a file to hold the result.
        text_file = StringIO.StringIO()
        # Format the field as HTML.
        html_file = StringIO.StringIO(self.FormatValueAsHtml(None,
                                                             value,
                                                             "brief"))

        # Turn the HTML into plain text.
        parser = htmllib.HTMLParser(formatter.AbstractFormatter
                                    (formatter.DumbWriter(text_file,
                                                          maxcol = columns)))
        parser.feed(html_file)
        parser.close()
        text = text_file.getValue()

        # Close the files.
        html_file.close()
        text_file.close()
        
        return text
    

    def FormatValueAsHtml(self, server, value, style, name=None):
        """Return an HTML rendering of a 'value' for this field.

        'server' -- The 'WebServer' in which the HTML will be
        displayed.
        
        'value' -- The value for this field.  May be 'None', which
        renders a default value (useful for blank forms).

        'style' -- The rendering style.  Can be "full" or "brief" (both
        read-only), or "new" or "edit" or "hidden".

        'name' -- The name to use for the primary HTML form element
        containing the value of this field, if 'style' specifies the
        generation of form elements.  If 'name' is 'None', the value
        returned by 'GetHtmlFormFieldName()' should be used.

        returns -- A string containing the HTML representation of
        'value'."""

        raise NotImplementedError


    def MakeDomNodeForValue(self, value, document):
        """Generate a DOM element node for a value of this field.

        'value' -- The value to represent.

        'document' -- The containing DOM document node."""

        raise NotImplementedError

    ### Input methods.
    
    def Validate(self, value):
        """Validate a field value.

        For an acceptable type and value, return the representation of
        'value' in the underlying field storage.

        'value' -- A value to validate for this field.

        returns -- If the 'value' is valid, returns 'value' or an
        equivalent "canonical" version of 'value'.  (For example, this
        function may search a hash table and return an equivalent entry
        from the hash table.)

        This function must raise an exception if the value is not valid.
        The string representation of the exception will be used as an
        error message in some situations.

        Implementations of this method must be idempotent."""

        raise NotImplementedError


    def ParseTextValue(self, value):
        """Parse a value represented as a string.

        'value' -- A string representing the value.

        returns -- The corresponding field value.  The value returned
        should be processed by 'Validate' to ensure that it is valid
        before it is returned."""

        raise NotImplemented
    
        
    def ParseFormValue(self, request, name, attachment_stores):
        """Convert a value submitted from an HTML form.

        'request' -- The 'WebRequest' containing a value corresponding
        to this field.

        'name' -- The name corresponding to this field in the 'request'.

        'attachment_stores' -- A dictionary mapping 'AttachmentStore' ids
        (in the sense of Python's 'id' built-in) to the
        'AttachmentStore's themselves.
        
        returns -- A pair '(value, redisplay)'.  'value' is the value
        for this field, as indicated in 'request'.  'redisplay' is true
        if and only if the form should be redisplayed, rather than
        committed.  If an error occurs, an exception is thrown."""

        # Retrieve the value provided in the form.
        value = request[name]
        # Treat the result as we would if it were provided on the
        # command-line.
        return (self.ParseTextValue(value), 0)


    def GetValueFromDomNode(self, node, attachment_store):
        """Return a value for this field represented by DOM 'node'.

        This method does not validate the value for this particular
        instance; it only makes sure the node is well-formed, and
        returns a value of the correct Python type.

        'node' -- The DOM node that is being evaluated.

        'attachment_store' -- For attachments, the store that should be
        used.
        
        If the 'node' is incorrectly formed, this method should raise an
        exception."""

        raise NotImplementedError

    # Other methods.
    
    def GetHtmlFormFieldName(self):
        """Return the form field name corresponding this field.

        returns -- A string giving the name that should be used for this
        field when used in an HTML form."""

        return self.form_field_prefix + self.GetName()


    def __repr__(self):

        # This output format is more useful when debugging than the
        # default "<... instance at 0x...>" format provided by Python.
        return "<%s %s>" % (self.__class__, self.GetName())


########################################################################

class IntegerField(Field):
    """An 'IntegerField' stores an 'int' or 'long' object."""

    def __init__(self, name="", default_value=0, **properties):
        """Construct a new 'IntegerField'.

        'name' -- As for 'Field.__init__'.

        'default_value' -- As for 'Field.__init__'.

        'properties' -- Other keyword arguments for 'Field.__init__'."""

        # Perform base class initialization.
        super(IntegerField, self).__init__(name, default_value, **properties)


    def GetHelp(self):

        return """This field stores an integer.

               The default value of this field is %d."""
    
    ### Output methods.

    def FormatValueAsText(self, value, columns=72):

        return str(value)
    

    def FormatValueAsHtml(self, server, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = self.GetDefaultValue()
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            return '<input type="text" size="8" name="%s" value="%d" />' \
                   % (name, value)
        elif style == "full" or style == "brief":
            return '<tt>%d</tt>' % value
        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%d" />' \
                   % (name, value)            
        else:
            assert None


    def MakeDomNodeForValue(self, value, document):
        return xmlutil.create_dom_text_element(document, "integer",
                                               str(value))


    ### Input methods.

    def Validate(self, value):

        if not isinstance(value, (int, long)):
            raise ValueError, value

        return value


    def ParseTextValue(self, value):

        try:
            return self.Validate(int(value))
        except:
            raise qm.common.QMException, \
                  qm.error("invalid integer field value")


    def GetValueFromDomNode(self, node, attachment_store):

        # Make sure 'node' is an '<integer>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "integer":
            raise qm.QMException, \
                  qm.error("dom wrong tag for field",
                           name=self.GetName(),
                           right_tag="integer",
                           wrong_tag=node.tagName)
        # Retrieve the contained text.
        value = xmlutil.get_dom_text(node)
        # Convert it to an integer.
        return self.ParseTextValue(value)


########################################################################

class TextField(Field):
    """A field that contains text."""

    def __init__(self,
                 name = "",
                 default_value = "",
                 multiline = "false",
                 structured = "false",
                 verbatim = "false",
                 not_empty_text = "false",
                 **properties):
        """Construct a new 'TextField'.

        'multiline' -- If false, a value for this field is a single line
        of text.  If true, multi-line text is allowed.

        'structured' -- If true, the field contains structured text.

        'verbatim' -- If true, the contents of the field are treated as
        preformatted text.
            
        'not_empty_text' -- The value of this field is considered
        invalid if it empty or composed only of whitespace.

        'properties' -- A dictionary of other keyword arguments which
        are provided to the base class constructor."""

        # Initialize the base class.
        super(TextField, self).__init__(name, default_value, **properties)

        self.__multiline = multiline == "true"
        self.__structured = structured == "true"
        self.__verbatim = verbatim == "true"
        self.__not_empty_text = not_empty_text == "true"


    def GetHelp(self):

        help = """
            A text field.  """
        if self.__structured:
            help = help + '''
            The text is interpreted as structured text, and formatted
            appropriately for the output device.  See "Structured Text
            Formatting
            Rules":http://www.python.org/sigs/doc-sig/stext.html for
            more information.  '''
        elif self.__verbatim:
            help = help + """
            The text is stored verbatim; whitespace and indentation are
            preserved.  """
        if self.__not_empty_text:
            help = help + """
            This field may not be empty.  """
        help = help + """
            The default value of this field is "%s".
            """ % self.GetDefaultValue()
        return help

    ### Output methods.

    def FormatValueAsText(self, value, columns=72):

        if self.__structured:
            return structured_text.to_text(value, width=columns)
        elif self.__verbatim:
            return value
        else:
            return common.wrap_lines(value, columns)
    

    def FormatValueAsHtml(self, server, value, style, name=None):

        # Use default value if requested.
        if value is None:
            value = ""
        else:
            value = str(value)
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        if style == "new" or style == "edit":
            if self.__multiline:
                result = '<textarea cols="64" rows="8" name="%s">' \
                         '%s</textarea>' \
                         % (name, web.escape(value))
            else:
                result = \
                    '<input type="text" size="40" name="%s" value="%s" />' \
                    % (name, web.escape(value))
            # If this is a structured text field, add a note to that
            # effect, so users aren't surprised.
            if self.__structured:
                result = result \
                + '<br><font size="-1">This is a ' \
                + qm.web.make_help_link_html(
                    qm.structured_text.html_help_text,
                    "structured text") \
                + 'field.</font>'
            return result

        elif style == "hidden":
            return '<input type="hidden" name="%s" value="%s" />' \
                   % (name, web.escape(value))            

        elif style == "brief":
            if self.__structured:
                # Use only the first line of text.
                value = string.split(value, "\n", 1)
                value = web.format_structured_text(value[0])
            else:
                # Replace all whitespace with ordinary space.
                value = re.sub(r"\s", " ", value)

            # Truncate to 80 characters, if it's longer.
            if len(value) > 80:
                value = value[:80] + "..."

            if self.__verbatim:
                # Put verbatim text in a <tt> element.
                return '<tt>%s</tt>' % web.escape(value)
            elif self.__structured:
                # It's already formatted as HTML; don't escape it.
                return value
            else:
                # Other text set normally.
                return web.escape(value)

        elif style == "full":
            if self.__verbatim:
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
            elif self.__structured:
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


    def MakeDomNodeForValue(self, value, document):

        return xmlutil.create_dom_text_element(document, "text", value)

    ### Input methods.

    def Validate(self, value):

        if not isinstance(value, types.StringTypes):
            raise ValueError, value
        
        # Clean up unless it's a verbatim string.
        if not self.__verbatim:
            # Remove leading whitespace.
            value = string.lstrip(value)
        # If this field has the not_empty_text property set, make sure the
        # value complies.
        if self.__not_empty_text and value == "":
            raise ValueError, \
                  qm.error("empty text field value",
                           field_title=self.GetTitle()) 
        # If this is not a multi-line text field, remove line breaks
        # (and surrounding whitespace).
        if not self.__multiline:
            value = re.sub(" *\n+ *", " ", value)
        return value


    def ParseFormValue(self, request, name, attachment_stores):

        # HTTP specifies text encodings are CR/LF delimited; convert to
        # the One True Text Format (TM).
        return (self.ParseTextValue(qm.convert_from_dos_text(request[name])),
                0)
    

    def ParseTextValue(self, value):

        return self.Validate(value)

    
    def GetValueFromDomNode(self, node, attachment_store):

        # Make sure 'node' is a '<text>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "text":
            raise qm.QMException, \
                  qm.error("dom wrong tag for field",
                           name=self.GetName(),
                           right_tag="text",
                           wrong_tag=node.tagName)
        return self.Validate(xmlutil.get_dom_text(node))


########################################################################

class TupleField(Field):
    """A 'TupleField' contains zero or more other 'Field' objects.

    The contained 'Field' objects may have different types.  The value
    of a 'TupleField' is a Python list; the values in the list
    correspond to the values of the contained 'Field' objects.  For
    example, '["abc", 3]' would be a valid value for a 'TupleField'
    containing a 'TextField' and an 'IntegerField'."""

    def __init__(self, name = "", fields = None, **properties):
        """Construct a new 'TupleField'.

        'name' -- The name of the field.

        'fields' -- A sequence of 'Field' instances.

        The new 'TupleField' stores a list whose elements correspond to
        the 'fields'."""

        self.__fields = fields == None and [] or fields
        default_value = map(lambda f: f.GetDefaultValue(), self.__fields)
        Field.__init__(self, name, default_value, **properties)


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


    def GetSubfields(self):

        return self.__fields

    
    ### Output methods.

    def FormatValueAsHtml(self, server, value, style, name = None):

        # Use the default name if none is specified.
        if name is None:
            name = self.GetHtmlFormFieldName()
            
        # Format the field as a multi-column table.
        html = '<table border="0" cellpadding="0">\n <tr>\n'
        for f, v in map(None, self.__fields, value):
            element_name = name + "_" + f.GetName()
            html += "  <td><b>" + f.GetTitle() + "</b>:</td>\n"
            html += ("  <td>\n" 
                     + f.FormatValueAsHtml(server, v, style, element_name)
                     + "  </td>\n")
        html += " </tr>\n</table>\n"

        return html


    def MakeDomNodeForValue(self, value, document):

        element = document.createElement("tuple")
        for f, v in map(None, self.__fields, value):
            element.appendChild(f.MakeDomNodeForValue(v, document))

        return element

    ### Input methods.
    
    def Validate(self, value):

        assert len(value) == len(self.__fields)
        return map(lambda f, v: f.Validate(v),
                   self.__fields, value)


    def ParseFormValue(self, request, name, attachment_stores):

        value = []
        redisplay = 0
        for f in self.__fields:
            v, r = f.ParseFormValue(request, name + "_" + f.GetName(),
                                    attachment_stores)
            value.append(v)
            if r:
                redisplay = 1

        # Now that we've computed the value of the entire tuple, make
        # sure it is valid.
        value = self.Validate(value)
        
        return (value, redisplay)
            

    def GetValueFromDomNode(self, node, attachment_store):

        values = []
        for f, element in map(None, self.__fields, node.childNodes):
            values.append(f.GetValueFromDomNode(element, attachment_store))

        return self.Validate(values)
    

    
class DictionaryField(Field):
    """A 'DictionaryField' maps keys to values."""

    def __init__(self, key_field, value_field, **properties):
        """Construct a new 'DictionaryField'.

        'key_field' -- The key field.

        'value_field' -- The value field.
        """

        self.__key_field = key_field
        self.__value_field = value_field
        super(DictionaryField, self).__init__(**properties)


    def GetHelp(self):

        help = """
        A dictionary field. A dictionary maps keys to values. The key type:
        %s
        The value type:
        %s"""%(self.__key_field.GetHelp(), self.__value_field.GetHelp())
        return help

    
    def GetKeyField(self): return self.__key_field
    def GetValueField(self): return self.__value_field

    ### Output methods.

    def FormatValueAsHtml(self, server, content, style, name = None):

        if content is None:
            content = {}
        # Use the default name if none is specified.
        if name is None:
            name = self.GetHtmlFormFieldName()
            
        if style == 'brief' or style == 'full':
            if len(content) == 0:
                # An empty set.
                return 'None'
            body = ['<th>%s</th><td>%s</td>\n'
                    %(self.__key_field.FormatValueAsHtml(server, key, style),
                      self.__value_field.FormatValueAsHtml(server, value, style))
                    for (key, value) in content.iteritems()]
            return '<table><tr>%s</tr>\n</table>\n'%'</tr>\n<tr>'.join(body)

        elif style in ['new', 'edit', 'hidden']:
            html = ''
            if content:
                # Create a table to represent the dictionary -- but only if it is
                # non-empty.  A table with no body is invalid HTML.
                html += ('<table border="0" cellpadding="0" cellspacing="0">'
                         '\n <tbody>\n')
                element_number = 0
                for key, value in content.iteritems():
                    html += '  <tr>\n   <td>'
                    element_name = name + '_%d' % element_number
                    checkbox_name = element_name + "_remove"
                    if style == 'edit':
                        html += ('<input type="checkbox" name="%s" /></td>\n'
                                 '   <td>\n'
                                 % checkbox_name)
                    element_name = name + '_key_%d' % element_number
                    html += ('   <th>%s</th>\n'
                             %self.__key_field.FormatValueAsHtml(server, key,
                                                                 style,
                                                                 element_name))
                    element_name = name + '_value_%d' % element_number
                    html += ('   <td>%s</td>\n'
                             %self.__value_field.FormatValueAsHtml(server, value,
                                                                   style,
                                                                   element_name))
                    html += '  </tr>\n'
                    element_number += 1
                html += ' </tbody>\n</table>\n'
            # The action field is used to keep track of whether the
            # "Add" or "Remove" button has been pushed.  It would be
            # much nice if we could use JavaScript to update the
            # table, but Netscape 4, and even Mozilla 1.0, do not
            # permit that.  Therefore, we have to go back to the server.
            html += '<input type="hidden" name="%s" value="" />' % name
            html += ('<input type="hidden" name="%s_count" value="%d" />'
                     % (name, len(content)))
            if style != 'hidden':
                html += ('<table border="0" cellpadding="0" cellspacing="0">\n'
                         ' <tbody>\n'
                         '  <tr>\n'
                         '   <td><input type="button" name="%s_add" '
                         'value="Add Another" '
                         '''onclick="%s.value = 'add'; submit();" />'''
                         '</td>\n'
                         '   <td><input type="button" name="%s_remove"'
                         'value="Remove Selected" '
                         '''onclick="%s.value = 'remove'; submit();" />'''
                         '</td>\n'
                         '  </tr>'
                         ' </tbody>'
                         '</table>'
                         % (name, name, name, name))
            return html


    def MakeDomNodeForValue(self, value, document):

        element = document.createElement('dictionary')
        for k, v in value.iteritems():
            item = element.appendChild(document.createElement('item'))
            item.appendChild(self.__key_field.MakeDomNodeForValue(k, document))
            item.appendChild(self.__value_field.MakeDomNodeForValue(v, document))
        return element


    ### Input methods.
    
    def Validate(self, value):

        valid = {}
        for k, v in value.items():
            valid[self.__key_field.Validate(k)] = self.__value_field.Validate(v)

        return valid


    def ParseTextValue(self, value):

        raise NotImplementedError


    def ParseFormValue(self, request, name, attachment_stores):

        content = {}
        redisplay = 0

        action = request[name]

        for i in xrange(int(request[name + '_count'])):
            if not (action == 'remove'
                    and request.get(name + '_%d_remove'%i) == 'on'):
                key, rk = self.__key_field.ParseFormValue(request,
                                                          name + '_key_%d'%i,
                                                          attachment_stores)
                value, rv = self.__value_field.ParseFormValue(request,
                                                              name + '_value_%d'%i,
                                                              attachment_stores)
                content[key] = value
                if rk or rv:
                    redisplay = 1

        # Remove entries from the request that might cause confusion
        # when the page is redisplayed.
        names = []
        for n, v in request.items():
            if n[:len(name)] == name:
                names.append(n)
        for n in names:
            del request[n]

        content = self.Validate(content)
        
        if action == 'add':
            redisplay = 1
            content[self.__key_field.GetDefaultValue()] =\
            self.__value_field.GetDefaultValue()
        elif action == 'remove':
            redisplay = 1

        return (content, redisplay)
            

    def GetValueFromDomNode(self, node, attachment_store):

        values = {}
        for item in node.childNodes:
            if item.nodeType == xml.dom.Node.ELEMENT_NODE:
                values[self.__key_field.GetValueFromDomNode
                       (item.childNodes[0], attachment_store)] =\
                       self.__value_field.GetValueFromDomNode(item.childNodes[1],
                                                              attachment_store)
        return self.Validate(values)
    

    
class SetField(Field):
    """A field containing zero or more instances of some other field.

    All contents must be of the same field type.  A set field may not
    contain sets.

    The default field value is set to an empty set."""

    def __init__(self, contained, not_empty_set = "false", default_value = None,
                 **properties):
        """Create a set field.

        The name of the contained field is taken as the name of this
        field.

        'contained' -- An 'Field' instance describing the
        elements of the set.

        'not_empty_set' -- If true, this field may not be empty,
        i.e. the value of this field must contain at least one element.

        raises -- 'ValueError' if 'contained' is a set field.

        raises -- 'TypeError' if 'contained' is not a 'Field'."""

        if not properties.has_key('description'):
            properties['description'] = contained.GetDescription()

        super(SetField, self).__init__(
            contained.GetName(),
            default_value or [],
            title = contained.GetTitle(),
            **properties)

        # A set field may not contain a set field.
        if isinstance(contained, SetField):
            raise ValueError, \
                  "A set field may not contain a set field."
        if not isinstance(contained, Field):
            raise TypeError, "A set must contain another field."
        # Remeber the contained field type.
        self.__contained = contained
        self.__not_empty_set = not_empty_set == "true"


    def GetHelp(self):
        return """
        A set field.  A set contains zero or more elements, all of the
        same type.  The elements of the set are described below:

        """ + self.__contained.GetHelp()


    def GetSubfields(self):

        return (self.__contained,)
    

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

    ### Output methods.
    
    def FormatValueAsText(self, value, columns=72):
        # If the set is empty, indicate this specially.
        if len(value) == 0:
            return "None"
        # Format each element of the set, and join them into a
        # comma-separated list. 
        contained_field = self.__contained
        formatted_items = []
        for item in value:
            formatted_item = contained_field.FormatValueAsText(item, columns)
            formatted_items.append(repr(formatted_item))
        result = "[ " + string.join(formatted_items, ", ") + " ]"
        return qm.common.wrap_lines(result, columns)


    def FormatValueAsHtml(self, server, value, style, name=None):
        # Use default value if requested.
        if value is None:
            value = []
        # Use the default field form field name if requested.
        if name is None:
            name = self.GetHtmlFormFieldName()

        contained_field = self.__contained
        if style == "brief" or style == "full":
            if len(value) == 0:
                # An empty set.
                return "None"
            formatted \
                = map(lambda v: contained_field.FormatValueAsHtml(server,
                                                                  v, style),
                      value)
            if style == "brief":
                # In the brief style, list elements separated by commas.
                separator = ", "
            else:
                # In the full style, list elements one per line.
                separator = "<br>\n"
            return string.join(formatted, separator)

        elif style in ["new", "edit", "hidden"]:
            html = ""
            if value:
                # Create a table to represent the set -- but only if the set is
                # non-empty.  A table with no body is invalid HTML.
                html += ('<table border="0" cellpadding="0" cellspacing="0">'
                         "\n <tbody>\n")
                element_number = 0
                for element in value:
                    html += "  <tr>\n   <td>"
                    element_name = name + "_%d" % element_number
                    checkbox_name = element_name + "_remove"
                    if style == "edit":
                        html += \
                           ('<input type="checkbox" name="%s" /></td>\n'
                            '   <td>\n'
                            % checkbox_name)
                    html += contained_field.FormatValueAsHtml(server,
                                                              element,
                                                              style,
                                                              element_name)
                    html += "   </td>\n  </tr>\n"
                    element_number += 1
                html += " </tbody>\n</table>\n"
            # The action field is used to keep track of whether the
            # "Add" or "Remove" button has been pushed.  It would be
            # much nice if we could use JavaScript to update the
            # table, but Netscape 4, and even Mozilla 1.0, do not
            # permit that.  Therefore, we have to go back to the server.
            html += '<input type="hidden" name="%s" value="" />' % name
            html += ('<input type="hidden" name="%s_count" value="%d" />'
                     % (name, len(value)))
            if style != "hidden":
                html += ('<table border="0" cellpadding="0" cellspacing="0">\n'
                         ' <tbody>\n'
                         '  <tr>\n'
                         '   <td><input type="button" name="%s_add" '
                         'value="Add Another" '
                         '''onclick="%s.value = 'add'; submit();" />'''
                         '</td>\n'
                         '   <td><input type="button" name="%s_remove"'
                         'value="Remove Selected" '
                         '''onclick="%s.value = 'remove'; submit();" />'''
                         '</td>\n'
                         '  </tr>'
                         ' </tbody>'
                         '</table>'
                         % (name, name, name, name))
            return html


    def MakeDomNodeForValue(self, value, document):

        # Create a set element.
        element = document.createElement("set")
        # Add a child node for each item in the set.
        contained_field = self.__contained
        for item in value:
            # The contained field knows how to make a DOM node for each
            # item in the set.
            item_node = contained_field.MakeDomNodeForValue(item, document)
            element.appendChild(item_node)
        return element

    ### Input methods.
    
    def Validate(self, value):

        # If this field has the not_empty_set property set, make sure
        # the value complies.
        if self.__not_empty_set and len(value) == 0:
            raise ValueError, \
                  qm.error("empty set field value",
                           field_title=self.GetTitle()) 
        # Assume 'value' is a sequence.  Copy it, simultaneously
        # validating each element in the contained field.
        return map(lambda v: self.__contained.Validate(v),
                   value)


    def ParseTextValue(self, value):

        def invalid(tok):
            """Raise an exception indicating a problem with 'value'.
            
            'tok' -- A token indicating the position of the problem.

            This function does not return; instead, it raises an
            appropriate exception."""

            raise qm.QMException, \
                  qm.error("invalid set value", start = value[tok[2][1]:])
            
        # Use the Python parser to handle the elements of the set.
        s = StringIO.StringIO(value)
        g = tokenize.generate_tokens(s.readline)
        
        # Read the opening square bracket.
        tok = g.next()
        if tok[0] != tokenize.OP or tok[1] != "[":
            invalid(tok)

        # There are no elements yet.
        elements = []

        # Keep going until we find the closing bracket.
        while 1:
            # If we've reached the closing bracket, the set is
            # complete.
            tok = g.next()
            if tok[0] == tokenize.OP and tok[1] == "]":
                break
            # If this is not the first element of the set, there should
            # be a comma before the next element.
            if elements:
                if tok[0] != tokenize.OP or tok[1] != ",":
                    invalid(tok)
                tok = g.next()
            # The next token should be a string constant.
            if tok[0] != tokenize.STRING:
                invalid(tok)
            # Parse the string constant.
            v = eval(tok[1])
            elements.append(self.__contained.ParseTextValue(v))

        # There should not be any tokens left over.
        tok = g.next()
        if not tokenize.ISEOF(tok[0]):
            invalid(tok)

        return self.Validate(elements)
        
                       
    def ParseFormValue(self, request, name, attachment_stores):

        values = []
        redisplay = 0
        
        # See if the user wants to add or remove elements from the set.
        action = request[name]
        # Loop over the entries for each of the elements, adding them to
        # the set.
        contained_field = self.__contained
        element = 0
        for element in xrange(int(request[name + "_count"])):
            element_name = name + "_%d" % element
            if not (action == "remove"
                    and request.get(element_name + "_remove") == "on"):
                v, r = contained_field.ParseFormValue(request,
                                                      element_name,
                                                      attachment_stores)
                values.append(v)
                if r:
                    redisplay = 1
            element += 1
        
        # Remove entries from the request that might cause confusion
        # when the page is redisplayed.
        names = []
        for n, v in request.items():
            if n[:len(name)] == name:
                names.append(n)
        for n in names:
            del request[n]

        # Validate the values.
        values = self.Validate(values)
        
        # If the user requested another element, add to the set.
        if action == "add":
            redisplay = 1
            # There's no need to validate this new value and it may in
            # fact be dangerous to do so.  For example, the default
            # value for a ChoiceField might be the "nothing selected"
            # value, which is not a valid selection.  If the user does
            # not actually select something, the problem will be
            # reported when the form is submitted.
            values.append(contained_field.GetDefaultValue())
        elif action == "remove":
            redisplay = 1

        return (values, redisplay)


    def GetValueFromDomNode(self, node, attachment_store):
        # Make sure 'node' is a '<set>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "set":
            raise qm.QMException, \
                  qm.error("dom wrong tag for field",
                           name=self.GetName(),
                           right_tag="set",
                           wrong_tag=node.tagName)
        # Use the contained field to extract values for the children of
        # this node, which are the set elements.
        contained_field = self.__contained
        fn = lambda n, f=contained_field, s=attachment_store: \
             f.GetValueFromDomNode(n, s)
        values = map(fn,
                     filter(lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE,
                            node.childNodes))
        return self.Validate(values)



########################################################################

class UploadAttachmentPage(web.DtmlPage):
    """DTML context for generating upload-attachment.dtml."""

    def __init__(self,
                 attachment_store,
                 field_name,
                 encoding_name,
                 summary_field_name,
                 in_set=0):
        """Create a new page object.

        'attachment_store' -- The AttachmentStore in which the new
        attachment will be placed.
        
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
        # Set up properties.
        self.attachment_store_id = id(attachment_store)
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


    def __init__(self, name = "", **properties):
        """Create an attachment field.

        Sets the default value of the field to 'None'."""

        # Perform base class initialization. 
        apply(Field.__init__, (self, name, None), properties)


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
    
    ### Output methods.
    
    def FormatValueAsText(self, value, columns=72):

        return self._FormatSummary(value)


    def FormatValueAsHtml(self, server, value, style, name=None):
        
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
            summary_value = 'value="%s"' % self._FormatSummary(value)
            if value is None:
                field_value = ""
            else:
                # We'll encode all the relevant information.
                parts = (description, mime_type, location, file_name,
                         str(id(value.GetStore())))
                # Each part is URL-encoded.
                parts = map(urllib.quote, parts)
                # The parts are joined into a semicolon-delimited list.
                field_value = string.join(parts, ";")
            field_value = 'value="%s"' % field_value

            # Generate the popup upload page.
            upload_page = \
                UploadAttachmentPage(server.GetTemporaryAttachmentStore(),
                                     self.GetTitle(),
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
                = server.MakeButtonForCachedPopup("Upload",
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
                            document.form.%s.value = '';" />
            ''' % (field_name, summary_field_name, name)
            # A hidden control for the encoded attachment value.  The
            # popup upload form fills in this control.
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


    def MakeDomNodeForValue(self, value, document):
        return attachment.make_dom_node(value, document)


    def _FormatSummary(self, attachment):
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


    ### Input methods.
        
    def Validate(self, value):

        # The value should be an instance of 'Attachment', or 'None'.
        if value != None and not isinstance(value, attachment.Attachment):
            raise ValueError, \
                  "the value of an attachment field must be an 'Attachment'"
        return value


    def ParseFormValue(self, request, name, attachment_stores):

        encoding = request[name]
        # An empty string represnts a missing attachment, which is OK.
        if string.strip(encoding) == "":
            return None
        # The encoding is a semicolon-separated sequence indicating the
        # relevant information about the attachment.
        parts = string.split(encoding, ";")
        # Undo the URL encoding of each component.
        parts = map(urllib.unquote, parts)
        # Unpack the results.
        description, mime_type, location, file_name, store_id = parts
        # Figure out which AttachmentStore corresponds to the id
        # provided.
        store = attachment_stores[int(store_id)]
        # Create the attachment.
        value = attachment.Attachment(mime_type, description,
                                      file_name, location,
                                      store)
        return (self.Validate(value), 0)


    def GetValueFromDomNode(self, node, attachment_store):

        # Make sure 'node' is an "attachment" element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "attachment":
            raise qm.QMException, \
                  qm.error("dom wrong tag for field",
                           name=self.GetName(),
                           right_tag="attachment",
                           wrong_tag=node.tagName)
        return self.Validate(attachment.from_dom_node(node, attachment_store))


########################################################################

class ChoiceField(TextField):
    """A 'ChoiceField' allows choosing one of several values.

    The set of acceptable values can be determined when the field is
    created or dynamically.  The empty string is used as the "no
    choice" value, and cannot therefore be one of the permitted
    values."""

    def GetItems(self):
        """Return the options from which to choose.

        returns -- A sequence of strings, each of which will be
        presented as a choice for the user."""

        raise NotImplementedError


    def FormatValueAsHtml(self, server, value, style, name = None):

        if style not in ("new", "edit"):
            return qm.fields.TextField.FormatValueAsHtml(self, server,
                                                         value,
                                                         style, name)

        # For an editable field, give the user a choice of available
        # resources.
        items = self.GetItems()
        if name is None:
            name = self.GetHtmlFormFieldName()
        result = '<select name="%s">\n' % name
        # HTML does not permit a "select" tag with no contained "option"
        # tags.  Therefore, we ensure that there is always one option to
        # choose from.
        result += ' <option value="">--Select--</option>\n'
        # Add the choices for the ordinary options.
        for r in self.GetItems():
            result += ' <option value="%s"' % r
            if r == value:
                result += ' selected="selected"'
            result += '>%s</option>\n' % r
        result += "</select>\n"

        return result
    

    def Validate(self, value):

        value = super(ChoiceField, self).Validate(value)
        if value == "":
            raise ValueError, "No choice specified for %s." % self.GetTitle()
        return value

        
        
class EnumerationField(ChoiceField):
    """A field that contains an enumeral value.

    The enumeral value is selected from an enumerated set of values.
    An enumeral field uses the following properties:

    enumeration -- A mapping from enumeral names to enumeral values.
    Names are converted to strings, and values are stored as integers.

    ordered -- If non-zero, the enumerals are presented to the user
    ordered by value."""

    def __init__(self,
                 name = "",
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
        super(EnumerationField, self).__init__(name, default_value, 
                                               **properties)
        # Remember the enumerals.
        self.__enumerals = enumerals


    def GetItems(self):
        """Return a sequence of enumerals.

        returns -- A sequence consisting of string enumerals objects, in
        the appropriate order."""

        return self.__enumerals


    def GetHelp(self):
        enumerals = self.GetItems()
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

    ### Output methods.
    
    def MakeDomNodeForValue(self, value, document):

        # Store the name of the enumeral.
        return xmlutil.create_dom_text_element(document, "enumeral", 
                                               str(value))


    ### Input methods.
    
    def GetValueFromDomNode(self, node, attachment_store):

        # Make sure 'node' is an '<enumeral>' element.
        if node.nodeType != xml.dom.Node.ELEMENT_NODE \
           or node.tagName != "enumeral":
            raise qm.QMException, \
                  qm.error("dom wrong tag for field",
                           name=self.GetName(),
                           right_tag="enumeral",
                           wrong_tag=node.tagName)
        # Extract the value.
        return self.Validate(xmlutil.get_dom_text(node))



class BooleanField(EnumerationField):
    """A field containing a boolean value.

    The enumeration contains two values: true and false."""

    def __init__(self, name = "", default_value = None, **properties):

        # Construct the base class.
        EnumerationField.__init__(self, name, default_value,
                                  ["true", "false"], **properties)


    def Validate(self, value):

        if qm.common.parse_boolean(value):
            value = "true"
        else:
            value = "false"
        return super(BooleanField, self).Validate(value)
        

########################################################################

class TimeField(IntegerField):
    """A field containing a date and time.

    The data and time is stored as seconds since the start of the UNIX
    epoch, UTC (the semantics of the standard 'time' function), with
    one-second precision.  User representations of 'TimeField' fields
    show one-minue precision."""

    def __init__(self, name = "", **properties):
        """Create a time field.

        The field is given a default value for this field is 'None', which
        corresponds to the current time when the field value is first
        created."""

        # Perform base class initalization.
        super(TimeField, self).__init__(name, None, **properties)


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
        default_value = self.GetDefaultValue()
        if default_value is None:
            help = help + """
            The default value for this field is the current time.
            """
        else:
            help = help + """
            The default value for this field is %s.
            """ % self.FormatValueAsText(default_value)
        return help

    ### Output methods.
    
    def FormatValueAsText(self, value, columns=72):
        if value is None:
            return "now"
        else:
            return qm.common.format_time(value, local_time_zone=1)


    def FormatValueAsHtml(self, server, value, style, name=None):

        value = self.FormatValueAsText(value)

        if style == "new" or style == "edit":
            return '<input type="text" size="8" name="%s" value="%s" />' \
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
            return '<input type="hidden" name="%s" value="%s" />' \
                   % (name, value)
        else:
            raise ValueError, style

    ### Input methods.
        
    def ParseTextValue(self, value):

        return self.Validate(qm.common.parse_time(value,
                                                  default_local_time_zone=1))


    def GetDefaultValue(self):

        default_value = super(TimeField, self).GetDefaultValue()
        if default_value is not None:
            return default_value

        return int(time.time())



class PythonField(Field):
    """A 'PythonField' stores a Python value.

    All 'PythonField's are computed; they are never written out, nor can
    they be specified directly by users.  They are used in situations
    where the value of the field is specified programatically by the
    system."""

    def __init__(self, name = "", default_value = None):

        Field.__init__(self, name, default_value, computed = "true")
    
########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

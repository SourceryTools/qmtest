#!/usr/bin/python
########################################################################
#
# File:   structured_text.py
# Author: Alex Samuel
# Date:   2001-03-04
#
# Contents:
#   Code for processing structured text.
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

"""Functions for parsing, processing, and formatting Python structured text.

See "Structured Text Formatting
Rules":http://www.python.org/sigs/doc-sig/stext.html for more
information.
"""

########################################################################
# imports
########################################################################

import cStringIO
import htmlentitydefs
import re
import string
import sys

########################################################################
# constants
########################################################################

html_help_text = '''
<h4>Structured Text</h4>

<p>Structured text is a simple set of conventions for formatting
ordinary text.  Usually, you can simply type ordinary text where QM
expects structured text; the resulting output will be line-wrapped, with
paragraph breaks indicated by blank lines.</p>

<p>Structured text also provides simple ways of adding elements such as
bulleted and numbered lists, bold and italics text, monospaced text, and
hyperlinks to ordinary text.  For example, to obtain bold text, place a
pair of asterisks on either side of it.  Thus,
<blockquote><pre>
**hello, there**
</pre></blockquote>
is displayed as
<blockquote>
<b>hello, there</b>
</blockquote>Structured text may be displayed as HTML, as plain text,
or in other formats.  The exact format of the output will depend on the
capabilities of the output system.</p>

<p>For a complete description of structured text rules, see the
<a href="http://www.python.org/sigs/doc-sig/stext.html">Structured Text
Formatting Rules</a>.</p>
'''

########################################################################
# classes
########################################################################

class Formatter:
    """Interface for output formatters for the 'StructuredTextProcessor'.

    Valid list environment types are

      * definition list

      * ordered list

      * paragraph

      * unordered list

    Valid styles are

      * emphasized

      * strong

      * underlined

      * verbatim

    """

    pass



class TextFormatter(Formatter):
    """Formatter for generating plain text from structured text."""

    __style_markers = {
        "emphasized" :          "*",
        "strong" :              "**",
        "underlined" :          "_",
        "verbatim" :            "'",
        }

        
    def __init__(self,
                 output_file=sys.stdout,
                 width=78,
                 indent_size=2,
                 indent=0,
                 list_bullet="-"):
        """Create a new HTML formatter.

        'output_file' -- A file object to which HTML source is
        written."""

        self.__output_file = output_file
        self.__width = width
        self.__col = 0
        self.__indent = indent
        self.__indent_size = indent_size
        self.__list_bullet = list_bullet
        self.__list_depth = 0
        self.__current_link_target = None
        self.__link_targets = []


    def End(self):
        """End the processed text document."""

        # If there were any hyperlink references placed, we need to list
        # the link targets at the end of the document.
        if len(self.__link_targets) > 0:
            self.__NextLine()
            for index in range(0, len(self.__link_targets)):
                # Print the reference number and link target, one to a
                # line. 
                target = self.__link_targets[index]
                self.WriteText("[%d] %s" % (index + 1, target))
                self.__NextLine()


    def WriteText(self, text):
        """Write ordinary text."""
        
        # Split the text into words.  Use 're.split' and grouping
        # around the separator so that the resulting list contains
        # elements for the separators, too.
        words = re.split("( )", text)
        # Remove empty strings.
        words = filter(None, words)
        # Loop over words.
        start_of_line = 0
        for word in words:
            # Does this word fit on the line?
            if self.__col + len(word) > self.__width:
                # No.  Go to the next line.
                self.__NextLine()
                self.__IndentTo(self.__indent)
                start_of_line = 1
            # Are we at the beginning of a line?
            if start_of_line:
                if string.strip(word) == "":
                    # Don't print spaces at the start of a line.
                    continue
                else:
                    # No longer.
                    start_of_line = 0
            # Write the word.
            self.__Write(word)


    def StartList(self, type):
        """Start a list environment of type 'type'."""

        # Bump up indentation for paragraphs, except for the outermost
        # level. 
        if type == "paragraph" and self.__list_depth > 0:
            self.__indent = self.__indent + self.__indent_size
        # Keep track of the nesting depth of lists.
        self.__list_depth = self.__list_depth + 1


    def EndList(self, type):
        """End a list environment of type 'type'."""

        # Keep track of the nesting depth of lists.
        self.__list_depth = self.__list_depth - 1
        # Bump back indentation when ending paragraph lists, except for
        # the outermost level.
        if type == "paragraph" and self.__list_depth > 0:
            self.__indent = self.__indent - self.__indent_size


    def StartItem(self, type, label=None):
        """Begin an element to the environment of type 'type'.

        'label' -- If type is "ordered list", this is the label for
        this list element."""

        self.__IndentTo(self.__indent)
        # For list items, emit the appopriate item tag.
        if type == "ordered list":
            self.__Write("%s " % label)
        elif type == "unordered list":
            self.__Write("%s " % self.__list_bullet)
        elif type == "definition list":
            pass


    def FinishDefinedTerm(self):
        """Finish the definition of a term in a definition list."""

        self.__Write(" -- ");


    def EndItem(self, type):
        """End an element in the environment of type 'type'."""

        if type == "paragraph":
            # End a paragraph.  End this line if we've started writing
            # on it.
            if self.__col > self.__indent:
                self.__NextLine()
            # Skip another line.
            self.__NextLine()


    def StartStyle(self, style):
        """Start a new text style 'style'."""

        self.__Write(self.__style_markers[style])


    def EndStyle(self, style):
        """End the text style 'style'."""

        self.__Write(self.__style_markers[style])


    def StartLink(self, target):
        """Being a hyperlink to 'target'."""

        # Links should not be nested.
        assert self.__current_link_target is None
        # Store the link target, which we'll need at the end of the
        # link. 
        self.__current_link_target = target


    def EndLink(self):
        """End a hyperlink."""

        # Retrieve the link target, which was stored from when we
        # started the link.
        target = self.__current_link_target
        assert target is not None
        self.__current_link_target = None
        # Check if we've already placed a link to this target.  If we
        # have, use the same reference number as before.
        try:
            reference_number = self.__link_targets.index(target) + 1
        except ValueError:
            # This is the first time we're placing a reference to this
            # link target.  Add it to the list of links, and assign a
            # new reference number.
            self.__link_targets.append(target)
            reference_number = len(self.__link_targets)
        # Write the reference number.
        self.__Write(" [%d]" % reference_number)


    # Helper methods.

    def __IndentTo(self, col):
        if col > self.__col:
            self.__Write(" " * (col - self.__col))


    def __Write(self, text):
        self.__output_file.write(text)
        self.__col = self.__col + len(text)


    def __NextLine(self):
        self.__Write("\n")
        self.__col = 0



class HtmlFormatter(Formatter):
    """Formatter for generating HTML from structured text."""

    __start_list_tags = {
        "definition list":      "<dl>\n",
        "ordered list":         "<ol>\n",
        "paragraph":            "",
        "unordered list":       "<ul>\n",
        }

    __end_list_tags = {
        "definition list":      "</dl>\n",
        "ordered list":         "</ol>\n",
        "paragraph":            "",
        "unordered list":       "</ul>\n",
        }

    __start_item_tags = {
        "definition list":      "<dt>",
        "ordered list":         "<li>\n",
        "paragraph":            "<p>",
        "unordered list":       "<li>\n",
        }

    __end_item_tags = {
        "definition list":      "</dd>\n",
        "ordered list":         "</li>\n",
        "paragraph":            "</p>\n",
        "unordered list":       "</li>\n",
        }

    __start_style_tags = {
        "emphasized":           "<em>",
        "strong":               "<strong>",
        "underlined":           "<u>",
        "verbatim":             "<tt>",
        }

    __end_style_tags = {
        "emphasized":           "</em>",
        "strong":               "</strong>",
        "underlined":           "</u>",
        "verbatim":             "</tt>",
        }


    def __init__(self, output_file=sys.stdout):
        """Create a new HTML formatter.

        'output_file' -- A file object to which HTML source is
        written."""

        self.__output_file = output_file


    def End(self):
        """End the processed text document."""

        pass


    def WriteText(self, text):
        """Write ordinary text."""
        
        text = escape_html_entities(text)
        self.__Write(text)


    def StartList(self, type):
        """Start a list environment of type 'type'."""

        self.__Write(self.__start_list_tags[type])


    def EndList(self, type):
        """End a list environment of type 'type'."""

        self.__Write(self.__end_list_tags[type])


    def StartItem(self, type, label=None):
        """Begin an element to the environment of type 'type'.

        'label' -- If type is "ordered list", this is the label for
        this list element."""

        self.__Write(self.__start_item_tags[type])


    def FinishDefinedTerm(self):
        """Finish the definition of a term in a definition list."""

        self.__Write("</dt><dd>\n");


    def EndItem(self, type):
        """End an element in the environment of type 'type'."""

        self.__Write(self.__end_item_tags[type])


    def StartStyle(self, style):
        """Start a new text style 'style'."""

        self.__Write(self.__start_style_tags[style])


    def EndStyle(self, style):
        """End the text style 'style'."""

        self.__Write(self.__end_style_tags[style])


    def StartLink(self, target):
        """Being a hyperlink to 'target'."""

        self.__Write('<a href="%s">' % target)


    def EndLink(self):
        """End a hyperlink."""

        self.__Write("</a>")


    # Helper methods.

    def __Write(self, text):
        self.__output_file.write(text)



class StructuredTextProcessor:
    """Parser and formatter for Python structured text."""

    # Regex fragment matching a single punctuation or space character.
    __punctuation = "[%s]" % "][)(.,!?;:'\" "

    # Regex matching a list bullet at the start of the line.
    __bullet_regex = re.compile("^[-o*] +")

    # Regex matching a sequence label at the start of the line.
    __sequence_regex = re.compile("^([A-Za-z]+\.|[0-9]+\.?)+ +")

    # Regex matching a definition label at the start of the line.
    # Group 1 is the defined term.
    __definition_regex = re.compile("^(.*) +-- +")

    # Regex matching newslines plus any spaces on either side.
    __collapse_regex = re.compile(" *\n *", re.MULTILINE)

    # Regex matching indentation at the beginning of a line.
    __indent_regex = re.compile("^ *")

    # Regex matching single-quoted verbatim text.  Group 1 is leading
    # spaces; group 2 is the verbatim text; group 3 is trailing spaces
    # and/or punctuation.
    __verbatim_regex = re.compile("( +|^)'([^']+)'(%s+|$)" % __punctuation)

    # Regex matching emphasized text.  Group 1 is leading spaces;
    # group 2 is the verbatim text; group 3 is trailing spaces and/or
    # punctuation.
    __strong_regex = re.compile("( +|^)\*\*([^*]+)\*\*(%s+|$)" % __punctuation)

    # Regex matching strong text.  Group 1 is leading spaces; group 2
    # is the verbatim text; group 3 is trailing spaces and/or
    # punctuation.
    __emph_regex = re.compile("( +|^)\*([^*]+)\*(%s+|$)" % __punctuation)

    # Regex matching underlined text.  Group 1 is leading spaces;
    # group 2 is the verbatim text; group 3 is trailing spaces and/or
    # punctuation.
    __underline_regex = re.compile("( +|^)_([^_]+)_(%s+|$)" % __punctuation)

    # Regex matching double-quoted text that may be a hyperlink.  If
    # there is a matching link footnote, the contents of the double
    # quotes, group 1, is a hyperlink.
    __link_regex = re.compile('"([^"]*)"')

    # Regex matching hyperlink footnotes.  Group one is the link text;
    # group 2 is the link target URL.
    __link_footnote_regex = re.compile('\n\\.\\. *"([^"]*)" *([^ \n]*)[^\n]*')

    # List types which may not include other environments nested
    # inside their items.
    __non_nestable_types = [
        "paragraph",
        ]


    def __init__(self, formatter):
        """Create a new structured text processor.

        'formatter' -- The formatter to use to generate output."""
        
        self.__stack = []
        self.__formatter = formatter
        self.__hyperlinks = {}


    def NormalizeSpaces(self, text):
        """Return 'text' with spaces normalized."""

        # FIXME: Handle tabs and other unholy whitespace here.
        return string.strip(text) + " "


    def __call__(self, text):
        """Process structured text 'text'."""

        # Look for hyperlink footnotes, and build a map of hyperlinked
        # phrases.  Keep track of where the last match was.
        position = 0
        while position < len(text):
            # Look for the next hyperlink footnote match.
            match = self.__link_footnote_regex.search(text[position:])
            if match is None:
                # No more; all done.
                break
            else:
                # Record the hyperlink.
                link_text = string.strip(match.group(1))
                link_target = match.group(2)
                self.__hyperlinks[link_text] = link_target
                # Remove the footnote from the text.
                text = text[:match.start() + position] \
                       + text[match.end() + position:]
                # Next, try searching from the text following the match.
                position = match.start()

        # Split text into paragraphs.
        paragraphs = get_paragraphs(text)

        # Loop over paragraphs.
        for paragraph in paragraphs:
            # Extract indentations for all the lines in the paragraph.
            indents = self.__indent_regex.findall(paragraph)
            # The paragraph's indentation is the minimum indentation
            # of its lines.
            indentation = min(map(len, indents))
            # Trim indentation from the first line.
            paragraph = paragraph[indentation:]
            
            # Skip empty paragraphs.
            if paragraph == "":
                continue

            # Grab the first line of the paragraph.
            first_line = string.split(paragraph, "\n", 1)[0]

            # Does it look like a bullet (unordered) list item?
            match = self.__bullet_regex.match(first_line)
            if match is not None:
                # Yes.  Put the formatter into an unordered list
                # environment. 
                self.__SetType("unordered list", indentation)
                # Cut off the bullet, and use the indentation of the
                # text itself.
                match_length = len(match.group(0))
                indentation = indentation + match_length
                paragraph = paragraph[match_length:]
            else:
                # Does it look like a sequence label of an ordered list?
                match = self.__sequence_regex.match(first_line)
                if match is not None:
                    # Yes.  Put the formatter into an ordered list
                    # environment. 
                    self.__SetType("ordered list", indentation,
                                   label=match.group(1))
                    # Cut off the label, and use the indentation of
                    # the text itself.
                    match_length = len(match.group(0))
                    indentation = indentation + match_length
                    paragraph = paragraph[match_length:]
                else:
                    match = self.__definition_regex.match(first_line)
                    # Does it look like a definition list item?
                    if match is not None:
                        # Yes.  Put the formatter into a definition
                        # list environment.
                        self.__SetType("definition list", indentation,
                                       label=match.group(1))
                        # Cut off the defined term label, and use the
                        # indentation of the definition.
                        match_length = len(match.group(0))
                        indentation = indentation + match_length
                        paragraph = paragraph[match_length:]

            # Collapse the remaining paragraph into a single line of
            # text by replacing newlines with spaces.
            paragraph = self.__collapse_regex.sub(" ", paragraph)
            # Clean up spacing.
            paragraph = self.NormalizeSpaces(paragraph)
            # Now generate a paragraph for the rest of the text.
            self.__SetType("paragraph", indentation)
            self.__WriteText(paragraph)


    def End(self):
        """Stop processing text, and do any necessary cleanup."""

        # Pop out of any remaining environments.
        while len(self.__stack) > 0:
            top_type, top_indentation = self.__stack[-1]
            # End the item.
            self.__formatter.EndItem(top_type)
            # End the environment.
            self.__PopType()
        # Finish up the formatter.
        self.__formatter.End()


    # Helper methods.

    def __PushType(self, type, indentation):
        """Start a new environment."""

        # The innermost environment may be of a type that cannot
        # contain nested environments in its items.  If that's the
        # case, end the item here.
        if len(self.__stack) > 0:
            top_type, top_indentation = self.__stack[-1]
            if top_type in self.__non_nestable_types:
                self.__formatter.EndItem(top_type)
        # Start te environment.
        self.__formatter.StartList(type)
        # Push it onto the stack.
        self.__stack.append((type, indentation))


    def __PopType(self):
        """End and remove the innermost environment."""

        # Get the topmost environment on the stack.
        top_type, top_indentation = self.__stack[-1]
        # End the environment.
        self.__formatter.EndList(top_type)
        # Remove it from the stack.
        self.__stack.pop()
        # The new innermost environment may be of a type that cannot
        # contain nested environments.  If it is, then we
        # (prematurely) ended an item when we opened the environment
        # that just closed.  We'll have to open a new item here.
        if len(self.__stack) > 0:
            top_type, top_indentation = self.__stack[-1]
            if top_type in self.__non_nestable_types:
                self.__formatter.StartItem(top_type)


    def __SetType(self, type, indentation, label=None):
        """Set the environment type and indentation level."""
        
        while 1:
            # Look at the current innermost environment (if there is
            # eone). 
            if len(self.__stack) == 0:
                top_indentation = -1
            else:
                top_type, top_indentation = self.__stack[-1]

            # Are we outdented from the current environment and
            # indentation level, or at the same indentation?
            if indentation <= top_indentation:
                # End the previous item.
                self.__formatter.EndItem(top_type)
                if indentation < top_indentation:
                    # We're outdented, so end the previous environment.
                    self.__PopType()
                elif top_type != type:
                    # Same indentation but different environment type.
                    # End the previous environment, and start a new
                    # one.
                    self.__PopType()
                    self.__PushType(type, indentation)
                else:
                    # Same indentation, same environment.  We just
                    # need a new item, so fall through.
                    break
            else:
                # We're indented.  Nest a new environment in the
                # current item.
                self.__PushType(type, indentation)
                break

        # Start a new item in the current environment.
        self.__formatter.StartItem(type, label)
        if type == "definition list":
            self.__WriteText(label)
            self.__formatter.FinishDefinedTerm()


    def __WriteText(self, text):
        """Write paragraph text."""

        # Look for various types of markup for special formatting for
        # a range of text.
        for regex, style in [
            (self.__verbatim_regex, "verbatim"),
            (self.__strong_regex, "strong"),
            (self.__emph_regex, "emphasized"),
            (self.__underline_regex, "underlined"),
            ]:
            # Find the first match.
            match = regex.search(text)
            if match is not None:
                # Found a match.  Recursively format everything up to
                # the start of the match.
                self.__WriteText(text[:match.end(1)])
                # Start generating text in the indicated style.
                self.__formatter.StartStyle(style)
                # If it's a verbatim style, push the verbatim text out
                # directly.  Otherwise, format it recursively.
                if style == "verbatim":
                    self.__formatter.WriteText(match.group(2))
                else:
                    self.__WriteText(match.group(2))
                # Stop generating text in the specified style.
                self.__formatter.EndStyle(style)
                # Recursively format everything following the match.
                self.__WriteText(text[match.start(3):])
                return

        # Look for hyperlink markup.
        match = self.__link_regex.search(text)
        if match is not None:
            link_text = string.strip(match.group(1))
            # Is there a footnote providing a link target for this
            # phrase? 
            if self.__hyperlinks.has_key(link_text):
                # Yes.  Emit a hyperlink.
                link_target = self.__hyperlinks[link_text]
                # Recursively format everything up to the start of the
                # match.
                self.__WriteText(text[:match.start(0)])
                # Generate the start of the link.
                self.__formatter.StartLink(link_target)
                # Recursively format the link text.
                self.__WriteText(match.group(1))
                # End the link.
                self.__formatter.EndLink()
                # Recursively format everything following the match.
                self.__WriteText(text[match.end(1) + 1:])
                return
            else:
                # Fall through and format the entire text as usual.
                pass

        # Nothing special.  Write ordinary text.
        self.__formatter.WriteText(text)



########################################################################
# functions
########################################################################

def escape_html_entities(text):
    """Return 'text' with special characters converted to HTML entities."""

    return __entity_char_regex.sub(__entity_char_replacement, text)


def __format(text, formatter):
    """Process structured text 'text' with 'formatter'."""

    processor = StructuredTextProcessor(formatter)
    processor(text)
    processor.End()


def to_html(structured_text):
    """Return 'structured_text' formatted as HTML."""

    # Create an HTML formatter that dumps its output to a StringIO.
    output_string = cStringIO.StringIO()
    formatter = HtmlFormatter(output_string)
    # Generate output.
    __format(structured_text, formatter)
    # Return the resulting text.
    return output_string.getvalue()
    

def to_text(structured_text, width=78, indent=0):
    """Return 'structured_text' formatted as plain text.

    'width' -- The width of the text (including the indentation).

    'indent' -- The width of the block indentation of the formatted
    output."""

    # Create a text formatter that dumps its output to a StringIO.
    output_string = cStringIO.StringIO()
    formatter = TextFormatter(output_string, width=width, indent=indent)
    # Generate output.
    __format(structured_text, formatter)
    # Return the resulting text.
    return output_string.getvalue()


def get_first(structured_text):
    """Return the first line of 'structured_text'.

    By convention, the first line of a structured text description is a
    short summary."""

    return string.split(structured_text, "\n", 1)[0]


def get_rest(structured_text):
    """Return the contents of 'structured_text' minus the first line."""

    parts = string.split(structured_text, "\n", 1)
    # There may not be more than one line; handle this gracefully.
    if len(parts) > 0:
        return parts[1]
    else:
        return ""

        
def get_paragraphs(structured_text):
    """Split 'structured_text' into paragraphs.

    'structured_text' -- A string consisting of structured text.
    
    returns -- A sequence of pagraphs of structured text.  Each
    element in the sequence corresponds to a successive pagraph
    in the 'structured_text'.  If 'structured_text' is the empty
    string, the sequence returned will consist of a single
    paragraph, itself empty."""

    return __paragraph_regex.split(structured_text)


def get_first_paragraph(structured_text):
    """Return the first paragraph of 'structured_text'.

    'structured_text' -- A string consisting of structured text.

    returns -- A string of structured text that is the first paragraph
    of the 'structured_text'."""

    return get_paragraphs(structured_text)[0]
    
########################################################################
# variables
########################################################################

# Write a regular expression for finding characters that need to be
# escaped as HTML entities.
__entity_char_regex = htmlentitydefs.entitydefs.values()
# FIXME: Only handle single-byte characters.
__entity_char_regex = filter(lambda l: len(l) == 1, __entity_char_regex)
__entity_char_regex = "[" + string.join(__entity_char_regex, "") + "]"
__entity_char_regex = re.compile(__entity_char_regex)

# Generate a replacement function for special characters to HTML
# entities.  Start by creating a map from the character to the
# corresponding HTML entity code.
__entity_char_replacement = {}
for entity, character in htmlentitydefs.entitydefs.items():
    if len(character) == 1:
        __entity_char_replacement[character] = "&%s;" % entity
# Write a function for use as the regex replacement that looks up the
# corresponding entity for a matched character.
__entity_char_replacement = lambda match, \
                                   replacement_map=__entity_char_replacement: \
                            replacement_map[match.group(0)]

# Regex matching paragraph separators.
__paragraph_regex = re.compile("(?:\n *)+\n", re.MULTILINE)

########################################################################
# script
########################################################################

# If invoked as a script, act as a structured text processor.

if __name__ == "__main__":
    # Parse command-line options.
    import getopt
    long_options = [
        "html",
        "text",
        ]
    options, arguments = getopt.getopt(sys.argv[1:], "", long_options)
    # Interpret them.
    formatter = None
    for option, option_argument in options:
        if option == "--html":
            formatter = HtmlFormatter()
        elif option == "--text":
            formatter = TextFormatter()
    # Use a text formatter by default.
    if formatter is None:
        formatter = TextFormatter()

    # Fire up a processor.
    processor = StructuredTextProcessor(formatter)

    # Were input files specified on the command line?
    if len(arguments) == 0:
        # No; read from standard input.
        inputs = (sys.stdin, )
    else:
        # Yes; open them all.
        inputs = map(lambda file_name: open(file_name, "rt"), arguments)

    # Loop over inputs.
    for input in inputs:
        # Read in each one, and process it.
        processor(input.read())

    # End processing.
    processor.End()

    # All done.
    sys.exit(0)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

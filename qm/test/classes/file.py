########################################################################
#
# File:   file.py
# Author: Alex Samuel
# Date:   2001-06-21
#
# Contents:
#   Test classes involving file contents.
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

"""File-related test classes."""

########################################################################
# imports
########################################################################

import qm.fields
import qm.test.base
from   qm.test.base import Result
import qm.web
import re
import string

########################################################################
# classes
########################################################################

class SubstitutionField(qm.fields.TextField):
    """A rule for performing a text substitution.

    A 'SubstitutionField' consists of a regular expression pattern and a
    corresponding replacement string.  When the substitution is applied
    to a body of text, all substrings that match the pattern are
    replaced with the substitution string.

    The syntax for the regular expression and the substitution string is
    that of the standard Python 're' (regular expression) module."""

    class_name = "qm.test.classes.file.SubstitutionField"

    # The pattern and replacement string are encoded together into a
    # single string, separated by a semicolon.  Semicolons that occur
    # within the pattern and replacement string are escaped with a
    # backslash.
    #
    # Use 'SplitValue' to extract the pattern and replacement string
    # from a value of this field.


    def __init__(self, name, **properties):
        """Create a new 'SubstitutionField'.

        By default, the pattern and replacement string are empty."""

        # Initialize the base class.
        apply(qm.fields.TextField.__init__, (self, name, ";"), properties)


    def SplitValue(self, value):
        """Split a value of this field into the pattern and replacement string.

        'value' -- A value for this field.

        returns -- A pair '(pattern, replacement_string)'."""

        # Be lenient about an empty string.
        if value == "":
            return ("", "")
        # Break it in half.
        elements = string.split(value, ";", 1)
        # Unescape semicolons in both halves.
        elements = map(lambda e: string.replace(e, r"\;", ";"), elements) 
        return elements


    def FormatValueAsHtml(self, value, style, name=None):
        pattern, replacement = self.SplitValue(value)
        # Since we're generating HTML, escape special characters.
        pattern = qm.web.escape(pattern)
        replacement = qm.web.escape(replacement)

        if style in ["new", "edit"]:
            result = '''
            <input type="hidden"
                   name="%(name)s"
                   value="%(value)s"/>
            <table border="0" cellpadding="0" cellspacing="4">
             <tr>
              <td>Pattern:</td>
              <td>&nbsp;</td>
              <td><input type="text"
                         size="40"
                         name="pattern"
                         onchange="update_substitution();"
                         value="%(pattern)s"/></td>
             </tr>
             <tr>
              <td>Replacement:</td>
              <td>&nbsp;</td>
              <td><input type="text"
                         size="40"
                         name="substitution"
                         onchange="update_substitution();"
                         value="%(replacement)s"/></td>
             </tr>
            </table>
            <script language="JavaScript">
            function update_substitution()
            {
              var pattern = document.form.pattern.value;
              pattern = pattern.replace(/;/g, "\\;");
              var substitution = document.form.substitution.value;
              substitution = substitution.replace(/;/g, "\\;");
              document.form.%(name)s.value = pattern + ";" + substitution;
            }
            </script>
            ''' % locals()
            return result

        elif style == "full":
            return '''
            <table border="0" cellpadding="2" cellspacing="0">
             <tr valign="top">
              <td>Pattern:</td>
              <td><tt>%s</tt></td>
             </tr>
             <tr valign="top">
              <td>Replacement:</td>
              <td><tt>%s</tt></td>
             </tr>
            </table>
            ''' % (pattern, replacement)

        else:
            # For all other styles, use the base class implementation.
            return qm.fields.TextField.FormatValueAsHtml(
                self, value, style, name)


    def FormatValueAsText(self, value, columns=72):
        # Don't line-wrap or otherwise futz with the value.
        return value


    def GetHelp(self):
        return """
        A substitution consists of a regular expression pattern and a
        substitution string.  When the substitution is applied, all
        subtrings matching the pattern are replaced with the
        substitution string.  The substitution string may reference
        matched groups in the pattern.

        The regular expression and substitution syntax are those of
        Python's standard "'re' regular expression module"

.. "'re' regular expression module" http://www.python.org/doc/1.5.2p2/lib/module-re.html ."""



class FileContentsTest:
    """Check that the contents of a file match the expected value.

    A 'FileContentsTest' examines the contents of a file.  The test
    passes if and only if the contents exactly match the expected value.

    The path to the file itself is not specified explicitly in the test.
    Instead, it is taken from a contex property; the name of that
    variable is specified in the **Path Property** field.

    Optionally, the test may specify one or more substitutions.  Each
    substitution consists of a regular expression pattern and a
    replacement string.  Both the actual file contents and the expected
    file contents are processed with these substitutions, with all
    pattern matches replaced with the corresponding substitutions,
    before the comparison is performed."""

    fields = [
        qm.fields.TextField(
            name="path_property",
            title="Path Property",
            description="""The context property naming the file.

            The context property given here will contain the path name
            of the file.""",
            not_empty_text=1,
            default="path"),

        qm.fields.TextField(
            name="expected_contents",
            title="Expected Contents",
            description="""The expected contents of the file.""",
            verbatim="true",
            multiline="true"),

        qm.fields.SetField(SubstitutionField(
            name="substitutions",
            title="Substitutions",
            description="""Regular expression substitutions.

            Each substitution will be applied to both the expected and
            actual contents of the file.  The comparison will be
            performed after the substitutions have been performed.

            You can use substitutions to ignore insignificant
            differences between the expected and autual contents.""")),
        ]


    def __init__(self,
                 path_property,
                 expected_contents,
                 substitutions):
        self.__path_property = path_property
        self.__substitutions = substitutions
        # Might as well perform substitutions on the expected contents here.
        expected_contents = self.__PerformSubstitutions(expected_contents)
        self.__expected_contents = expected_contents


    def Run(self, context):
        # Extract the path to the file we're testing.
        try:
            path = context[self.__path_property]
        except KeyError:
            # The path is not present in the context under the expected
            # property name.
            return Result(Result.FAIL,
                          cause="Missing property '%s' in context." %
                          self.__path_property)
        # Read the contents of the file.
        try:
            contents = open(path, "r").read()
        except IOError, exception:
            # Couldn't read the file.
            return Result(Result.FAIL,
                          cause="Could not open file '%s'." % path,
                          error=str(exception))
        # Perform substitutions on the file contents.
        contents = self.__PerformSubstitutions(contents)
        # Compare the contnets to the expected contents.
        if contents == self.__expected_contents:
            return Result(Result.PASS)
        else:
            return Result(Result.FAIL,
                          cause="Contents do not match expected contents.",
                          contents=contents,
                          expected_contents=self.__expected_contents)


    def __PerformSubstitutions(self, text):
        """Perform substitutions on a body of text.

        returns -- The string 'text', processed with the substitutions
        configured for this test instance."""

        substitutions_field = self.fields[2].GetContainedField()
        for substitution in self.__substitutions:
            pattern, replacement = substitutions_field.SplitValue(substitution)
            text = re.sub(pattern, replacement, text)
        return text



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

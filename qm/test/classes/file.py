########################################################################
#
# File:   file.py
# Author: Alex Samuel
# Date:   2001-06-21
#
# Contents:
#   Test classes involving file contents.
#
# Copyright (c) 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

"""File-related test classes."""

########################################################################
# imports
########################################################################

import qm.fields
import qm.test.base
from   qm.test.result import *
from   qm.test.test import *
import qm.web
import re
import string

########################################################################
# classes
########################################################################

class SubstitutionField(qm.fields.TupleField):
    """A rule for performing a text substitution.

    A 'SubstitutionField' consists of a regular expression pattern and a
    corresponding replacement string.  When the substitution is applied
    to a body of text, all substrings that match the pattern are
    replaced with the substitution string.

    The syntax for the regular expression and the substitution string is
    that of the standard Python 're' (regular expression) module."""

    class_name = "qm.test.classes.file.SubstitutionField"

    def __init__(self, name, **properties):
        """Create a new 'SubstitutionField'.

        By default, the pattern and replacement string are empty."""

        # Initialize the base class.
        fields = (qm.fields.TextField(name = "pattern",
                                      title = "Pattern",),
                  qm.fields.TextField(name = "replacement",
                                      title = "Replacement"))
        qm.fields.TupleField.__init__(self, name, fields, **properties)


    def GetHelp(self):
        return """
        A substitution consists of a regular expression pattern and a
        substitution string.  When the substitution is applied, all
        subtrings matching the pattern are replaced with the
        substitution string.  The substitution string may reference
        matched groups in the pattern.

        The regular expression and substitution syntax are those of
        Python's standard "'re' regular expression module"."""



class FileContentsTest(Test):
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

    arguments = [
        qm.fields.TextField(
            name="path_property",
            title="Path Property",
            description="""The context property naming the file.

            The context property given here will contain the path name
            of the file.""",
            not_empty_text=1,
            default_value="path"),

        qm.fields.TextField(
            name="expected_contents",
            title="Expected Contents",
            description="""The expected contents of the file.""",
            verbatim="true",
            multiline="true",
            default_value=""),

        qm.fields.SetField(SubstitutionField(
            name="substitutions",
            title="Substitutions",
            description="""Regular expression substitutions.

            Each substitution will be applied to both the expected and
            actual contents of the file.  The comparison will be
            performed after the substitutions have been performed.

            You can use substitutions to ignore insignificant
            differences between the expected and autual contents."""))
        ]


    def Run(self, context, result):
        # Extract the path to the file we're testing.
        path = context[self.path_property]
        # Read the contents of the file.
        contents = open(path, "r").read()
        # Perform substitutions on the file contents.
        self.expected_contents = \
          self.__PerformSubstitutions(self.expected_contents)
        contents = self.__PerformSubstitutions(contents)
        # Compare the contents to the expected contents.
        if contents != self.expected_contents:
            result.Fail("Contents do not match expected contents.",
                        { "FileContentsTest.contents" : contents,
                          "FileContentsTest.expected_contents" :
                          self.expected_contents })


    def __PerformSubstitutions(self, text):
        """Perform substitutions on a body of text.

        returns -- The string 'text', processed with the substitutions
        configured for this test instance."""

        for pattern, replacement in self.substitutions:
            text = re.sub(pattern, replacement, text)
        return text



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

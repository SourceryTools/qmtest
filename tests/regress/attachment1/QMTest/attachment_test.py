########################################################################
#
# File:   attachment_test.py
# Author: Mark Mitchell
# Date:   2003-07-21
#
# Contents:
#   Test classes for tests written in Python.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import qm.fields
from   qm.test.test import Test

########################################################################
# Classes
########################################################################

class AttachmentTest(Test):
    """An 'AttachmentTest' has a single attachment.

    This test class is used to validate QMTest's attachment processing."""
    
    arguments = [
        qm.fields.AttachmentField(
            name="attachment"
            )
        ]


    def Run(self, context, result):

        if (self.attachment.GetData()
            != "The quick brown fox jumped over the lazy dog.\n"):
            result.Fail("Incorrect attachment contents.")

########################################################################
#
# File:   discussion.py
# Author: Alex Samuel
# Date:   2001-05-27
#
# Contents:
#   Trigger for managing discussion fields.
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

import qm.track.issue_class
from   qm.track.issue_class import TriggerResult
import string
import types

########################################################################
# classes
########################################################################

class DiscussionTrigger(qm.track.issue_class.Trigger):
    """Trigger to manage a 'DiscussionField'."""

    def __init__(self, name, field_name):
        """Create a new trigger.

        'name' -- The trigger name.

        'field_name' -- The name of the field containing the
        discussion.  The field should be a
        'qm.track.issue_class.DiscussionField' field."""
        
        # Initialize the base class.
        qm.track.issue_class.Trigger.__init__(self, name)
        # Remember the field name.
        self.__field_name = field_name


    def Preupdate(self, issue, previous_issue):
        field = issue.GetClass().GetField(self.__field_name)
        contained_field = field.GetContainedField()

        # Extract the value being set for this issue.
        value = issue.GetField(self.__field_name)
        if type(value) is types.StringType:
            # Normally, since 'DiscussionField' is a 'SetField'
            # subclass, the value is a list.  However, when the user
            # edits the issue, we may have a string instead,
            # representing a new discussion element.  As a starting
            # point, extract the old field value, which should be a list
            # of previous discussion elements.
            if previous_issue is not None:
                previous_value = previous_issue.GetField(self.__field_name)
            else:
                previous_value = []
            if value != "":
                # The user added a new discussion element.  Prepend a
                # line stating the user's ID and the current time.
                user = issue.GetFieldAsText("user")
                timestamp = issue.GetFieldAsText("timestamp")
                value = "On %s, %s wrote:\n%s" % (timestamp, user, value)
                # Append the discussion element to the previous value of
                # this field.
                new_value = previous_value + [value]
            else:
                # If it's empty, don't add a new element.  Keep the
                # previous field value.
                new_value = previous_value
            # Replace the string with a list.
            issue.SetField(self.__field_name, new_value)

        # Proceed as usual.
        return TriggerResult(self, TriggerResult.ACCEPT)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

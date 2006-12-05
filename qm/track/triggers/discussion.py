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
# For license terms see the file COPYING.
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

    class_name = "qm.track.triggers.discussion.DiscussionTrigger"

    property_declarations = \
        qm.track.issue_class.Trigger.property_declarations + (
        qm.fields.PropertyDeclaration(
            name="field_name",
            description="The name of the discussion field.",
            default_value="discussion"
            ),

        )


    def __init__(self, name, field_name, **properties):
        """Create a new trigger.

        'name' -- The trigger name.

        'field_name' -- The name of the field containing the
        discussion.  The field should be a
        'qm.track.issue_class.DiscussionField' field."""
        
        # Initialize the base class.
        apply(qm.track.issue_class.Trigger.__init__,
              (self, name),
              properties)
        # Store the discussion field name.
        self.SetProperty("field_name", field_name)


    def Preupdate(self, issue, previous_issue):
        field_name = self.GetProperty("field_name")
        field = issue.GetClass().GetField(field_name)
        contained_field = field.GetContainedField()

        # Extract the value being set for this issue.
        value = issue.GetField(field_name)
        if type(value) is types.StringType:
            # Normally, since 'DiscussionField' is a 'SetField'
            # subclass, the value is a list.  However, when the user
            # edits the issue, we may have a string instead,
            # representing a new discussion element.  As a starting
            # point, extract the old field value, which should be a list
            # of previous discussion elements.
            if previous_issue is not None:
                previous_value = previous_issue.GetField(field_name)
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
            issue.SetField(field_name, new_value)

        # Proceed as usual.
        return TriggerResult(self, TriggerResult.ACCEPT)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

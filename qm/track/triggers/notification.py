########################################################################
#
# File:   notification.py
# Author: Alex Samuel
# Date:   2001-05-03
#
# Contents:
#   Trigger for email notificaiton.
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

"""Triggers for email notification of changes to issues.

The 'Trigger' class in this module sends notification email messages
when an issue has changed.

Each trigger instance has an associated condition which specifies
whether, for a given issue update, notification should be sent.  The
condition is a Python expression, which is evaluated according to
'qm.track.issue.eval_revision_expression'.

This module includes several trigger classes, which differ in how they
determine the recipients of the notification.

  'NotifyFixedTrigger' -- The subscribers are specified in the trigger's
  configuration.  A subscriber may be specified by email address or UID.

  'NotifyByAddressFieldTrigger' -- The subscribers are extracted from a
  field containing email addresses.  The field may be a text field (at
  most one address) or a set-of-text field (arbitrarily many subscriber
  addresses).

  'NotifyByUidFieldTrigger' -- The subscribers are extracted from a field
  containing UIDs.  Notification is sent to any of those users who have
  an email address in the user database.  The field may be a UID field
  (at most one UID) or a set-of-UID field (arbitrarily many subscriber
  UIDs).
"""

########################################################################
# imports
########################################################################

import qm.common
import qm.fields
import qm.platform
import qm.track.issue
import qm.track.issue_class
from   qm.track.issue_class import TriggerResult
import qm.user
import string

########################################################################
# classes
########################################################################

class _NotifyTrigger(qm.track.issue_class.Trigger):
    """Base class for email notification triggers."""

    # This class includes logic for evaluating the condition under which
    # notification is sent, as well as logic for generating the
    # notification message itself.  Subclasses specify the list of
    # subscribers of the notification by providing a
    # 'GetSubscriberAddresses' method.
    
    property_declarations = \
        qm.track.issue_class.Trigger.property_declarations + (
        qm.fields.PropertyDeclaration(
            name="condition",
            description="""A Python expression specifying the
            condition under which to send a notification
            message.""",
            default_value="1"),

        qm.fields.PropertyDeclaration(
            name="from_address",
            description="""The email address from which notification
            messages should originate.""",
            default_value="qmtrack@%s" % qm.platform.get_host_name()),

        qm.fields.PropertyDeclaration(
            name="subject_prefix",
            description="""The prefix for the subject line of
            notification messdages.""",
            default_value="[QMTrack] "),

        )


    def __init__(self, name, condition, **properties):
        """Construct a new trigger.

        'name' -- The name of the trigger instance.

        'condition' -- The text of a Python expression which must
        evaluate to true for notification to be sent."""

        # Initialize the base class.
        apply(qm.track.issue_class.Trigger.__init__, (self, name), properties)
        # Set up attributes.
        self.SetProperty("condition", condition)


    def GetCondition(self):
        """Return the expression representing the notification condition."""

        return self.GetProperty("condition")


    def SetFromAddress(self, address):
        """Set the address from which notification email originates.

        'address' -- An email address to be used in the 'From' field of
        notification messages."""

        self.SetProperty("from_address", address)


    def SetSubjectPrefix(self, prefix):
        """Set the subject prefix for notification messages.

        'prefix' -- Text that will be prepended to the subject of
        notification email messages."""

        self.SetProperty("subject_prefix", prefix)
        

    def Postupdate(self, issue, previous_issue):
        # Evaluate the condition.
        condition = self.GetCondition()
        result = qm.track.issue.eval_revision_expression(condition, issue,
                                                         previous_issue)
        # Did the condition return a true value?
        if result:
            # Yes.  We should send notification.  Find the list of
            # subscribers. 
            subscribers = self.GetSubscriberAddresses(issue)
            if len(subscribers) == 0:
                # No subscribers, so nothing to do.
                return
            # Write the notification message.
            message = self.__MakeMessage(issue, previous_issue)
            # Construct the subject.
            if previous_issue is None:
                subject = "new issue %s" % issue.GetId()
            else:
                subject = "modification to issue %s" % issue.GetId()
            # Add the prefix.
            subject = self.GetProperty("subject_prefix") + " " + subject
            # Send the message.
            from_address = self.GetProperty("from_address")
            qm.platform.send_email(message,
                                   subject=subject,
                                   recipients=subscribers,
                                   from_address=from_address)


    # Internal methods.

    def __MakeMessage(self, issue, previous_issue):
        """Write the notification message.

        'issue' -- The issue following the update.

        'previous_issue' -- The previous revision of the issue, before
        the update, or 'None' if this is a new issue."""
        
        # Write a summary of who changed the issue and when.
        user = issue.GetFieldAsText("user")
        timestamp = issue.GetFieldAsText("timestamp")
        if previous_issue is None:
            message = "The issue %s was created by %s on %s.\n\n" \
                      % (issue.GetId(), user, timestamp) 
            # Show all fields in the notification.
            fields_to_show = issue.GetClass().GetFields()
        else:
            message = "The issue %s was changed by %s on %s.\n\n" \
                      % (issue.GetId(), user, timestamp) \
                      + "The following fields were modified:\n\n"
            # Find the fields that have been changed in the new revision.
            fields_to_show = qm.track.issue.get_differing_fields(
                previous_issue, issue)
        # Briefly summarize the change to each field.
        for field in fields_to_show:
            # Skip hidden fields.
            if field.IsProperty("hidden"):
                continue
            name = field.GetName()
            # Extract the value and convert it to plain text.
            value = issue.GetField(name)
            value = field.FormatValueAsText(value, columns=66)
            message = message + "  %s: " % field.GetTitle()
            # Does it require more than one line?
            if "\n" in value:
                # Yes.  Break it into lines and indent it, for
                # readability. 
                message = message + "\n" \
                          + qm.common.indent_lines(value, 6)
            else:
                # One line; nothing special to do.
                message = message + value
            message = message + "\n"
        # All done.
        return message



class NotifyFixedTrigger(_NotifyTrigger):
    """Notification trigger with fixed configuration.

    The 'Trigger' class in this module sends notification email messages
    when an issue has changed.

    The trigger has an associated condition which specifies whether, for
    a given issue update, notification should be sent.  The condition is
    a Python expression, which is evaluated according to
    'qm.track.issue.eval_revision_expression'.

    The notification subscribers are part of the trigger's configuration.
    Subscribers may be specified by email address or by user ID."""

    class_name = "qm.track.triggers.notification.NotifyFixedTrigger"


    def __init__(self,
                 name,
                 condition,
                 **properties):
        """Create a new trigger instance.

        'name' -- The name of the trigger instance.

        'condition' -- A Python expression representing the condition
        under which to send notification."""
        
        # Initialize the base class.
        apply(_NotifyTrigger.__init__, (self, name, condition), properties)


    def GetSubscriberAddresses(self, issue):
        """Return a sequence of email addresses of subscribers."""
        
        # Start with subscribers listed by email address.
        result = self.GetRecipientAddresses()
        # Add email addresses of subscribed users.
        for uid in self.GetRecipientUids():
            try:
                user = qm.user.database[uid]
            except KeyError:
                # No such user; skip silently.
                continue
            # Get the user's email address.
            email_address = user.GetInfoProperty("email", None)
            if email_address is None:
                # Silently ignore if 'user' has no email address.
                continue
            else:
                # Add the email address.
                result.append(email_address)
        return result


    def SetRecipientAddresses(self, addresses):
        """Set the recipients by email address.

        'addresses' -- The sequence of email addresses of recipients who
        are specified by email address."""

        self.SetProperty("recipient_addresses", string.join(addresses, ","))


    def GetRecipientAddresses(self):
        """Return a sequence of recipients specified by email address."""

        return string.split(self.GetProperty("recipient_addresses"), ",")


    def SetRecipientUids(self, user_ids):
        """Set the recipients by user ID.

        'user_ids' -- The sequence of user IDs of recipients who are
        specified by user ID."""

        self.SetProperty("recipient_uids", string.join(user_ids, ","))


    def GetRecipientUids(self):
        """Return a sequence of recipients specified by user ID."""

        return string.split(self.GetProperty("recipient_uids"), ",")


    def AddRecipientAddress(self, address):
        """Add email 'address' to the list of recipients."""

        addresses = self.GetRecipientAddresses()
        addresses.append(address)
        self.SetRecipientAddresses(addresses)


    def AddRecipientUid(self, uid):
        """Add the user with ID 'uid' to the list of recipients.

        Adds the user's email address, if it is specified in the user
        database.  If there is no user with ID 'uid', does nothing.
        Note that notification email is sent only to users for whom an
        email address is specified in the user database."""

        database = qm.user.database
        # Extract the user with ID 'uid'.
        try:
            user = database[uid]
        except KeyError:
            # FIXME?
            # Silently ignore invalid user IDs.
            return
        else:
            uids = self.GetRecipientUids()
            uids.append(user)
            self.SetRecipientUids(uids)



class _NotifyByFieldTrigger(_NotifyTrigger):
    """Base class for triggers which extract subscribers from a field."""

    property_declarations = \
        _NotifyTrigger.property_declarations + (
        qm.fields.PropertyDeclaration(
            name="field_name",
            description="The name of the field listing notification "
            "subscribers.",
            default_value="subscribers"),

        )


    def __init__(self, name, condition, field_name, **properties):
        """Create a new trigger instance.

        'name' -- The name of the trigger instance.

        'condition' -- A Python expression representing the condition
        under which to send notification.

        'field_name' -- The name of the field from which subscribers will
        be extracted.  The field must either be a text field, or a set
        field containing a text field.  (Subclasses of a text field may
        be substituted.)"""

        # Initialize the base class.
        apply(_NotifyTrigger.__init__, (self, name, condition), properties)
        # Remeber the field name.
        self.SetProperty("field_name", field_name)


    def GetFieldName(self):
        """Return the name of the issue field containing recipients."""

        return self.GetProperty("field_name")


    def GetFieldContents(self, issue):
        """Return the contents of the field containing subscribers.

        returns -- A sequence of strings."""

        # Extract the field object.
        issue_class = issue.GetClass()
        field_name = self.GetFieldName()
        field = issue_class.GetField(field_name)
        # Get the field value for the issue.
        value = issue.GetField(field_name)
        # Is it a text field (or subclass)?
        if isinstance(field, qm.fields.TextField):
            # Yes; the value is the single subscriber, unless it's an
            # empty string.
            if string.strip(value) == "":
                return []
            else:
                return [value]
        # Is it a set-of-text field?
        elif isinstance(field, qm.fields.SetField) \
             and isinstance(field.GetContainedField(), qm.fields.TextField):
            # Yes; the value is a sequence of subscribers.
            return value
        else:
            # Can't handle this field type.
            raise RuntimeError, \
                  "field %s is an invalid type" % field_name
    


class NotifyByAddressFieldTrigger(_NotifyByFieldTrigger):
    """Trigger which extracts subscriber email addresses from a field.

    The 'Trigger' class in this module sends notification email messages
    when an issue has changed.

    The trigger has an associated condition which specifies whether, for
    a given issue update, notification should be sent.  The condition is
    a Python expression, which is evaluated according to
    'qm.track.issue.eval_revision_expression'.

    The subscribers are extracted from a field containing email
    addresses.  The field may be a text field (at most one address) or a
    set-of-text field (arbitrarily many subscriber addresses)."""

    class_name = "qm.track.fields.notification.NotifyByAddressFieldTrigger"


    def __init__(self, name, condition, address_field_name, **properties):
        """Create a new trigger instance.

        'name' -- The name of the trigger instance.

        'condition' -- A Python expression representing the condition
        under which to send notification.

        'address_field_name' -- The name of the issue field which
        contains the email address or addresses of notification
        subscribers.  The field may be a text field or a set-of-text
        field.""" 

        # Initialize the base class.
        apply(_NotifyByFieldTrigger.__init__,
              (self, name, condition, address_field_name),
              properties)


    def GetSubscriberAddresses(self, issue):
        return self.GetFieldContents(issue)



class NotifyByUidFieldTrigger(_NotifyByFieldTrigger):
    """Trigger which extracts subscriber email addresses from a field.

    The 'Trigger' class in this module sends notification email messages
    when an issue has changed.

    The trigger has an associated condition which specifies whether, for
    a given issue update, notification should be sent.  The condition is
    a Python expression, which is evaluated according to
    'qm.track.issue.eval_revision_expression'.

    The subscribers are extracted from a field containing UIDs.
    Notification is sent to any of those users who have an email address
    in the user database.  The field may be a UID field (at most one
    UID) or a set-of-UID field (arbitrarily many subscriber UIDs).

    Additionally, this trigger may be configured to subscribe
    automatically users who modify the issue.  This automatic
    subscription may be predicated on a condition expression.  The user
    is subscribed automatically, this is performed before notifications
    are issued, so a user who modifies the issue and is automatically
    subscribed will receive notification for the same revision (if the
    revision satisfies the notification condition)."""

    class_name = "qm.track.triggers.notification.NotifyByUidFieldTrigger"

    property_declarations = \
        _NotifyByFieldTrigger.property_declarations + (
        qm.fields.PropertyDeclaration(
            name="subscription_condition",
            description="A Python issue expression.  If the issue "
            "evaluates to true when the issue is modified, the "
            "modifying user is automatically subscribed.",
            default_value="0"),

        )


    def __init__(self,
                 name,
                 condition,
                 field_name,
                 subscription_condition="0",
                 **properties):
        """Create a new trigger instance.

        'name' -- The name of the trigger instance.

        'field_name' -- The name of the issue field which contains
        the email address or addresses of notification subscribers.  The
        field may be a UID field or a set-of-UID field.

        'subscription_condition' -- A Python expression representing the
        condition under which to send notification."""

        # Initialize the base class.
        apply(_NotifyByFieldTrigger.__init__,
              (self, name, condition, field_name),
              properties)
        # Store the subscription condition.
        self.SetProperty("subscription_condition", subscription_condition)


    def GetSubscriberAddresses(self, issue):
        # Get the field contents, which is a list of UIDs.
        uids = self.GetFieldContents(issue)
        # Loop over UIDs, extracting corresponding email addresses.
        database = qm.user.database
        addresses = []
        for uid in uids:
            # Extract the user.
            try:
                user = database[uid]
            except KeyError:
                # FIXME?
                # Silently ignore invalid user IDs.
                pass
            else:
                # Got the user.  Get his/her email address.
                email_address = user.GetInfoProperty("email", None)
                if email_address is not None:
                    addresses.append(email_address)
                else:
                    # Silently ignore users without email addresses.
                    pass
        return addresses


    def SetSubscriptionCondition(self, subscription_condition):
        """Set the condition for automatic subscription.

        'subscriptio_condition' -- A Python expression specifying the
        condition under which the user who modifies the issue will be
        added to the notification list.

        Set the condition to "0" (which always evaluates to false) to
        disable automatic subscription."""

        self.SetProperty("subscription_condition", subscription_condition)


    def GetSubscriptionCondition(self):
        """Return the condition under which users are subscribed."""

        return self.GetProperty("subscription_condition")


    def Preupdate(self, issue, previous_issue):
        subscription_condition = self.GetSubscriptionCondition()
        # Should the user who made the update be subscribed automatically?
        result = qm.track.issue.eval_revision_expression(
            subscription_condition, issue, previous_issue)
        if result:
            # Yes.
            uid = issue.GetField("user")
            current_subscribers = issue.GetField(self._field_name)
            # Is the user already subscribed?
            if uid not in current_subscribers:
                # Find out who was subscribed before the revision.
                if previous_issue is None:
                    previous_subscribers = []
                else:
                    previous_subscribers = previous_issue.GetField(
                        self._field_name)
                # First check if the user was explicitly unsubscribed as
                # part of this revision (i.e. was previously in the
                # subscriber list but is no longer). 
                if uid in previous_subscribers:
                    # Let's not be obnoxious and forcefully resubscribe the
                    # user.
                    pass
                else:
                    # Subscribe the user.
                    current_subscribers.append(uid)
                    issue.SetField(self._field_name, current_subscribers)
        # Proceed as usual.
        return TriggerResult(self, TriggerResult.ACCEPT)



########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

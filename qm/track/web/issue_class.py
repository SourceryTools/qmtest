########################################################################
#
# File:   issue_class.py
# Author: Alex Samuel
# Date:   2001-05-02
#
# Contents:
#   Web GUI for viewing and editing an issue class.
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

import copy
import qm.common
import qm.fields
import qm.label
import qm.track
import qm.track.issue_class
import qm.web
import string
import sys
import web

########################################################################
# classes
########################################################################

class ShowPage(web.DtmlPage):
    """Page for displaying and editing an issue class."""

    mandatory_field_names = qm.track.issue_class.mandatory_field_names

    def __init__(self, issue_class):
        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "issue-class.dtml",
                              issue_class=issue_class)


    def GetFieldType(self, field):
        """Return a description of the type of field 'field', as HTML."""

        if isinstance(field, qm.fields.SetField):
            return "<tt>%s</tt> of <tt>%s</tt>"  \
                   % (field.__class__, field.GetContainedField().__class__)
        else:
            return "<tt>%s</tt>" % field.__class__



class AddFieldPage(web.DtmlPage):
    """Form to add a field to an issue class."""

    field_types = [
        ("integer field", "qm.fields.IntegerField"),
        ("text field", "qm.fields.TextField"),
        ("attachment field", "qm.fields.AttachmentField"),
        ("enumeration field", "qm.fields.EnumerationField"),
        ("time field", "qm.fields.TimeField"),
        ("user ID field", "qm.fields.UidField"),
        ]
    """Names and Python class names of standard field types."""


    def __init__(self,
                 field_name="",
                 field_class_name="",
                 is_set=0,
                 errors={}):
        """Create a new page.

        'errors' -- A map of field errors.  If not empty, we're
        redisplaying the new field form to display errors from an
        invalid form submission.  Each key in 'errors' is a field name,
        either "name" or "type", and the corresponding value is a
        structured text error message describing the problem with the
        value of that field."""
        
        # Initialize the base class.
        web.DtmlPage.__init__(self,
                              "add-issue-field.dtml",
                              field_name=field_name,
                              field_class_name=field_class_name,
                              is_set=is_set)
        # Convert the error messages in 'errors' from structured text to
        # HTML. 
        for key, value in errors.items():
            errors[key] = qm.structured_text.to_html(value)
        self.errors = errors



class AddClassPage(web.DtmlPage):
    """Form for adding a new issue class."""

    def __init__(self, errors={}):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "add-issue-class.dtml")
        # Convert the error messages in 'errors' from structured text to
        # HTML. 
        for key, value in errors.items():
            errors[key] = qm.structured_text.to_html(value)
        self.errors = errors


    def MakeCategoriesControl(self):
        """Construct controls for specifying the categories."""
        
        # Names of HTML form fields.
        field_name = "categories"
        select_name = "_set_" + field_name
        # Generate the popup page to specify each additional category.
        add_page = web.DtmlPage("add-category-name.dtml",
                                field_name=field_name,
                                select_name=select_name)
        add_page = add_page(self.request)
        # Are we redisplaying a form following an invalid submission?
        if len(self.errors) > 0:
            # Yes.  Extract the categories from the submission.
            categories = self.request["categories"]
            initial_elements = qm.web.decode_set_control_contents(categories)
        else:
            # No.  Show the default set of categories.
            initial_elements = qm.track.issue_class.default_categories
        # Construct a list of pairs, which 'make_set_control' needs.
        initial_elements = map(lambda c: (c, c), initial_elements)
        # Construct the control.
        return qm.web.make_set_control(
            form_name="form",
            field_name=field_name,
            select_name=select_name,
            add_page=add_page,
            initial_elements=initial_elements,
            request=self.request)



class ConfigIdbPage(web.DtmlPage):
    """Page for configuring the issue database."""

    def __init__(self):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "config-idb.dtml")


    def GetIssueClasses(self):
        """Return a sequence of issue classes in the IDB."""

        # Generate a list of issue classes in the IDB.
        idb = self.request.GetSession().idb
        issue_classes = idb.GetIssueClasses()
        # Put them into dictionary order.
        issue_classes.sort(lambda c1, c2: cmp(c1.GetName(), c2.GetName()))
        return issue_classes



class NotificationPage(web.DtmlPage):
    """Page for configuring automatic email notification."""

    def __init__(self, trigger):
        """Create a new page object.

        'trigger' -- If modifying an existing 'NotifyFixedTrigger'
        instance, that instance.  Otherwise 'None'."""

        # Initialize the base class.
        web.DtmlPage.__init__(self, "notification.dtml", trigger=trigger)


    def MakeRecipientAddressesControl(self):
        """Construct controls for selecting recipient email addresses."""

        # Field names.
        field_name = "recipient_addresses"
        select_name = "_set_" + field_name
        # Make the popup page for specifying a new address.
        add_page = web.DtmlPage("add-notification-address.dtml",
                                field_name=field_name,
                                select_name=select_name)
        add_page = add_page(self.request)
        # If there already is a notification trigger, include recipients
        # specified in it.
        if self.trigger is not None:
            recipients = self.trigger.GetRecipientAddresses()
            recipients = map(lambda r: (r, r), recipients)
        else:
            recipients = []
        # Build the controls.
        return qm.web.make_set_control(
            form_name="form",
            field_name=field_name,
            select_name=select_name,
            add_page=add_page,
            request=self.request,
            initial_elements=recipients)


    def MakeRecipientUidsControl(self):
        """Construct controls for selecting recipient UIDs."""

        # Field names.
        field_name = "recipient_uids"
        select_name = "_set_" + field_name
        # Make the popup page for selecting a UID to add.
        add_page = web.DtmlPage("add-notification-uid.dtml",
                                field_name=field_name,
                                select_name=select_name,
                                uids=qm.user.database.keys())
        add_page = add_page(self.request)
        # If there is already a notification trigger, include recipient
        # users specified in it.
        if self.trigger is not None:
            recipients = self.trigger.GetRecipientUids()
            recipients = map(lambda r: (r, r), recipients)
        else:
            recipients = []
        # Build the controls.
        return qm.web.make_set_control(
            form_name="form",
            field_name=field_name,
            select_name=select_name,
            add_page=add_page,
            request=self.request,
            initial_elements=recipients)



########################################################################
# functions
########################################################################

# Nothing to do besides generate the page.
handle_config_idb = ConfigIdbPage()
handle_add_field = AddFieldPage()
handle_add_class = AddClassPage()
handle_state_model = web.DtmlPage("state-model.dtml")


def _get_issue_class_for_session(request):
    """Return the issue class object for the session in 'request'."""

    # The issue class object itself should be attached to the session
    # object. 
    session = request.GetSession()
    try:
        issue_class = session.__issue_class
    except AttributeError:
        # Oops, no issue class for this session.
        raise RuntimeError, "No issue class for request."

    return issue_class


def handle_show_class(request):
    """Handle a web request to show and edit an issue class.

    'request' -- A 'WebRequest' object.

    These query field are used from the request object:

      'issue_class' -- The name of the issue class to show."""

    session = request.GetSession()

    try:
        # Try to extract the name of the issue class from the request.
        issue_class_name = request["issue_class"]
    except KeyError:
        # There is no class name specified.  Use the class associated
        # with the session.
        issue_class = _get_issue_class_for_session(request)
    else:
        # Got the issue class name.  Get it from the IDB.
        idb = session.idb
        issue_class = idb.GetIssueClass(issue_class_name)
        # Make a copy of it.
        issue_class = copy.deepcopy(issue_class)
        # Attach the copy to the request.  Subsequent requests refer to
        # this copy by omitting the 'class' query field.
        session.__issue_class = issue_class
        # Now redirect to a page that uses the session's issue class,
        # rather than specifying the issue class explicitly.  Store the
        # internal ID of the copied issue class in the URL, so we can do
        # a sanity check later when the issue class is retrieved from
        # the session.
        del request["issue_class"]
        raise qm.web.HttpRedirect, request

    return ShowPage(issue_class)(request)


def handle_show_field(request):
    """Handle the request to show/edit an issue class field.

    Uses the issue class associated with the request's session.  The
    name of the field is specified in the "field" attribute of the
    request."""

    # Get hold of the field.
    issue_class = _get_issue_class_for_session(request)
    field_name = request["field"]
    field = issue_class.GetField(field_name)
    # This is the request to which to submit edits to the field.  See
    # 'handle_submit_field'. 
    submit_request = request.copy("submit-issue-field")
    # Have the field generate its page.
    return field.GenerateEditWebPage(request, submit_request)


def handle_submit_field(request):
    """Handle the submission of edits to an issue class field.

    Uses the issue class associated with the request's session.  The
    name of the field is specified in the "field" attribute of the
    request."""

    # Get the issue class associated with the session.
    issue_class = _get_issue_class_for_session(request)
    # Get the field.  Its name is included in the request.
    field_name = request["field"]
    field = issue_class.GetField(field_name)

    # Change the field according to the request.
    field.UpdateFromRequest(request)

    # If this is an attachment field (or set thereof), its default value
    # might be an attachment (or list of attachments) that we need to
    # transfer from the temporary attachment database to our permanent
    # attachment store.
    default_value = field.GetDefaultValue()
    idb = request.GetSession().idb
    if isinstance(field, qm.fields.AttachmentField):
        # An attachment field -- process the value.
        default_value = \
            web.store_attachment_data(idb, None, default_value)
        field.SetDefaultValue(default_value)
    elif isinstance(field, qm.fields.SetField) \
         and isinstance(field.GetContainedField(),
                        qm.fields.AttachmentField):
        # An attachment set field -- process each element of the
        # value.
        default_value = map(
            lambda attachment, idb=idb: \
            web.store_attachment_data(idb, None, attachment),
            default_value)
        field.SetDefaultValue(default_value)

    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-issue-class", base=request)


def handle_submit_class(request):
    """Handle a 'submit-issue-class' request.

    This request commits changes to the issue class attached to the
    request's session.

    'request' -- A 'WebRequest' object."""

    session = request.GetSession()

    # Extract the issue class we're submitting, which is associated with
    # the request's session.
    issue_class = _get_issue_class_for_session(request)
    issue_class_name = issue_class.GetName()

    # This should be a revision to an existing issue class.
    idb = session.idb
    previous_issue_class = idb.GetIssueClass(issue_class_name)
    # Replace it.
    idb.UpdateIssueClass(issue_class)

    # Dissociate the issue class from the session. 
    del session.__issue_class    
    # Redirect to the IDB configuration page.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("config-idb", base=request)


def handle_delete_field(request):
    """Handle a 'delete-issue-field' request.

    This request removes a field from the issue class currently being
    edited in the request's session.  The "field" query attribute
    contains the name of the field to delete."""

    # Get hold of the field to delete.
    issue_class = _get_issue_class_for_session(request)
    field_name = request["field"]
    field = issue_class.GetField(field_name)
    # Remove it.
    issue_class.RemoveField(field)
    # Redisplay the issue class.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-issue-class", base=request)


def handle_new_field(request):
    """Handle a 'new-issue-field' request.

    Processes the addition of a new field to the issue class currently
    being editied in the request's session.  These query attributes are
    used from the request:

      'name' -- The name of the new field.

      'type' -- The Python class name of the field type.

      'is_set' -- Either "true" or "false", for whether this is a set
      field.  If it is, 'type' is the name of the contained field type.
    """

    issue_class = _get_issue_class_for_session(request)
    errors = {}

    # Extract the field name.
    field_name = string.strip(request["name"])
    if not qm.label.is_valid(field_name):
        errors["name"] = qm.error("invalid field name", field_name=field_name)
    # Extract the name of the field type.
    field_class_name = string.strip(request["type"])
    try:
        # Load the class.
        field_class = qm.common.load_class(field_class_name, sys.path)
    except (ImportError, ValueError), err:
        # Couldn't load the class.
        errors["type"] = qm.error("invalid field type",
                                  field_type=field_class_name)
    else:
        # Make sure the field type is a subclass of 'Field'.
        if not issubclass(field_class, qm.fields.Field) \
           or field_class is qm.fields.Field:
            errors["type"] = qm.error("invalid field type",
                                      field_type=field_class.__name__)
    # Is this a set field?
    is_set = ["false", "true"].index(request["is_set"])

    if len(errors) > 0:
        # There were errors.  Redisplay the form for adding a new field,
        # showing the values already entered, and the appropriate error
        # messages. 
        page = AddFieldPage(field_name, field_class_name, is_set, errors)
        return page(request)
    else:
        # Good to go.  Instantiate a field object.
        field = field_class(field_name, title=field_name)
        # If a set was requested, wrap it in a 'SetField'.
        if is_set:
            field = qm.fields.SetField(field)
        # Add it to the issue class.
        issue_class.AddField(field)

        # Redirect to the page displaying the new field.
        show_request = qm.web.WebRequest("show-issue-field",
                                         base=request, field=field_name)
        raise qm.web.HttpRedirect, show_request


def handle_new_class(request):
    """Handle a 'new-issue-class' request.

    This request processes the form submission for the creation of a new
    issue class.  These query attributes are used from the request:

      'name' -- The issue class name.

      'title' -- The issue class title.

      'categories' -- The available enumerals for the "categories"
      field."""
    
    # Extract the form contents and validate them.
    errors = {}
    class_name = string.strip(request["name"])
    if not qm.label.is_valid(class_name):
        errors["name"] = qm.error("invalid class name", class_name=class_name)
    class_title = string.strip(request["title"])
    if class_title == "":
        errors["title"] = qm.error("missing class title")
    categories = qm.web.decode_set_control_contents(request["categories"])

    # Were there any validation errors?
    if len(errors) > 0:
        # Yes.  Redisplay the form, listing the errors.
        return AddClassPage(errors)(request)
    
    # Construct the issue class.
    issue_class = qm.track.issue_class.IssueClass(name=class_name,
                                                  title=class_title,
                                                  categories=categories)
    # Add it to the IDB.
    idb = request.GetSession().idb 
    idb.AddIssueClass(issue_class)
    # If this is the first issue class, make it the default issue class.
    if len(idb.GetIssueClasses()) == 1:
        idb.GetConfiguration()["default_class"] = class_name
    # Redirect to the IDB configuration page.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("config-idb", base=request)


def handle_show_notification(request):
    """Handle an 'show-notification' request.

    This request shows a form for configuring a notification trigger."""

    issue_class = _get_issue_class_for_session(request)
    notification_trigger = issue_class.GetTrigger("notification")
    return NotificationPage(trigger=notification_trigger)(request)


def handle_submit_notification(request):
    """Handle submission of a change to the notification trigger.

    These fields are used in the request:

      'recipient_addresses' -- A list of email addresses of recipients.

      'recipient_uids' -- A list of user IDs of recipients.

      'notification_condition' -- A Python expression on an issue
      indicating when notification is sent.
    """

    # Extract parameters from the request.
    recipient_addresses = qm.web.decode_set_control_contents(
        request["recipient_addresses"])
    recipient_uids = qm.web.decode_set_control_contents(
        request["recipient_uids"])
    condition = request["notification_condition"]
    # Construct the trigger.
    from qm.track.triggers.notification import NotifyFixedTrigger
    trigger = NotifyFixedTrigger("notification",
                                 condition,
                                 recipient_addresses,
                                 recipient_uids)
    # Insert it.
    issue_class = _get_issue_class_for_session(request)
    issue_class.RegisterTrigger(trigger)
    # Redirect to the page displaying the issue class.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-issue-class", base=request)


def handle_show_subscription(request):
    """Handle a 'show-subscription' request.

    This request shows a form for configuring a subscription field and
    trigger."""

    issue_class = _get_issue_class_for_session(request)
    try:
        field = issue_class.GetField("subscribers")
    except KeyError:
        field = None
    page = web.DtmlPage("subscription.dtml",
                        field=field,
                        trigger=issue_class.GetTrigger("subscription"))
    return page(request)
    

def handle_submit_subscription(request):
    """Handle submission of a change to the subscription trigger.

    These fields are used in the request:

      'notification_condition' -- The condition under which notification
      messages are sent.

      'subscription_condition' -- The condition under which users are
      subscribed automatically.

      'hide_subscription' -- Whether to hide the subscription list.
    """

    issue_class = _get_issue_class_for_session(request)

    # Extract parameters from the request.
    notification_condition = request["notification_condition"]
    subscription_condition = request["subscription_condition"]
    if request.get("hide_subscription") == "true":
        hide_subscription = "true"
    else:
        hide_subscription = "false"
    # Construct the field, if it doesn't exist.
    if not issue_class.HasField("subscribers"):
        subscribers_field = qm.fields.SetField(qm.fields.UidField(
            name="subscribers",
            title="Subscribers",
            description=
"""User IDs of users subscribed to receive automatic notification of
changes to this issue."""))
        issue_class.AddField(subscribers_field)
    else:
        subscribers_field = issue_class.GetField("subscribers")
    # Set the "hidden" attribute appropriately.
    subscribers_field.SetProperty("hidden", hide_subscription)
    # Construct the trigger.
    from qm.track.triggers.notification import NotifyByUidFieldTrigger
    trigger = NotifyByUidFieldTrigger("subscription",
                                      notification_condition,
                                      "subscribers")
    trigger.SetSubscriptionCondition(subscription_condition)
    # Insert it.
    issue_class = _get_issue_class_for_session(request)
    issue_class.RegisterTrigger(trigger)
    # Redirect to the page displaying the issue class.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-issue-class", base=request)


def handle_add_discussion(request):
    """Handle a 'add-discussion' request.

    This request adds a discussion field to the issue class being modified.""" 
    issue_class = _get_issue_class_for_session(request)
    # Construct the field, if it doesn't exist.
    if not issue_class.HasField("discussion"):
        text_field = qm.fields.TextField(
            name="discussion",
            title="Discussion",
            description="Follow-up discussion of this issue.",
            structured="true")
        discussion_field = qm.track.issue_class.DiscussionField(text_field)
        issue_class.AddField(discussion_field)
    else:
        discussion_field = issue_class.GetField("discussion")
    # Construct the trigger.
    from qm.track.triggers.discussion import DiscussionTrigger
    trigger = DiscussionTrigger("discussion", discussion_field.GetName())
    # Insert it.
    issue_class = _get_issue_class_for_session(request)
    issue_class.RegisterTrigger(trigger)
    # Redirect to the page displaying the issue class.
    raise qm.web.HttpRedirect, \
          qm.web.WebRequest("show-issue-class", base=request)


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

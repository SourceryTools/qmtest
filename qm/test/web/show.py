########################################################################
#
# File:   show.py
# Author: Alex Samuel
# Date:   2001-04-09
#
# Contents:
#   Web forms to display and edit a test.
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

"""Web forms for creating, displaying, and editing tests and resources.

Many functions in this file work for both tests and resources, referred
to generally as "items".  Where we need to distinguish between them, we
use a type string that is either "test" or "resource".

Creating a new test or resource is a two-step process.  For a test, the
user is first presented with a form for selecting the test class and
entering the new test's ID; this is generated by 'handle_new_test' in
response to the 'new-test' request.  Once these have been specified, the
user is presented with the usual test editing form, generated by
'handle_show' in response to the 'create-test' request.  The test is not
created until the user submits the second form.  The procedure for new
resources is analogous."""

########################################################################
# imports
########################################################################

import qm.label
import qm.structured_text
import qm.test.base
import qm.web
import string
import sys
import web

########################################################################
# classes
########################################################################

class ShowPage(web.DtmlPage):
    """DTML page for showing and editing tests and resources.

    See 'handle_show' for more information."""

    def __init__(self, item, edit, new, type, field_errors={}):
        """Construct a new DTML context.
        
        These parameters are also available in DTML under the same name:

        'item' -- The 'Test' or 'Resource' instance.

        'edit' -- True for editing the item; false for displaying it
        only.

        'new' -- True for editing a newly-created item ('edit' is then
        also true).

        'type' -- Either "test" or "resource".

        'field_errors' -- A map from field names to corresponding error
        messages.  The values "_prerequisites", "_resources", and
        "_categories" may also be used as keys."""

        # Initialize the base class.
        web.DtmlPage.__init__(self, "show.dtml")
        # Set up attributes.
        self.item = item
        self.fields = item.GetClass().fields
        self.edit = edit
        self.new = new
        assert type in ["test", "resource"]
        self.type = type
        self.field_errors = field_errors

        # Some extra attributes that don't apply to resources.
        if self.type is "test":
            self.prerequisites = item.GetPrerequisites()
            self.resources = item.GetResources()
            self.categories = item.GetCategories()


    def GetTitle(self):
        """Return the page title for this page."""

        # Map the scriptname to a nicely-formatted title.
        url = self.request.GetScriptName()
        title = {
            "show-test":       "Show Test",
            "edit-test":       "Edit Test",
            "create-test":     "New Test",
            "show-resource":   "Show Resource",
            "edit-resource":   "Edit Resource",
            "create-resource": "New Resource",
            }[url]
        # Show the item's ID too.
        title = title + " " + self.item.GetId()
        return title


    def FormatFieldValue(self, field):
        """Return an HTML rendering of the value for 'field'."""

        # Extract the field value.
        arguments = self.item.GetArguments()
        field_name = field.GetName()
        try:
            value = arguments[field_name]
        except KeyError:
            # Use the default value if none is provided.
            value = field.GetDefaultValue()
        # Format it appropriately.
        if self.edit:
            if field.IsProperty("hidden"):
                return field.FormatValueAsHtml(value, "hidden")
            elif field.IsProperty("read_only"):
                # For read-only fields, we still need a form input, but
                # the user shouldn't be able to change anything.  Use a
                # hidden input, and display the contents as if this
                # wasn't an editing form.
                return field.FormatValueAsHtml(value, "hidden") \
                       + field.FormatValueAsHtml(value, "full")
            else:
                return field.FormatValueAsHtml(value, "edit")
        else:
            return field.FormatValueAsHtml(value, "full")


    def GetClassDescription(self):
        """Return a full description of the test or resource class.

        returns -- The description, formatted as HTML."""

        # Extract the class's doc string.
        doc_string = self.item.GetClass().__doc__
        if doc_string is not None:
            return qm.web.format_structured_text(doc_string)
        else:
            return "&nbsp;"


    def GetBriefClassDescription(self):
        """Return a brief description of the test or resource class.

        returns -- The brief description, formatted as HTML."""

        # Extract the class's doc string.
        doc_string = self.item.GetClass().__doc__
        if doc_string is not None:
            doc_string = qm.structured_text.get_first(doc_string)
            return qm.web.format_structured_text(doc_string)
        else:
            return "&nbsp;"


    def MakeShowUrl(self):
        """Return the URL for showing this item."""

        return qm.web.WebRequest("show-" + self.type,
                                 base=self.request,
                                 id=self.item.GetId()) \
               .AsUrl()


    def MakeSubmitUrl(self):
        """Return the URL for submitting edits."""

        return self.request.copy("submit-" + self.type).AsUrl()


    def MakePrerequisitesControl(self):
        """Make controls for editing test prerequisites."""

        # Encode the current prerequisites.  The first element of each
        # option is user-visible; the second is the option value which
        # we can parse back later.
        options = []
        for test_id, outcome in self.prerequisites.items():
            options.append(("%s (%s)" % (test_id, outcome),
                            "%s;%s" % (test_id, outcome)))
        # Generate the page for selecting the prerequisite test to add.
        test_path = qm.label.dirname(self.item.GetId())
        add_page = AddPrerequisitePage(test_path)(self.request)
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="prerequisites",
                                       select_name="_set_prerequisites",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=480)


    def MakeResourcesControl(self):
        """Make controls for editing the resources associated with a test."""

        # Encode the current resource values.
        options = map(lambda ac: (ac, ac), self.resources)
        # Generate the page for selecting the resource to add.
        test_path = qm.label.dirname(self.item.GetId())
        add_page = AddResourcePage(test_path)(self.request)
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="resources",
                                       select_name="_set_resources",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=360)


    def MakeCategoriesControl(self):
        """Make controls for editing a test's categories."""

        # Encode the current categories.
        options = map(lambda cat: (cat, cat), self.categories)
        # Generate the page for selecting the category to add.
        add_page = web.DtmlPage("add-category.dtml")
        add_page = add_page(self.request) 
        # Generate the controls.
        return qm.web.make_set_control(form_name="form",
                                       field_name="categories",
                                       select_name="_set_categories",
                                       add_page=add_page,
                                       initial_elements=options,
                                       rows=4,
                                       window_height=240)


    def MakeDeleteScript(self):
        """Make a script to confirm deletion of the test or resource.

        returns -- JavaScript source for a function, 'delete_script',
        which shows a popup confirmation window."""

        item_id = self.item.GetId()
        delete_url = qm.web.make_url("delete-" + self.type,
                                     base_request=self.request,
                                     id=item_id)
        message = """
        <p>Are you sure you want to delete the %s %s?</p>
        """ % (self.type, item_id)
        return qm.web.make_confirmation_dialog(message, delete_url)




class AddPrerequisitePage(web.DtmlPage):
    """Page for specifying a prerequisite test to add."""

    outcomes = qm.test.base.Result.outcomes
    """The list of possible test outcomes."""


    def __init__(self, base_path):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "add-prerequisite.dtml")
        # Extract a list of all test IDs in the specified path. 
        db = qm.test.base.get_database()
        test_ids = db.GetTestIds(base_path)
        test_ids.sort()
        # Store it for the DTML code.
        self.test_ids = test_ids



class AddResourcePage(web.DtmlPage):
    """Page for specifying an resource to add."""

    def __init__(self, resource_path):
        # Initialize the base class.
        web.DtmlPage.__init__(self, "add-resource.dtml")
        # Extract a list of all resource IDs in the specified path.
        db = qm.test.base.get_database()
        resource_ids = db.GetResourceIds(resource_path)
        resource_ids.sort()
        # Store it for the DTML code.
        self.resource_ids = resource_ids
        


class NewItemPage(web.DtmlPage):
    """Page for creating a new test or resource."""

    def __init__(self,
                 type,
                 item_id="",
                 class_name="",
                 field_errors={}):
        """Create a new DTML context.

        'type' -- Either "test" or "resource".

        'item_id' -- The item ID to show.

        'class_name' -- The class name to show.

        'field_errors' -- A mapping of error messages for fields.  Keys
        may be "_id" or "_class"."""

        # Initialize the base class.
        web.DtmlPage.__init__(self, "new.dtml")
        # Set up attributes.
        assert type in ["test", "resource"]
        self.type = type
        self.item_id = item_id
        self.class_name = class_name
        if type == "test":
            self.class_names = qm.test.base.get_database().GetTestClasses()
        elif type == "resource":
            self.class_names = qm.test.base.standard_resource_class_names
        self.field_errors = field_errors


    def GetTitle(self):
        """Return the title this page."""

        return "Create a New %s" % string.capwords(self.type)


    def MakeSubmitUrl(self):
        """Return the URL for submitting the form.

        The URL is for the script 'create-test' or 'create-resource' as
        appropriate."""

        return qm.web.WebRequest("create-" + self.type,
                                 base=self.request) \
               .AsUrl()



########################################################################
# functions
########################################################################

# No need to do anything besides generate the page.
handle_new_test = NewItemPage(type="test")


# No need to do anything besides generate the page.
handle_new_resource = NewItemPage(type="resource")


def handle_show(request):
    """Generate the show test page.

    'request' -- A 'WebRequest' object.

    This function generates pages to handle these requests:

      'create-test' -- Generate a form for initial editing of a test
      about to be created, given its test ID and test class.

      'create-resource' -- Likewise for an resource.

      'show-test' -- Display a test.

      'show-resource' -- Likewise for an resource.

      'edit-test' -- Generate a form for editing an existing test.

      'edit-resource' -- Likewise for an resource.

    This function distinguishes among these cases by checking the script
    name of the request object.

    The request must have the following fields:

      'id' -- A test or resource ID.  For show or edit pages, the ID of an
      existing item.  For create pages, the ID of the item being
      created.

      'class' -- For create pages, the name of the test or resource
      class.

    """

    # Paramaterize this function based on the request's script name.
    url = request.GetScriptName()
    edit, create, type = {
        "show-test":       (0, 0, "test"),
        "edit-test":       (1, 0, "test"),
        "create-test":     (1, 1, "test"),
        "show-resource":   (0, 0, "resource"),
        "edit-resource":   (1, 0, "resource"),
        "create-resource": (1, 1, "resource"),
        }[url]

    database = qm.test.base.get_database()

    try:
        # Determine the ID of the item.
        item_id = request["id"]
    except KeyError:
        # The user probably submitted the form without entering an ID.
        message = qm.error("no id for show")
        return qm.web.generate_error_page(request, message)

    if create:
        # We're in the middle of creating a new item.  
        class_name = request["class"]

        # First perform some validation.
        field_errors = {}
        # Check that the ID is valid.
        try:
            qm.test.base.validate_id(item_id)
        except RuntimeError, diagnostic:
            field_errors["_id"] = diagnostic
        else:
            # Check that the ID doesn't already exist.
            if type is "resource":
                if database.HasResource(item_id):
                    field_errors["_id"] = qm.error("resource already exists",
                                                   resource_id=item_id)
            elif type is "test":
                if database.HasTest(item_id):
                    field_errors["_id"] = qm.error("test already exists",
                                                   test_id=item_id)
        # Check that the class exists.
        try:
            qm.test.base.get_class(class_name)
        except ValueError:
            # The class name was incorrectly specified.
            field_errors["_class"] = qm.error("invalid class name",
                                              class_name=class_name)
        except ImportError:
            # Can't find the class.
            field_errors["_class"] = qm.error("class not found",
                                              class_name=class_name)
        # Were there any errors?
        if len(field_errors) > 0:
            # Yes.  Instead of showing the edit page, re-show the new
            # item page.
            page = NewItemPage(type=type,
                               item_id=item_id,
                               class_name=class_name,
                               field_errors=field_errors)
            return page(request)
            
        # Construct an test with default argument values, as the
        # starting point for editing.
        if type is "resource":
            item = qm.test.base.make_new_resource(class_name, item_id)
        elif type is "test":
            item = qm.test.base.make_new_test(class_name, item_id)
    else:
        # We're showing or editing an existing item.
        # Look it up in the database.
        if type is "resource":
            try:
                item = database.GetResource(item_id)
            except qm.test.base.NoSuchTestError:
                # An test with the specified test ID was not fount.
                # Show a page indicating the error.
                message = qm.error("no such test", test_id=item_id)
                return qm.web.generate_error_page(request, message)
        elif type is "test":
            try:
                item = database.GetTest(item_id)
            except qm.test.base.NoSuchResourceError:
                # An test with the specified resource ID was not fount.
                # Show a page indicating the error.
                message = qm.error("no such resource", resource_id=item_id)
                return qm.web.generate_error_page(request, message)

    # Generate HTML.
    return ShowPage(item, edit, create, type)(request)


def _retrieve_attachment_data(database, item_id, attachment):
    """Retrieve temporary attachment data and store it in the right place.

    Loads attachment data for 'attachment' stored in the temporary
    attachment store and stores it in its permanent location in the test
    database.

    'database' -- The test database.

    'item_id' -- The ID of the test or resource associated with this
    attachment.

    'attachment' -- An 'Attachment' instance.

    returns -- An 'Attachment' instance (may be the same as
    'attachment', or not) to use for the attachment."""

    if attachment is None:
        return None

    location = attachment.GetLocation()
    if qm.attachment.is_temporary_location(location):
        # The attachment data is in the temporary store.  We need to
        # extract it and store it in the test database's permanent
        # attachment store.  Cause the temporary store to release
        # control of the file containing the attachment data.
        data_file_path = qm.attachment.temporary_store.Release(location)
        # Adopt it into the permanent attachment store.
        attachment_store = database.GetAttachmentStore()
        return attachment_store.Adopt(
            item_id=item_id,
            mime_type=attachment.GetMimeType(),
            description=attachment.GetDescription(),
            file_name=attachment.GetFileName(),
            path=data_file_path)
    else:
        return attachment


def handle_submit(request):
    """Handle a test or resource submission.

    This function handles submission of the test or resource editing form
    generated by 'handle_show'.  The script name in 'request' should be
    'submit-test' or 'submit-resource'.  It constructs the appropriate
    'Test' or 'Resource' object and writes it to the database, either as a
    new item or overwriting an existing item.

    The request must have the following form fields:

    'id' -- The test or resource ID of the item being edited or created.

    'class' -- The name of the test or resource class of this item.

    arguments -- Argument values are encoded in fields whose names start
    with 'qm.fields.Field.form_field_prefix'.

    'prerequisites' -- For tests, a set-encoded collection of
    prerequisites.  Each prerequisite is of the format
    'test_id;outcome'.

    'resources' -- For tests, a set-encoded collection of resource IDs.

    'categories' -- For tests, a set-encoded collection of categories."""

    if request.GetScriptName() == "submit-test":
        type = "test"
    elif request.GetScriptName() == "submit-resource":
        type = "resource"

    # Make sure there's an ID in the request, and extract it.
    try:
        item_id = request["id"]
    except KeyError:
        message = qm.error("no id for submit")
        return qm.web.generate_error_page(request, message)
    
    database = qm.test.base.get_database()
    # Extract the class and field specification.
    item_class_name = request["class"]
    item_class = qm.test.base.get_class(item_class_name)
    fields = item_class.fields

    # We'll perform various kinds of validation as we extract form
    # fields.  Errors are placed into this map; later, if it's empty, we
    # know there were no validation errors.
    field_errors = {}

    # Loop over fields of the class, looking for arguments in the
    # submitted request.
    arguments = {}
    field_prefix = qm.fields.Field.form_field_prefix
    for field in fields:
        # Construct the name we expect for the corresponding argument.
        field_name = field.GetName()
        form_field_name = field_prefix + field_name
        try:
            # Try to get the argument value.
            value = request[form_field_name]
        except KeyError:
            # The value for this field is missing.
            message = qm.error("missing argument",
                               title=field.GetTitle())
            return qm.web.generate_error_page(request, message)
        # Parse the value for this field.
        try:
            value = field.ParseFormValue(value)
        except:
            # Something went wrong parsing the value.  Associate an
            # error message with this field.
            message = str(sys.exc_info()[1])
            field_errors[field_name] = message
        else:
            # All is well with this field.

            # If the field is an attachment field, or a set of
            # attachments field, we have to process the values.  The
            # data for each attachment is stored in the temporary
            # attachment store; we need to copy it from there into the
            # test database.  This function does the work.
            fn = lambda attachment, database=database, item_id=item_id: \
                 _retrieve_attachment_data(database, item_id, attachment)
            if isinstance(field, qm.fields.AttachmentField):
                # An attachment field -- process the value.
                value = fn(value)
            elif isinstance(field, qm.fields.SetField) \
                 and isinstance(field.GetContainedField(),
                                qm.fields.AttachmentField):
                # An attachment set field -- process each element of the
                # value.
                value = map(fn, value)

            # Store the field value.
            arguments[field_name] = value

    properties = qm.web.decode_properties(request["properties"])

    if type is "test":
        # Extract prerequisite tests.  
        preqs = request["prerequisites"]
        preqs = qm.web.decode_set_control_contents(preqs)
        # Prerequisite tests are encoded as 'test_id:outcome'.  Unencode
        # them and build a map from test ID to expected outcome.
        prerequisites = {}
        for preq in preqs:
            # Unencode.
            test_id, outcome = string.split(preq, ";", 1)
            # Make sure this outcome is one we know about.
            if not outcome in qm.test.base.Result.outcomes:
                raise RuntimeError, "invalid outcome"
            # Store it.
            prerequisites[test_id] = outcome

        # Extract resources.
        resources = request["resources"]
        resources = qm.web.decode_set_control_contents(resources)

        # Extract categories.
        categories = request["categories"]
        categories = qm.web.decode_set_control_contents(categories)

        # Create a new test.
        item = qm.test.base.Test(test_id=item_id,
                                 test_class_name=item_class_name,
                                 arguments=arguments,
                                 prerequisites=prerequisites,
                                 categories=categories,
                                 resources=resources,
                                 properties=properties)

    elif type is "resource":
        # Create a new resource.
        item = qm.test.base.Resource(resource_id=item_id,
                                     resource_class_name=item_class_name,
                                     arguments=arguments,
                                     properties=properties)

    # Were there any validation errors?
    if len(field_errors) > 0:
        # Yes.  Instead of processing the submission, redisplay the form
        # with error messages.
        request = request.copy(url="edit-" + type)
        return ShowPage(item, 1, 0, type, field_errors)(request)

    # Store it in the database.
    if type is "test":
        database.WriteTest(item)
    elif type is "resource":
        database.WriteResource(item)

    # Redirect to a page that displays the newly-edited item.
    request = qm.web.WebRequest("show-" + type, base=request, id=item_id)
    raise qm.web.HttpRedirect, request


def handle_delete(request):
    """Handle delete requests.

    This function handles the script requests 'delete-test' and
    'delete-resource'.

    'request' -- A 'WebRequest' object.

    The ID of the test or resource to delete is specified in the 'id'
    field of the request."""

    database = qm.test.base.get_database()
    # Extract the item ID.
    item_id = request["id"]
    # The script name determines whether we're deleting a test or an
    # resource. 
    script_name = request.GetScriptName()
    if script_name == "delete-test":
        database.RemoveTest(item_id)
    elif script_name == "delete-resource":
        database.RemoveResource(item_id)
    else:
        raise RuntimeError, "unrecognized script name"
    # Redirect to the main page.
    request = qm.web.WebRequest("dir", base=request)
    raise qm.web.HttpRedirect, request


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

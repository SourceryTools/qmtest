##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Form interfaces

$Id: interfaces.py 69417 2006-08-12 10:33:10Z philikon $
"""
import re
from zope import interface, schema
from zope.publisher.interfaces.browser import IBrowserPage

##############################################################################
# BBB 2006/04/19 -- to be removed after 12 months

import zope.deferredimport
zope.deferredimport.deprecated(
    "It has moved to zope.publisher.interfaces.browser.IBrowserPage.  "
    "This reference will be gone in Zope 3.5.",
    IPage = 'zope.publisher.interfaces.browser:IBrowserPage',
    )

##############################################################################

class FormError(Exception):
    """There was an error in managing the form
    """

def reConstraint(pat, explanation):
    pat = re.compile(pat)

    def constraint(value):
        if prefix_re.match(value):
            return True
        raise interface.Invalid(value, explanation)

class ISubPage(interface.Interface):
    """A component that computes part of a page
    """

    def update():
        """Update content ot view information based on user input
        """

    def render():
        """Render the sub page, returning a unicode string
        """

    prefix = schema.ASCII(
        constraint=reConstraint(
            '[a-zA-Z][a-zA-Z0-9_]*([.][a-zA-Z][a-zA-Z0-9_]*)*',
            "Must be a sequence of not-separated identifiers"),
        description=u"""Page-element prefix

        All named or identified page elements in a subpage should have
        names and identifiers that begin with a subpage prefix
        followed by a dot.
        """,
        readonly=True,
        )

    def setPrefix(prefix):
        """Update the subpage prefix
        """


class IFormAPI(interface.Interface):
    """API to facilitate creating forms, provided by zope.formlib.form
    """

    def Field(schema_field, **options):
        """Define a form field from a schema field and usage options


        The following options are supported:

        name
          Provide a name to use for the field.

        prefix
          The form-field prefix.

        for_display
          A flag indicating whether the form-field is to be used
          for display. See IFormField.

        for_input
          A flag indicating whether the form-field is to be used
          for input. See IFormField.

        custom_widget
           Factory to use for widget construction. See IFormField.

        render_context
           A flag indicating whether the default value to render
           should come from the form context. See IFormField.

        get_rendered
           A callable or form method name to be used to get a default
           rendered value.  See IFormField.

        """


    def Fields(*arguments, **options):
        """Create form-fields collection (IFormFields)

        Creates a form-field collection from a collection of:

        - Schemas

        - Schema fields

        - form fields (IFormField)

        - form-field collections (IFormFields)

        An IFormFields is returned.

        The following options are supported:

        name
          Provide a name to use for the field.

        prefix
          The form-field prefix for new form-fields created.
          When form-field collections are passed, their contents keep
          their existing prefixes are retained.

        for_display
          A flag indicating whether the form-fiellds are to be used
          for display.  This value is used for for_display attributes
          of all created form fields.  This option does not effect
          input from form-field collections.

        for_input
          A flag indicating whether the form-fiellds are to be used
          for input.  This value is used for for_input attributes
          of all created form fields.  This option does not effect
          input from form-field collections.

        render_context
           A flag indicating whether the default values to render
           should come from the form context. See IFormField.

        """

    def setUpInputWidgets(form_fields, form_prefix, context, request,
                          ignore_request=False):
        """Set up widgets for input

        An IWidgets is returned based on the give form fields.

        All of the resulting widgets will be input widgets, regardless
        of whether the form fields are for display or whether the
        underlying schema fields are read only.  This is so that one
        can easily build an input form, such as an add form from an
        existing schema.

        The widgets will have prefixes that combine the given form
        prefix and any form-field prefixes.

        A context argument is provided to allow field binding.

        If ignore_request passed a true value, then the widgets will
        not initialize their values from the request.
        """

    def setUpEditWidgets(form_fields, form_prefix, context, request,
                         adapters=None, for_display=False,
                         ignore_request=False):
        """Set up widgets for editing or displaying content

        An IWidgets is returned based on the give form fields.

        The resulting widgets will be input widgets unless:

        - the corresponding form field was defined with the
          for_display option,

        - the underlying field is read only, or

        - the for_display opetion to setUpEditWidgets was passed a
          true value.

        The widgets fields are bound to the context after it is
        adapted to the field schema.  A mapping object can be passed
        to setUpEditWidgets to capture the adapters created. The
        adapters are placed in the mapping using both interfaces and
        interface names as keys.

        If the ignore_request option is passed a true value, then
        widget's rendered data will be set from the context, and user
        inputs will be ignored.
        """

    def setUpDataWidgets(form_fields, form_prefix, context, request, data=(),
                         for_display=False, ignore_request=False):
        """Set up widgets for input or display

        An IWidgets is returned based on the give form fields.

        The resulting widgets will be input widgets unless:

        - the corresponding form field was defined with the
          for_display option,

        - the underlying field is read only, or

        - the for_display opetion to setUpEditWidgets was passed a
          true value.

        A data mapping argument can be passed to provide initial
        data.

        If the ignore_request option is passed a true value, then
        widget's rendered data will be set from the passed data or
        from field defaults, and user inputs will be ignored.

        """

    def getWidgetsData(widgets, form_prefix, data):
        """Get input data and input errors

        A sequence of input errors are returned.  Any data available
        are added to the data argument, which must be a mapping
        argument.  The keys in the output mapping are
        widget/form-field names without the form prefix.

        """

    def checkInvariants(form_fields, form_data):
        """Check schema invariants for input data

        For each schema that was used to define the form fields and
        that had invariants relevent to the fields, the invariants are
        checked. Invariants that refer to fields not included in the
        form fields are ignored.

        A list of errors is returned.
        """

    def applyChanges(context, form_fields, data, adapters=None):
        """Apply form data to an object

        For each form field that has data, the data are applied to the
        context argument.  The context is adapter to the schema for
        each field.  If an adapters mapping is passed, it will be used
        as a cache.  Typically, it would be a mapping object populated
        when setUpEditWidgets was called.

        """

    def Action(label, **options):
        """Define a submit action

        options:

        condition
          A callable or  name of a method to  call to test whether
          the  action is  applicable.  if  the value  is  a method
          name,  then the method  will be  passed the  action when
          called, otherwise, the callables will be passed the form
          and the action.

        validator
          A callable or name of a method to call to validate and
          collect inputs.  This is called only if the action was
          submitted and if the action either has no condition, or the
          condition evaluates to a true value.  If the validator is
          provided as a method name, the method will be called the
          action and a dictionary in which to save data.  If the
          validator is provided as a callable, the callable will be
          called the form, the action, and a dictionary in which to
          save data.  The validator normally returns a (usually empty)
          list of widget input errors.  It may also return None to behave
          as if the action wasn't submitted.

        success
          A handler, called when the the action was submitted and
          there are no validation errors.  The handler may be provided
          as either a callable or a method name.  If the handler is
          provided as a method name, the method will be called the
          action and a dictionary containing the form data.  If the
          success handler is provided as a callable, the callable will
          be called the form, the action, and a dictionary containing
          the data.  The handler may return a form result (e.g. page),
          or may return None to indicate that the form should generate
          it's own output.

        failure
          A handler, called when the the action was submitted and
          there are validation errors.  The handler may be provided as
          either a callable or a method name.  If the handler is
          provided as a method name, the method will be called the
          action, a dictionary containing the form data, and a list of
          errors.  If the failure handler is provided as a callable,
          the callable will be called the form, the action, a
          dictionary containing the data, and a list of errors.  The
          handler may return a form result (e.g. page), or may return
          None to indicate that the form should generate it's own
          output.

        prefix
          A form prefix for the action.  When generating submit
          actions, the prefix should be combined with the action
          name, separating the two with a dot. The default prefix
          is "actions"form.

        name
          The action name, without a prefix.  If the label is a
          valid Python identifier, then the lowe-case label will
          be used, otherwise, a hex encoding of the label will be
          used.  If for some strange reason the labels in a set of
          actions with the same prefix is not unique, a name will
          have to be given for some actions to get unique names.

        css_class
          The CSS class for the action.  The class defaults to
          "action"form.

        data
          A bag of extra information that can be used by handlers,
          validators, or conditions.

        """

    def action(label, **options):
        """Create an action factory

        This function creates a factory for creating an action from a
        function, using the function as the action success handler.
        The options are the same as for the Action constructor except
        that the options don't include the success option.

        The function is designed to be used as a decorator (Python 2.4
        and later), as in:

        @action("Edit")
        def handle_edit(self, action, data):
            ...


        """

    def validate(form, actions, form_prefix, data, default_validate=None):
        """Process a submitted action, if any

        Check each of the given actions to see if any were submitted.

        If an action was submitted, then validate the input.  The input
        is called by calling the action's validator, ir it has one, or
        by calling the default_validate passed in.

        If the input is validated successfully, and the action has one
        success handler, then the success handler is called.

        If the input was validated and there were errors, then the
        action's failure handler will be called, if it has one.

        If an action was submitted, then the function returns the
        result of validation and the action.  The result of validation
        is normally a boolean, but may be None if no validator was
        provided.

        If no action was submitted, then None is returned for both the
        result of validation and the action.

        """

    FormBase = interface.Attribute("""Base class for creating forms

    The FormBase class provides reuasable implementation for creating
    forms.  It implements ISubPage, IBrowserPage, and IFormBaseCustomization.
    Subclasses will override or use attributes defined by
    IFormBaseCustomization.
    """)

class IFormBaseCustomization(ISubPage, IBrowserPage):
    """Attributes provided by the Form base class

    These attributes may be used or overridden.

    Note that the update and render methods are designed to to work
    together.  If you override one, you probably need to override the
    other, unless you use original versions in your override.

    """

    label = interface.Attribute("A label to display at the top of a form")

    status = interface.Attribute(
        """An update status message

        This is normally generated by success or failure handlers.
        """)

    errors = interface.Attribute(
        """Sequence of errors encountered during validation
        """)

    form_result = interface.Attribute(
        """Return from action result method
        """)

    form_reset = interface.Attribute(
        """Boolean indicating whether the form needs to be reset
        """)

    form_fields = interface.Attribute(
        """The form's form field definitions

        This attribute is used by many of the default methods.
        """)

    widgets = interface.Attribute(
        """The form's widgets

        - set by setUpWidgets

        - used by validate
        """)

    def setUpWidgets(ignore_request=False):
        """Set up the form's widgets.

        The default implementation uses the form definitions in the
        form_fields attribute and setUpInputWidgets.

        The function should set the widgets attribute.
        """

    def validate(action, data):
        """The default form validator

        If an action is submitted and the action doesn't have it's own
        validator then this function will be called.
        """

    template = interface.Attribute(
        """Template used to display the form

        This can be overridden in 2 ways:

        1. You can override the attribute in a subclass

        2. You can register an alternate named template, named
           "default" for your form.

        """)

    def resetForm():
        """Reset any cached data because underlying content may have changed
        """

    def error_views():
        """Return views of any errors.

        The errors are returned as an iterable.
        """



class IFormFields(interface.Interface):
    """A colection of form fields (IFormField objects)
    """

    def __len__():
        """Get the number of fields
        """

    def __iter__():
        """Iterate over the form fields
        """

    def __getitem__(name):
        """Return the form field with the given name

        If the desired firld has a prefix, then the given name should
        be the prefix, a dot, and the unprefixed name.  Otherwise, the
        given name is just the field name.

        Raise a KeyError if a field can't be found for the given name.
        """

    def get(name, default=None):
        """Return the form field with the given name

        If the desired firld has a prefix, then the given name should
        be the prefix, a dot, and the unprefixed name.  Otherwise, the
        given name is just the field name.

        Return the default if a field can't be found for the given name.
        """

    def __add__(form_fields):
        """Add two form fields collections (IFormFields)

        Return a new IFormFields that is the concatination of the two
        IFormFields.
        """

    def select(*names):
        """Select fields with given names in order

        Return a new IFormFields that is a selection from the original
        IFormFields that has the named fields in the specified order.
        """

    def omit(*names):
        """Omit fields with given names
        """

SKIP_UNAUTHORIZED = 2
DISPLAY_UNWRITEABLE = 4

class IFormField(interface.Interface):
    """Definition of a field to be included in a form

    This should not be confused with a schema field.
    """

    __name__ = schema.ASCII(
        constraint=reConstraint('[a-zA-Z][a-zA-Z0-9_]*',
                                "Must be an identifier"),
        title = u"Field name",
        description=u"""\
        This is the name, without any proefix, used for the field.
        It is usually the same as the name of the for field's schem field.
        """
        )

    field = interface.Attribute(
        """Schema field that defines the data of the form field
        """
        )

    prefix = schema.ASCII(
        constraint=reConstraint('[a-zA-Z][a-zA-Z0-9_]*',
                                "Must be an identifier"),
        title=u"Prefix",
        description=u"""\
        Form-field prefix.  The form-field prefix is used to
        disambiguate fields with the same name (e.g. from different
        schema) within a collection of form fields.
        """,
        default="",
        )

    for_display = schema.Bool(
        title=u"Is the form field for display only?",
        description=u"""\
        If this attribute has a true value, then a display widget will be
        used for the field even if it is writable.
        """
        )

    for_input = schema.Bool(
        title=u"Is the form field for input?",
        description=u"""\
        If this attribute has a true value, then an input widget will be
        used for the field even if it is readonly.
        """
        )

    custom_widget = interface.Attribute(
        """Factory to use for widget construction.

        If not set, normal view lookup will be used.
        """
        )

    render_context = schema.Choice(
        title=u"Should the rendered value come from the form context?",
        description=u"""\

        If this attribute has a true value, and there is no other
        source of rendered data, then use data from the form context
        to set the rendered value for the widget.  This attribute is
        ignored if:

        - There is user input and user input is not being ignored, or

        - Data for the value is passed to setUpWidgets.

        If the value is true, then it is evaluated as a collection of bit
        flags with the flags:

        DISPLAY_UNWRITEABLE
            If the field isn't writable, then use a display widget

            TODO untested


        SKIP_UNAUTHORIZED
            If the user is not priviledges to perfoem the requested
            operation, then omit a widget.

            TODO unimplemented

        """,
        vocabulary=schema.vocabulary.SimpleVocabulary.fromValues((
            False, True,
            DISPLAY_UNWRITEABLE,
            SKIP_UNAUTHORIZED,
            DISPLAY_UNWRITEABLE | SKIP_UNAUTHORIZED,
            )),
        default=False,
        missing_value=False,
        )

    get_rendered = interface.Attribute(
        """Object to call to get a rendered value

        This attribute may be set to a callable object or to
        a form method name to call to get a value to be rendered in a
        widget.

        This attribute is ignored if:

        - There is user input and user input is not being ignored, or

        - Data for the value is passed to setUpWidgets.

        """
        )

class IWidgets(interface.Interface):
    """A widget collection

    IWidgets provide ordered collections of widgets that also support:

    - Name-based lookup

    - Keeping track of whether a widget is being used for input or
      display

    """

    def __iter__():
        """Return an interator in the widgets, in order
        """

    def __getitem__(name):
        """Get the widget with the given name

        Widgets are computed from form fields (IFormField).  If the
        form field used to create a widget has a prefix, then that
        should be reflected in the name passed.
        """

    def __iter_input_and_widget__():
        """Return an iterator of flag/widget pairs

        The flags indicate whether the corresponding widgets are used
        for input.  This is necessary because there is currently no
        way to introspect a widget to determine whether it is being
        used for input.
        """

    def __add__(widgets):
        """Add two widgets collections

        The result has the widgets in the first collection followed by
        the widgets in the second collection.

        Widgets should have different names in the two collections.
        The bahavior is undefined if the names overlap.

        """

class IForm(interface.Interface):
    """Base type for forms

    This exists primarily to provide something for which to register
    form-related conponents.

    """

class ISubPageForm(IForm, ISubPage):
    """A component that displays a part of a page.

    The rendered output must not have a form tag.  It is the
    responsibility of the surrounding page to supply a form tag.

    """

class IPageForm(IForm, IBrowserPage):
    """A component that displays a form as a page.
    """

class IAction(ISubPage):
    """Form submit actions
    """

    label = schema.TextLine(title=u"Action label")

    name = schema.TextLine(title=u"Action name")

    data = schema.Dict(title=u"Application data")

    condition = interface.Attribute(
        """Action condition

        This is a callable object that will be passed a form and an
        action and that returns a boolean to indicate whether the
        action is available.

        """)

    validator = interface.Attribute(
        """Action validator

        This is a callable object that will be passed a form and an
        action and that returns a (possibly empty) list of widget
        input errors.

        """)

    def available():
        """Return a boolean indicating whether the action is available
        """

    def submitted():
        """Return a boolean indicating whether the action was submitted
        """

    def validate(data):
        """Validate inputs

        If an action was submitted and has a custom validator, then
        the validator result is returned. Otherwise, None is returned.

        Validated inputs, if any, are placed into the mapping object
        passed as an argument,
        """

    def success(data):
        """Handle sucessful submition

        This method is called when the action was submitted and the
        submitted data was valid.
        """

    def failure(data, errors):
        """Handle unsucessful submition

        This method is called when the action was submitted and the
        submitted data was not valid.
        """

    def __get__(form, form_class=None):
        """Bind an action to a form

        Note that the other methods defined in this interface are
        valid only after the action has been bound to a form.
        """

class IActions(interface.Interface):
    """An action collection

    IActions provide ordered collections of actions that also support
    name-based lookup.

    """

    def __iter__():
        """Return an interator in the actions, in order
        """

    def __getitem__(name):
        """Get the action with the given name

        Actions are computed from form fields (IFormField).  If the
        form field used to create an action has a prefix, then that
        should be reflected in the name passed.
        """

    def __add__(actions):
        """Add two actions collections

        The result has the actions in the first collection followed by
        the actions in the second collection.

        Actions should have different names in the two collections.
        The bahavior is undefined if the names overlap.

        """

class IBoundAction(IAction):
    """An action that has been bound to a form
    """

    form = interface.Attribute("The form to which the action is bound")


class IAddFormCustomization(IFormBaseCustomization):
    """Form responsible for adding an object.
    """

    def create(data):
        """Create and return an object to be added to the context.

        The data argument is a dictionary with values supplied by the
        form.

        If any user errors occur, they should be collected into a list
        and raised as a `WidgetsError`.

        """

    def add(object):
        """Add an object to the context.  Returns the added object.
        """

    def createAndAdd(data):
        """Create and return an object that has been added to the context.

        The data argument is a dictionary with values supplied by the
        form.

        If any user errors occur, they should be collected into a list
        and raised as a `WidgetsError`.

        This is normally expected to simply call the create() and
        add() methods.

        """

    def nextURL():
        """Return the URL to be displayed after the add operation.

        This can be relative to the view's context.

        The default implementation returns `self.context.nextURL()`,
        i.e. it delegates to the `IAdding` view.

        """

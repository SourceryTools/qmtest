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
"""Forms

$Id: form.py 71638 2006-12-20 23:34:35Z jacobholm $
"""
import datetime
import re
import sys
import pytz

import zope.event
import zope.i18n
import zope.i18nmessageid
import zope.security
import zope.interface.interfaces
import zope.publisher.browser
import zope.publisher.interfaces.browser
from zope import component, interface, schema
from zope.interface.common import idatetime
from zope.interface.interface import InterfaceClass
from zope.schema.interfaces import IField
from zope.schema.interfaces import ValidationError
import zope.security
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent

import zope.app.container.interfaces
import zope.app.form.browser.interfaces
from zope.app.form.interfaces import IInputWidget, IDisplayWidget
from zope.app.form.interfaces import WidgetsError, MissingInputError
from zope.app.form.interfaces import InputErrors, WidgetInputError
from zope.app.pagetemplate import ViewPageTemplateFile

from zope.formlib import interfaces, namedtemplate
from zope.i18nmessageid import MessageFactory
_ = MessageFactory("zope")


interface.moduleProvides(interfaces.IFormAPI)

_identifier = re.compile('[A-Za-z][a-zA-Z0-9_]*$')

def expandPrefix(prefix):
    """Expand prefix string by adding a trailing period if needed.

    expandPrefix(p) should be used instead of p+'.' in most contexts.
    """
    if prefix and not prefix.endswith('.'):
        return prefix + '.'
    return prefix

class FormField:

    interface.implements(interfaces.IFormField)

    def __init__(self, field, name=None, prefix='',
                 for_display=None, for_input=None, custom_widget=None,
                 render_context=False, get_rendered=None, interface=None
                 ):
        self.field = field
        if name is None:
            name = field.__name__
        assert name
        self.__name__ = expandPrefix(prefix) + name
        self.prefix = prefix
        if interface is None:
            interface = field.interface
        self.interface = interface
        self.for_display = for_display
        self.for_input = for_input
        self.custom_widget = custom_widget
        self.render_context = render_context
        self.get_rendered = get_rendered

Field = FormField

def _initkw(keep_readonly=(), omit_readonly=False, **defaults):
    return keep_readonly, omit_readonly, defaults

class FormFields(object):

    interface.implements(interfaces.IFormFields)

    def __init__(self, *args, **kw):
        keep_readonly, omit_readonly, defaults = _initkw(**kw)

        fields = []
        for arg in args:
            if isinstance(arg, InterfaceClass):
                for name, field in schema.getFieldsInOrder(arg):
                    fields.append((name, field, arg))
            elif IField.providedBy(arg):
                name = arg.__name__
                if not name:
                        raise ValueError(
                            "Field has no name")

                fields.append((name, arg, arg.interface))
            elif isinstance(arg, FormFields):
                for form_field in arg:
                    fields.append(
                        (form_field.__name__, form_field, form_field.interface))
            elif isinstance(arg, FormField):
                fields.append((arg.__name__, arg, arg.interface))
            else:
                raise TypeError("Unrecognized argument type", arg)


        seq = []
        byname = {}
        for name, field, iface in fields:
            if isinstance(field, FormField):
                form_field = field
            else:
                if field.readonly:
                    if omit_readonly and (name not in keep_readonly):
                        continue
                form_field = FormField(field, interface=iface, **defaults)
                name = form_field.__name__

            if name in byname:
                raise ValueError("Duplicate name", name)
            seq.append(form_field)
            byname[name] = form_field

        self.__FormFields_seq__ = seq
        self.__FormFields_byname__ = byname

    def __len__(self):
        return len(self.__FormFields_seq__)

    def __iter__(self):
        return iter(self.__FormFields_seq__)

    def __getitem__(self, name):
        return self.__FormFields_byname__[name]

    def get(self, name, default=None):
        return self.__FormFields_byname__.get(name, default)

    def __add__(self, other):
        if not isinstance(other, FormFields):
            return NotImplemented
        return self.__class__(self, other)


    def select(self, *names):
        """Return a modified instance with an ordered subset of fields."""
        return self.__class__(*[self[name] for name in names])

    def omit(self, *names):
        """Return a modified instance omitting given fields."""
        return self.__class__(*[ff for ff in self if ff.__name__ not in names])

Fields = FormFields

def fields_initkw(keep_all_readonly=False, **other):
    return keep_all_readonly, other

# Backward compat
def fields(*args, **kw):
    keep_all_readonly, other = fields_initkw(**kw)
    other['omit_readonly'] = not keep_all_readonly
    return FormFields(*args, **other)

class Widgets(object):

    interface.implements(interfaces.IWidgets)

    def __init__(self, widgets, prefix_length=None, prefix=None):
        self.__Widgets_widgets_items__ = widgets
        self.__Widgets_widgets_list__ = [w for (i, w) in widgets]
        if prefix is None:
            # BBB Allow old code using the prefix_length argument.
            if prefix_length is None:
                raise TypeError(
                    "One of 'prefix_length' and 'prefix' is required."
                    )
            self.__Widgets_widgets_dict__ = dict(
                [(w.name[prefix_length:], w) for (i, w) in widgets]
                )
        else:
            prefix = expandPrefix(prefix)
            self.__Widgets_widgets_dict__ = dict(
                [(_widgetKey(w, prefix), w) for (i, w) in widgets]
                )

    def __iter__(self):
        return iter(self.__Widgets_widgets_list__)

    def __getitem__(self, name):
        return self.__Widgets_widgets_dict__[name]

    # TODO need test
    def get(self, name):
        return self.__Widgets_widgets_dict__.get(name)

    def __iter_input_and_widget__(self):
        return iter(self.__Widgets_widgets_items__)


    # TODO need test
    def __add__(self, other):
        widgets = self.__class__([], 0)
        widgets.__Widgets_widgets_items__ = (
            self.__Widgets_widgets_items__ + other.__Widgets_widgets_items__)
        widgets.__Widgets_widgets_list__ = (
            self.__Widgets_widgets_list__ + other.__Widgets_widgets_list__)
        widgets.__Widgets_widgets_dict__ = self.__Widgets_widgets_dict__.copy()
        widgets.__Widgets_widgets_dict__.update(other.__Widgets_widgets_dict__)
        return widgets

def canWrite(context, field):
    writer = getattr(field, 'writer', None)
    if writer is not None:
        return zope.security.canAccess(context, writer.__name__)
    return zope.security.canWrite(context, field.__name__)

def setUpWidgets(form_fields,
                 form_prefix=None, context=None, request=None, form=None,
                 data=(), adapters=None, ignore_request=False):

    if request is None:
        request = form.request
    if context is None and form is not None:
        context = form.context
    if form_prefix is None:
        form_prefix = form.prefix

    widgets = []
    adapter = None
    for form_field in form_fields:
        field = form_field.field
        if form_field.render_context:
            if adapters is None:
                adapters = {}

            # Adapt context, if necessary
            interface = form_field.interface
            adapter = adapters.get(interface)
            if adapter is None:
                if interface is None:
                    adapter = context
                else:
                    adapter = interface(context)
                adapters[interface] = adapter
                if interface is not None:
                    adapters[interface.__name__] = adapter
            field = field.bind(adapter)
        else:
            field = field.bind(context)

        readonly = form_field.for_display
        readonly = readonly or (field.readonly and not form_field.for_input)
        readonly = readonly or (
            (form_field.render_context & interfaces.DISPLAY_UNWRITEABLE)
            and not canWrite(context, field)
            )

        if form_field.custom_widget is not None:
            widget = form_field.custom_widget(field, request)
        else:
            if readonly:
                widget = component.getMultiAdapter((field, request),
                                                   IDisplayWidget)
            else:
                widget = component.getMultiAdapter((field, request),
                                                   IInputWidget)

        prefix = form_prefix
        if form_field.prefix:
            prefix = expandPrefix(prefix) + form_field.prefix

        widget.setPrefix(prefix)

        if ignore_request or readonly or not widget.hasInput():
            # Get the value to render
            if form_field.__name__ in data:
                widget.setRenderedValue(data[form_field.__name__])
            elif form_field.get_rendered is not None:
                widget.setRenderedValue(form_field.get_rendered(form))
            elif form_field.render_context:
                widget.setRenderedValue(field.get(adapter))
            else:
                widget.setRenderedValue(field.default)

        widgets.append((not readonly, widget))

    return Widgets(widgets, prefix=form_prefix)

def setUpInputWidgets(form_fields, form_prefix, context, request,
                      form=None, ignore_request=False):
    widgets = []
    for form_field in form_fields:
        field = form_field.field.bind(context)
        widget = _createWidget(form_field, field, request, IInputWidget)

        prefix = form_prefix
        if form_field.prefix:
            prefix = expandPrefix(prefix) + form_field.prefix

        widget.setPrefix(prefix)

        if ignore_request:
            if form_field.get_rendered is not None:
                value = form_field.get_rendered(form)
            else:
                value = field.default
            widget.setRenderedValue(value)

        widgets.append((True, widget))
    return Widgets(widgets, prefix=form_prefix)


def _createWidget(form_field, field, request, iface):
    if form_field.custom_widget is None:
        return component.getMultiAdapter((field, request), iface)
    else:
        return form_field.custom_widget(field, request)


def getWidgetsData(widgets, form_prefix, data):
    errors = []
    form_prefix = expandPrefix(form_prefix)

    for input, widget in widgets.__iter_input_and_widget__():
        if input and IInputWidget.providedBy(widget):
            name = _widgetKey(widget, form_prefix)

            if not widget.hasInput():
                continue

            try:
                data[name] = widget.getInputValue()
            except ValidationError, error:
                # convert field ValidationError to WidgetInputError
                error = WidgetInputError(widget.name, widget.label, error)
                errors.append(error)
            except InputErrors, error:
                errors.append(error)

    return errors

def _widgetKey(widget, form_prefix):
    name = widget.name
    if name.startswith(form_prefix):
        name = name[len(form_prefix):]
    else:
        raise ValueError("Name does not match prefix", name, form_prefix)
    return name

def setUpEditWidgets(form_fields, form_prefix, context, request,
                     adapters=None, for_display=False,
                     ignore_request=False):
    if adapters is None:
        adapters = {}

    widgets = []
    for form_field in form_fields:
        field = form_field.field
        # Adapt context, if necessary
        interface = form_field.interface
        adapter = adapters.get(interface)
        if adapter is None:
            if interface is None:
                adapter = context
            else:
                adapter = interface(context)
            adapters[interface] = adapter
            if interface is not None:
                adapters[interface.__name__] = adapter

        field = field.bind(adapter)

        readonly = form_field.for_display
        readonly = readonly or (field.readonly and not form_field.for_input)
        readonly = readonly or (
            (form_field.render_context & interfaces.DISPLAY_UNWRITEABLE)
            and not canWrite(context, field)
            )
        readonly = readonly or for_display

        if readonly:
            iface = IDisplayWidget
        else:
            iface = IInputWidget
        widget = _createWidget(form_field, field, request, iface)

        prefix = form_prefix
        if form_field.prefix:
            prefix = expandPrefix(prefix) + form_field.prefix

        widget.setPrefix(prefix)

        if ignore_request or readonly or not widget.hasInput():
            # Get the value to render
            value = field.get(adapter)
            widget.setRenderedValue(value)

        widgets.append((not readonly, widget))

    return Widgets(widgets, prefix=form_prefix)

def setUpDataWidgets(form_fields, form_prefix, context, request, data=(),
                     for_display=False, ignore_request=False):
    widgets = []
    for form_field in form_fields:
        field = form_field.field.bind(context)
        readonly = for_display or field.readonly or form_field.for_display
        if readonly:
            iface = IDisplayWidget
        else:
            iface = IInputWidget
        widget = _createWidget(form_field, field, request, iface)

        prefix = form_prefix
        if form_field.prefix:
            prefix = expandPrefix(prefix) + form_field.prefix

        widget.setPrefix(prefix)

        if ((form_field.__name__ in data)
            and (ignore_request or readonly or not widget.hasInput())
            ):
            widget.setRenderedValue(data[form_field.__name__])

        widgets.append((not readonly, widget))

    return Widgets(widgets, prefix=form_prefix)


class NoInputData(interface.Invalid):
    """There was no input data because:

    - It wasn't asked for

    - It wasn't entered by the user

    - It was entered by the user, but the value entered was invalid

    This exception is part of the internal implementation of checkInvariants.

    """

class FormData:

    def __init__(self, schema, data):
        self._FormData_data___ = data
        self._FormData_schema___ = schema

    def __getattr__(self, name):
        schema = self._FormData_schema___
        data = self._FormData_data___
        try:
            field = schema[name]
        except KeyError:
            raise AttributeError(name)
        else:
            value = data.get(name, data)
            if value is data:
                raise NoInputData(name)
            if zope.interface.interfaces.IMethod.providedBy(field):
                if not IField.providedBy(field):
                    raise RuntimeError(
                        "Data value is not a schema field", name)
                v = lambda: value
            else:
                v = value
            setattr(self, name, v)
            return v
        raise AttributeError(name)


def checkInvariants(form_fields, form_data):

    # First, collect the data for the various schemas
    schema_data = {}
    for form_field in form_fields:
        schema = form_field.interface
        if schema is None:
            continue

        data = schema_data.get(schema)
        if data is None:
            data = schema_data[schema] = {}

        if form_field.__name__ in form_data:
            data[form_field.field.__name__] = form_data[form_field.__name__]

    # Now validate the individual schemas
    errors = []
    for schema, data in schema_data.items():
        try:
            schema.validateInvariants(FormData(schema, data), errors)
        except interface.Invalid:
            pass # Just collect the errors

    return [error for error in errors if not isinstance(error, NoInputData)]

def applyChanges(context, form_fields, data, adapters=None):
    if adapters is None:
        adapters = {}

    changed = False

    for form_field in form_fields:
        field = form_field.field
        # Adapt context, if necessary
        interface = form_field.interface
        adapter = adapters.get(interface)
        if adapter is None:
            if interface is None:
                adapter = context
            else:
                adapter = interface(context)
            adapters[interface] = adapter

        name = form_field.__name__
        newvalue = data.get(name, form_field) # using form_field as marker
        if (newvalue is not form_field) and (field.get(adapter) != newvalue):
            changed = True
            field.set(adapter, newvalue)

    return changed

_identifier = re.compile('[A-Za-z][a-zA-Z0-9_]*$')

def _action_options(success=None, failure=None, condition=None, validator=None,
                    prefix='actions', name=None, data=None,
                    ):
    return (success, failure, condition, validator, prefix, name, data)

def _callify(f):
    if isinstance(f, str):
        callable = lambda form, *args: getattr(form, f)(*args)
    else:
        callable = f

    return callable

class Action(object):

    interface.implements(interfaces.IAction)

    def __init__(self, label, **options):
        (success, failure, condition, validator,
         prefix, name, data
         ) = _action_options(**options)

        self.label = label

        [self.success_handler, self.failure_handler,
         self.condition, self.validator] = [
            _callify(f) for f in (success, failure, condition, validator)]

        if name is None:
            if _identifier.match(label):
                name = unicode(label).lower()
            else:
                name = label.encode('hex')

        self.__name__ = expandPrefix(prefix) + name

        if data is None:
            data = {}
        self.data = data

    def __get__(self, form, class_=None):
        if form is None:
            return self
        result = self.__class__.__new__(self.__class__)
        result.__dict__.update(self.__dict__)
        result.form = form
        result.__name__ = expandPrefix(form.prefix) + result.__name__
        interface.alsoProvides(result, interfaces.IBoundAction)
        return result

    def available(self):
        condition = self.condition
        return (condition is None) or condition(self.form, self)

    def validate(self, data):
        if self.validator is not None:
            return self.validator(self.form, self, data)

    def success(self, data):
        if self.success_handler is not None:
            return self.success_handler(self.form, self, data)

    def failure(self, data, errors):
        if self.failure_handler is not None:
            return self.failure_handler(self.form, self, data, errors)

    def submitted(self):
        return (self.__name__ in self.form.request.form) and self.available()

    def update(self):
        pass

    render = namedtemplate.NamedTemplate('render')

@namedtemplate.implementation(interfaces.IAction)
def render_submit_button(self):
    if not self.available():
        return ''
    label = self.label
    if isinstance(label, zope.i18nmessageid.Message):
        label = zope.i18n.translate(self.label, context=self.form.request)
    return ('<input type="submit" id="%s" name="%s" value="%s"'
            ' class="button" />' %
            (self.__name__, self.__name__, label)
            )

class action:
    def __init__(self, label, actions=None, **options):
        caller_locals = sys._getframe(1).f_locals
        if actions is None:
            actions = caller_locals.get('actions')
        if actions is None:
            actions = caller_locals['actions'] = Actions()
        self.actions = actions
        self.label = label
        self.options = options

    def __call__(self, success):
        action = Action(self.label, success=success, **self.options)
        self.actions.append(action)
        return action


class Actions(object):

    interface.implements(interfaces.IActions)

    def __init__(self, *actions):
        self.actions = actions
        self.byname = dict([(a.__name__, a) for a in actions])

    def __iter__(self):
        return iter(self.actions)

    def __getitem__(self, name):
        try:
            return self.byname[name]
        except TypeError:
            if isinstance(name, slice):
                return self.__class__(
                    *self.actions[name.start:name.stop:name.step]
                    )

    def append(self, action):
        self.actions += (action, )
        self.byname[action.__name__] = action

    # TODO need test
    def __add__(self, other):
        return self.__class__(*(self.actions + other.actions))

    def copy(self):
        return self.__class__(*self.actions)

    def __get__(self, inst, class_):
        if inst is None:
            return self
        return self.__class__(*[a.__get__(inst) for a in self.actions])

def handleSubmit(actions, data, default_validate=None):

    for action in actions:
        if action.submitted():
            errors = action.validate(data)
            if errors is None and default_validate is not None:
                errors = default_validate(action, data)
            return errors, action

    return None, None

# TODO need test for this
def availableActions(form, actions):
    result = []
    for action in actions:
        condition = action.condition
        if (condition is None) or condition(form, action):
            result.append(action)
    return result


class FormBase(zope.publisher.browser.BrowserPage):

    label = u''

    prefix = 'form'

    status = ''

    errors = ()

    interface.implements(interfaces.IForm)

    def setPrefix(self, prefix):
        self.prefix = prefix

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        self.widgets = setUpWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            form=self, adapters=self.adapters, ignore_request=ignore_request)

    def validate(self, action, data):
        return (getWidgetsData(self.widgets, self.prefix, data)
                + checkInvariants(self.form_fields, data))

    template = namedtemplate.NamedTemplate('default')

    # TODO also need to be able to show disabled actions
    def availableActions(self):
        return availableActions(self, self.actions)

    def resetForm(self):
        self.setUpWidgets(ignore_request=True)

    form_result = None
    form_reset = True

    def update(self):
        self.setUpWidgets()
        self.form_reset = False

        data = {}
        errors, action = handleSubmit(self.actions, data, self.validate)
        # the following part will make sure that previous error not
        # get overriden by new errors. This is usefull for subforms. (ri)
        if self.errors is None:
            self.errors = errors
        else:
            if errors is not None:
                self.errors += tuple(errors)

        if errors:
            self.status = _('There were errors')
            result = action.failure(data, errors)
        elif errors is not None:
            self.form_reset = True
            result = action.success(data)
        else:
            result = None

        self.form_result = result

    def render(self):
        # if the form has been updated, it will already have a result
        if self.form_result is None:
            if self.form_reset:
                # we reset, in case data has changed in a way that
                # causes the widgets to have different data
                self.resetForm()
                self.form_reset = False
            self.form_result = self.template()

        return self.form_result

    def __call__(self):
        self.update()
        return self.render()

    def error_views(self):
        for error in self.errors:
            if isinstance(error, basestring):
                yield error
            else:
                view = component.getMultiAdapter(
                    (error, self.request),
                    zope.app.form.browser.interfaces.IWidgetInputErrorView)
                title = getattr(error, 'widget_title', None) # duck typing
                if title:
                    if isinstance(title, zope.i18n.Message):
                        title = zope.i18n.translate(title, context=self.request)
                    yield '%s: %s' % (title, view.snippet())
                else:
                    yield view.snippet()


def haveInputWidgets(form, action):
    for input, widget in form.widgets.__iter_input_and_widget__():
        if input:
            return True
    else:
        return False

class EditFormBase(FormBase):

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        self.widgets = setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )

    @action(_("Apply"), condition=haveInputWidgets)
    def handle_edit_action(self, action, data):
        if applyChanges(self.context, self.form_fields, data, self.adapters):
            zope.event.notify(ObjectModifiedEvent(self.context))
            formatter = self.request.locale.dates.getFormatter(
                'dateTime', 'medium')

            try:
                time_zone = idatetime.ITZInfo(self.request)
            except TypeError:
                time_zone = pytz.UTC

            status = _("Updated on ${date_time}",
                       mapping={'date_time':
                                formatter.format(
                                   datetime.datetime.now(time_zone)
                                   )
                        }
                       )
            self.status = status
        else:
            self.status = _('No changes')

class DisplayFormBase(FormBase):

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        self.widgets = setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, for_display=True,
            ignore_request=ignore_request
            )

    actions = ()


class AddFormBase(FormBase):

    interface.implements(interfaces.IAddFormCustomization,
                         zope.component.interfaces.IFactory)

    component.adapts(zope.app.container.interfaces.IAdding,
                     zope.publisher.interfaces.browser.IBrowserRequest)

    def __init__(self, context, request):
        self.__parent__ = context
        super(AddFormBase, self).__init__(context, request)

    def setUpWidgets(self, ignore_request=False):
        self.widgets = setUpInputWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            ignore_request=ignore_request,
            )

    @action(_("Add"), condition=haveInputWidgets)
    def handle_add(self, action, data):
        self.createAndAdd(data)

    # zope.formlib.interfaces.IAddFormCustomization

    def createAndAdd(self, data):
        ob = self.create(data)
        zope.event.notify(ObjectCreatedEvent(ob))
        return self.add(ob)

    def create(self, data):
        raise NotImplementedError(
            "concrete classes must implement create() or createAndAdd()")

    _finished_add = False

    def add(self, object):
        ob = self.context.add(object)
        self._finished_add = True
        return ob

    def render(self):
        if self._finished_add:
            self.request.response.redirect(self.nextURL())
            return ""
        return super(AddFormBase, self).render()

    def nextURL(self):
        return self.context.nextURL()


default_page_template = namedtemplate.NamedTemplateImplementation(
    ViewPageTemplateFile('pageform.pt'), interfaces.IPageForm)

default_subpage_template = namedtemplate.NamedTemplateImplementation(
    ViewPageTemplateFile('subpageform.pt'), interfaces.ISubPageForm)

class PageForm(FormBase):

    interface.implements(interfaces.IPageForm)

Form = PageForm

class PageEditForm(EditFormBase):

    interface.implements(interfaces.IPageForm)

EditForm = PageEditForm

class PageDisplayForm(DisplayFormBase):

    interface.implements(interfaces.IPageForm)

DisplayForm = PageDisplayForm

class PageAddForm(AddFormBase):

    interface.implements(interfaces.IPageForm)

AddForm = PageAddForm

class SubPageForm(FormBase):

    interface.implements(interfaces.ISubPageForm)

class SubPageEditForm(EditFormBase):

    interface.implements(interfaces.ISubPageForm)

class SubPageDisplayForm(DisplayFormBase):

    interface.implements(interfaces.ISubPageForm)

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Configuration handlers for forms and widgets

$Id: metaconfigure.py 40306 2005-11-21 20:59:01Z dominikhuber $
"""
__docformat__ = 'restructuredtext'

import os

import zope.component
from zope.security.checker import CheckerPublic
from zope.interface import implementedBy
from zope.component.interfaces import IViewFactory
from zope.configuration.exceptions import ConfigurationError

from zope.schema import getFieldNamesInOrder
from zope.app.container.interfaces import IAdding
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.app.publisher.browser.menumeta import menuItemDirective
from zope.app.i18n import ZopeMessageFactory as _

from zope.app.form import CustomWidgetFactory
from zope.app.form.interfaces import IInputWidget, IDisplayWidget
from add import AddView, AddViewFactory
from editview import EditView, EditViewFactory
from formview import FormView
from schemadisplay import DisplayView, DisplayViewFactory

class BaseFormDirective(object):

    # to be overriden by the subclasses
    view = None
    default_template = None

    # default basic information
    for_ = None
    layer = IDefaultBrowserLayer
    permission = CheckerPublic
    template = None
    class_ = None

    # default form information
    title = None
    label = None
    menu = None
    fields = None

    def __init__(self, _context, **kwargs):
        self._context = _context
        for key, value in kwargs.items():
            if not (value is None and hasattr(self, key)):
                setattr(self, key, value)
        self._normalize()
        self._widgets = {}

    def widget(self, _context, field, **kw):
        attrs = kw
        class_ = attrs.pop("class_", None)
        # Try to do better than accepting the string value by looking through
        # the interfaces and trying to find the field, so that we can use
        # 'fromUnicode()'
        if isinstance(class_, type):
            ifaces = implementedBy(class_)
            for name, value in kw.items():
                for iface in ifaces:
                    if name in iface:
                        attrs[name] = iface[name].fromUnicode(value)
                        break
        if class_ is None:
            # The _default_widget_factory is required to allow the
            # <widget> directive to be given without a "class"
            # attribute.  This can be used to override some of the
            # presentational attributes of the widget implementation.
            class_ = self._default_widget_factory
        
        # don't wrap a factory into a factory
        if IViewFactory.providedBy(class_):
            factory = class_
        else:
            factory = CustomWidgetFactory(class_, **attrs)

        self._widgets[field+'_widget'] = factory

    def _processWidgets(self):
        if self._widgets:
            customWidgetsObject = type('CustomWidgetsMixin', (object,),
                                       self._widgets)
            self.bases = self.bases + (customWidgetsObject,)

    def _normalize(self):
        if self.for_ is None:
            self.for_ = self.schema

        if self.class_ is None:
            self.bases = (self.view,)
        else:
            self.bases = (self.class_, self.view)

        if self.template is not None:
            self.template = os.path.abspath(str(self.template))
            if not os.path.isfile(self.template):
                raise ConfigurationError("No such file", self.template)
        else:
            self.template = self.default_template

        self.names = getFieldNamesInOrder(self.schema)

        if self.fields:
            for name in self.fields:
                if name not in self.names:
                    raise ValueError("Field name is not in schema",
                                     name, self.schema)
        else:
            self.fields = self.names

    def _args(self):
        permission = self.permission
        if permission == 'zope.Public':
            # Translate public permission to CheckerPublic
            permission = CheckerPublic
        return (self.name, self.schema, self.label, permission,
                self.layer, self.template, self.default_template,
                self.bases, self.for_, self.fields)

    def _discriminator(self):
        return ('view', self.for_, self.name, IBrowserRequest,
                self.layer)


class AddFormDirective(BaseFormDirective):

    view = AddView
    default_template = 'add.pt'
    for_ = IAdding

    # default add form information
    description = None
    content_factory_id = None
    content_factory = None
    arguments = None
    keyword_arguments = None
    set_before_add = None
    set_after_add = None

    def _default_widget_factory(self, field, request):
        # `field` is a bound field
        return zope.component.getMultiAdapter(
            (field, request), IInputWidget)

    def _handle_menu(self):
        if self.menu or self.title:
            if (not self.menu) or (not self.title):
                raise ValueError("If either menu or title are specified, "
                                 "they must both be specified")
            # Add forms are really for IAdding components, so do not use
            # for=self.schema.
            menuItemDirective(
                self._context, self.menu, self.for_, '@@' + self.name,
                self.title, permission=self.permission, layer=self.layer,
                description=self.description)

    def _handle_arguments(self, leftover=None):
        schema = self.schema
        fields = self.fields
        arguments = self.arguments
        keyword_arguments = self.keyword_arguments
        set_before_add = self.set_before_add
        set_after_add = self.set_after_add

        if leftover is None:
            leftover = fields

        if arguments:
            missing = [n for n in arguments if n not in fields]
            if missing:
                raise ValueError("Some arguments are not included in the form",
                                 missing)
            optional = [n for n in arguments if not schema[n].required]
            if optional:
                raise ValueError("Some arguments are optional, use"
                                 " keyword_arguments for them",
                                 optional)
            leftover = [n for n in leftover if n not in arguments]

        if keyword_arguments:
            missing = [n for n in keyword_arguments if n not in fields]
            if missing:
                raise ValueError(
                    "Some keyword_arguments are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in keyword_arguments]

        if set_before_add:
            missing = [n for n in set_before_add if n not in fields]
            if missing:
                raise ValueError(
                    "Some set_before_add are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in set_before_add]

        if set_after_add:
            missing = [n for n in set_after_add if n not in fields]
            if missing:
                raise ValueError(
                    "Some set_after_add are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in set_after_add]

            self.set_after_add += leftover

        else:
            self.set_after_add = leftover

    def _handle_content_factory(self):
        if self.content_factory is None:
            self.content_factory = self.content_factory_id

    def __call__(self):
        self._processWidgets()
        self._handle_menu()
        self._handle_content_factory()
        self._handle_arguments()

        self._context.action(
            discriminator=self._discriminator(),
            callable=AddViewFactory,
            args=self._args()+(self.content_factory, self.arguments,
                                 self.keyword_arguments,
                                 self.set_before_add, self.set_after_add),
            )

class EditFormDirectiveBase(BaseFormDirective):

    view = EditView

    def _default_widget_factory(self, field, request):
        # `field` is a bound field
        if field.readonly:
            iface = IDisplayWidget
        else:
            iface = IInputWidget
        return zope.component.getMultiAdapter(
            (field, request), iface)

class EditFormDirective(EditFormDirectiveBase):

    default_template = 'edit.pt'
    title = _('Edit')

    def _handle_menu(self):
        if self.menu:
            menuItemDirective(
                self._context, self.menu, self.for_ or self.schema,
                '@@' + self.name, self.title, permission=self.permission,
                layer=self.layer)

    def __call__(self):
        self._processWidgets()
        self._handle_menu()
        self._context.action(
            discriminator=self._discriminator(),
            callable=EditViewFactory,
            args=self._args(),
        )

class FormDirective(EditFormDirective):

    view = FormView

    def __init__(self, _context, **kwargs):
        super(FormDirective, self).__init__(_context, **kwargs)
        attrs = self.class_.__dict__.keys()
        if 'template' not in kwargs.keys() and 'update' not in attrs and \
               ('getData' not in attrs or 'setData' not in attrs):
            raise ConfigurationError(
                "You must specify a class that implements `getData()` "
                "and `setData()`, if you do not overwrite `update()`.")


class SubeditFormDirective(EditFormDirectiveBase):

    default_template = 'subedit.pt'

    # default subedit form directive
    fulledit_path = None
    fulledit_label = None

    def __call__(self):
        self._processWidgets()
        self._context.action(
            discriminator = self._discriminator(),
            callable = EditViewFactory,
            args = self._args()+(self.fulledit_path, self.fulledit_label),
            )


class SchemaDisplayDirective(EditFormDirective):

    view = DisplayView
    default_template = 'display.pt'

    def __call__(self):
        self._processWidgets()
        self._handle_menu()
        self._context.action(
            discriminator = self._discriminator(),
            callable = DisplayViewFactory,
            args = self._args()+(self.menu,)
            )

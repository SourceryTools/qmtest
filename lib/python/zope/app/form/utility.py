##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Form utility functions

In Zope 2's formulator, forms provide a basic mechanism for
organizing collections of fields and providing user interfaces for
them, especially editing interfaces.

In Zope 3, formulator's forms are replaced by Schema (See
zope.schema). In addition, the Formulator fields have been replaced by
schema fields and form widgets. Schema fields just express the semantics
of data values. They contain no presentation logic or parameters.
Widgets are views on fields that take care of presentation. The widget
view names represent styles that can be selected by applications to
customise the presentation. There can also be custom widgets with
specific parameters.

This module provides some utility functions that provide some of the
functionality of formulator forms that isn't handled by schema,
fields, or widgets.

$Id: utility.py 29638 2005-03-22 16:00:21Z benji_york $
"""
__docformat__ = 'restructuredtext'

from zope import security
from zope.security.proxy import Proxy
from zope.proxy import isProxy
from zope.interface.interfaces import IMethod
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.schema import getFieldsInOrder
from zope.app import zapi
from zope.app.form.interfaces import IWidget
from zope.app.form.interfaces import WidgetsError, MissingInputError
from zope.app.form.interfaces import InputErrors
from zope.app.form.interfaces import IInputWidget, IDisplayWidget
from zope.component.interfaces import IViewFactory

# A marker that indicates 'no value' for any of the utility functions that
# accept a 'value' argument.
no_value = object()

def _fieldlist(names, schema):
    if not names:
        fields = getFieldsInOrder(schema)
    else:
        fields = [ (name, schema[name]) for name in names ]
    return fields
    
    
def _createWidget(context, field, viewType, request):
    """Creates a widget given a `context`, `field`, and `viewType`."""    
    field = field.bind(context)
    return zapi.getMultiAdapter((field, request), viewType)

def _widgetHasStickyValue(widget):
    """Returns ``True`` if the widget has a sticky value.
    
    A sticky value is input from the user that should not be overridden
    by an object's current field value. E.g. a user may enter an invalid
    postal code, submit the form, and receive a validation error - the postal
    code should be treated as 'sticky' until the user successfully updates
    the object.
    """
    return IInputWidget.providedBy(widget) and widget.hasInput()
    
def setUpWidget(view, name, field, viewType, value=no_value, prefix=None,
                ignoreStickyValues=False, context=None):
    """Sets up a single view widget.

    The widget will be an attribute of the `view`. If there is already
    an attribute of the given name, it must be a widget and it will be
    initialized with the given `value` if not ``no_value``.

    If there isn't already a `view` attribute of the given name, then a
    widget will be created and assigned to the attribute.
    """
    if context is None:
        context = view.context
    widgetName = name + '_widget'
    
    # check if widget already exists
    widget = getattr(view, widgetName, None)
    if widget is None:
        # does not exist - create it
        widget = _createWidget(context, field, viewType, view.request)
        setattr(view, widgetName, widget)
    elif IViewFactory.providedBy(widget):
        # exists, but is actually a factory - use it to create the widget
        widget = widget(field.bind(context), view.request)
        setattr(view, widgetName, widget)
        
    # widget must implement IWidget
    if not IWidget.providedBy(widget):
        raise TypeError(
            "Unable to configure a widget for %s - attribute %s does not "
            "implement IWidget" % (name, widgetName))
    
    if prefix:
        widget.setPrefix(prefix)
        
    if value is not no_value and (
        ignoreStickyValues or not _widgetHasStickyValue(widget)):
        widget.setRenderedValue(value)


def setUpWidgets(view, schema, viewType, prefix=None, ignoreStickyValues=False,
                 initial={}, names=None, context=None):
    """Sets up widgets for the fields defined by a `schema`.
    
    Appropriate for collecting input without a current object implementing
    the schema (such as an add form).

    `view` is the view that will be configured with widgets. 

    `viewType` is the type of widgets to create (e.g. IInputWidget or
    IDisplayWidget).

    `schema` is an interface containing the fields that widgets will be
    created for.

    `prefix` is a string that is prepended to the widget names in the generated
    HTML. This can be used to differentiate widgets for different schemas.

    `ignoreStickyValues` is a flag that, when ``True``, will cause widget
    sticky values to be replaced with the context field value or a value
    specified in initial.

    `initial` is a mapping of field names to initial values.

    `names` is an optional iterable that provides an ordered list of field
    names to use. If names is ``None``, the list of fields will be defined by
    the schema.

    `context` provides an alternative context for acquisition.
    """
    for (name, field) in _fieldlist(names, schema):
        setUpWidget(view, name, field, viewType, 
                    value=initial.get(name, no_value),
                    prefix=prefix,
                    ignoreStickyValues=ignoreStickyValues, 
                    context=context)

def setUpEditWidgets(view, schema, source=None, prefix=None,
                     ignoreStickyValues=False, names=None, context=None,
                     degradeInput=False, degradeDisplay=False):
    """Sets up widgets to collect input on a view.
    
    See `setUpWidgets` for details on `view`, `schema`, `prefix`,
    `ignoreStickyValues`, `names`, and `context`.
    
    `source`, if specified, is an object from which initial widget values are
    read. If source is not specified, the view context is used as the source.
    
    `degradeInput` is a flag that changes the behavior when a user does not
    have permission to edit a field in the names.  By default, the function
    raises Unauthorized.  If degradeInput is True, the field is changed to
    an IDisplayWidget.
    
    `degradeDisplay` is a flag that changes the behavior when a user does not
    have permission to access a field in the names.  By default, the function
    raises Unauthorized.  If degradeDisplay is True, the field is removed from
    the form.
    
    Returns a list of names, equal to or a subset of the names that were 
    supposed to be drawn, with uninitialized undrawn fields missing.
    """
    if context is None:
        context = view.context
    if source is None:
        source = view.context
    security_proxied = isProxy(source, Proxy)
    res_names = []
    for name, field in _fieldlist(names, schema):
        try:
            value = field.get(source)
        except ForbiddenAttribute:
            raise
        except AttributeError, v:
            value = no_value
        except Unauthorized:
            if degradeDisplay:
                continue
            else:
                raise
        if field.readonly:
            viewType = IDisplayWidget
        else:
            if security_proxied:
                is_accessor = IMethod.providedBy(field)
                if is_accessor:
                    set_name = field.writer.__name__
                    authorized = security.canAccess(source, set_name)
                else:
                    set_name = name
                    authorized = security.canWrite(source, name)
                if not authorized:
                    if degradeInput:
                        viewType = IDisplayWidget
                    else:
                        raise Unauthorized(set_name)
                else:
                    viewType = IInputWidget
            else:
                # if object is not security proxied, might be a standard
                # adapter without a registered checker.  If the feature of
                # paying attention to the users ability to actually set a
                # field is decided to be a must-have for the form machinery,
                # then we ought to change this case to have a deprecation
                # warning.
                viewType = IInputWidget
        setUpWidget(view, name, field, viewType, value, prefix,
                    ignoreStickyValues, context)
        res_names.append(name)
    return res_names

def setUpDisplayWidgets(view, schema, source=None, prefix=None, 
                        ignoreStickyValues=False, names=None, context=None,
                        degradeDisplay=False):
    """Sets up widgets to display field values on a view.
    
    See `setUpWidgets` for details on `view`, `schema`, `prefix`,
    `ignoreStickyValues`, `names`, and `context`.
    
    `source`, if specified, is an object from which initial widget values are
    read. If source is not specified, the view context is used as the source.
    
    `degradeDisplay` is a flag that changes the behavior when a user does not
    have permission to access a field in the names.  By default, the function
    raises Unauthorized.  If degradeDisplay is True, the field is removed from
    the form.
    
    Returns a list of names, equal to or a subset of the names that were 
    supposed to be drawn, with uninitialized undrawn fields missing.
    """
    if context is None:
        context = view.context
    if source is None:
        source = view.context
    res_names = []
    for name, field in _fieldlist(names, schema):
        try:
            value = field.get(source)
        except ForbiddenAttribute:
            raise
        except AttributeError, v:
            value = no_value
        except Unauthorized:
            if degradeDisplay:
                continue
            else:
                raise
        setUpWidget(view, name, field, IDisplayWidget, value, prefix,
                    ignoreStickyValues, context)
        res_names.append(name)
    return res_names

def viewHasInput(view, schema, names=None):
    """Returns ``True`` if the any of the view's widgets contain user input.
    
    `schema` specifies the set of fields that correspond to the view widgets.
    
    `names` can be specified to provide a subset of these fields.
    """
    for name, field in _fieldlist(names, schema):
        if  getattr(view, name + '_widget').hasInput():
            return True
    return False

def applyWidgetsChanges(view, schema, target=None, names=None):
    """Updates an object with values from a view's widgets.
    
    `view` contained the widgets that perform the update. By default, the
    widgets will update the view's context.
    
    `target` can be specified as an alternative object to update.
    
    `schema` contrains the values provided by the widgets.
    
    `names` can be specified to update a subset of the schema constrained
    values.
    """
    errors = []
    changed = False
    if target is None:
        target = view.context

    for name, field in _fieldlist(names, schema):
        widget = getattr(view, name + '_widget')
        if IInputWidget.providedBy(widget) and widget.hasInput():
            try:
                changed = widget.applyChanges(target) or changed
            except InputErrors, v:
                errors.append(v)
    if errors:
        raise WidgetsError(errors)

    return changed

def getWidgetsData(view, schema, names=None):
    """Returns user entered data for a set of `schema` fields.
    
    The return value is a map of field names to data values.
    
    `view` is the view containing the widgets. `schema` is the schema that
    defines the widget fields. An optional `names` argument can be provided
    to specify an alternate list of field values to return. If `names` is
    not specified, or is ``None``, `getWidgetsData` will attempt to return
    values for all of the fields in the schema.
    
    A requested field value may be omitted from the result for one of two
    reasons:
        
        - The field is read only, in which case its widget will not have
          user input.
          
        - The field is editable and not required but its widget does not 
          contain user input.
    
    If a field is required and its widget does not have input, `getWidgetsData`
    raises an error.
    
    A widget may raise a validation error if it cannot return a value that
    satisfies its field's contraints.
    
    Errors, if any, are collected for all fields and reraised as a single
    `WidgetsError`.
    """
    result = {}
    errors = []

    for name, field in _fieldlist(names, schema):
        widget = getattr(view, name + '_widget')
        if IInputWidget.providedBy(widget):
            if widget.hasInput():
                try:
                    result[name] = widget.getInputValue()
                except InputErrors, error:
                    errors.append(error)
            elif field.required:
                errors.append(MissingInputError(
                    name, widget.label, 'the field is required'))
            
    if errors:
        raise WidgetsError(errors, widgetsData=result)
        
    return result


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
"""Validation Exceptions

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.schema.interfaces import ValidationError
from zope.component.interfaces import IView
from zope.interface import Attribute, Interface, implements
from zope.schema import Bool
from zope.exceptions.interfaces import UserError

class IWidgetInputError(Interface):
    """Placeholder for a snippet View"""

    def doc():
        """Returns a string that represents the error message."""

class WidgetInputError(UserError):
    """One or more user input errors occurred."""

    implements(IWidgetInputError)

    def __init__(self, field_name, widget_title, errors=None):
        """Initialize Error

        `errors` is a ``ValidationError`` or a list of ValidationError objects
        """
        UserError.__init__(self, field_name, widget_title, errors)
        self.field_name = field_name
        self.widget_title = widget_title
        self.errors = errors

    def doc(self):
        # TODO this duck typing is to get the code working.  See
        # collector issue 372
        if isinstance(self.errors, basestring):
            return self.errors
        elif getattr(self.errors, 'doc', None) is not None:
            return self.errors.doc()
        return ''


class MissingInputError(WidgetInputError):
    """Required data was not supplied."""


class ConversionError(Exception):
    """A conversion error occurred."""

    implements(IWidgetInputError)

    def __init__(self, error_name, original_exception=None):
        Exception.__init__(self, error_name, original_exception)
        self.error_name = error_name
        self.original_exception = original_exception

    def doc(self):
        return self.error_name

InputErrors = WidgetInputError, ValidationError, ConversionError


class ErrorContainer(Exception):
    """A base error class for collecting multiple errors."""

    def append(self, error):
        self.args += (error, )

    def __len__(self):
        return len(self.args)

    def __iter__(self):
        return iter(self.args)

    def __getitem__(self, i):
        return self.args[i]

    def __str__(self):
        return "\n".join(
            ["%s: %s" % (error.__class__.__name__, error)
             for error in self.args]
            )

    __repr__ = __str__

class WidgetsError(ErrorContainer):
    """A collection of errors from widget processing.

    widgetValues is a map containing the list of values that were obtained
    from the widgets, keyed by field name.
    """

    def __init__(self, errors, widgetsData={}):
        ErrorContainer.__init__(self, *errors)
        self.widgetsData = widgetsData

class IWidget(IView):
    """Generically describes the behavior of a widget.

    Note that this level must be still presentation independent.
    """

    name = Attribute(
        """The unique widget name

        This must be unique within a set of widgets.""")

    label = Attribute(
        """The widget label.

        Label may be translated for the request.""")

    hint = Attribute(
        """A hint regarding the use of the widget.

        Hints are traditionally rendered using tooltips in GUIs, but may be
        rendered differently depending on the UI implementation.

        Hint may be translated for the request.""")

    visible = Attribute(
        """A flag indicating whether or not the widget is visible.""")

    def setRenderedValue(value):
        """Set the value to be rendered by the widget.

        Calling this method will override any values provided by the user.

        For input widgets (`IInputWidget` implementations), calling
        this sets the value that will be rendered even if there is
        already user input.

        """

    def setPrefix(prefix):
        """Set the name prefix used for the widget

        The widget name is used to identify the widget's data within
        input data.  For example, for HTTP forms, the widget name is
        used for the form key.

        It is acceptable to *reset* the prefix: set it once to read
        values from the request, and again to redraw with a different
        prefix but maintained state.
                        
        """

class IInputWidget(IWidget):
    """A widget for editing a field value."""

    required = Bool(
        title=u"Required",
        description=u"""If True, widget should be displayed as requiring input.

        By default, this value is the field's 'required' attribute. This
        field can be set to False for widgets that always provide input (e.g.
        a checkbox) to avoid unnecessary 'required' UI notations.
        """)

    def getInputValue():
        """Return value suitable for the widget's field.

        The widget must return a value that can be legally assigned to
        its bound field or otherwise raise ``WidgetInputError``.

        The return value is not affected by `setRenderedValue()`.
        """

    def applyChanges(content):
        """Validate the user input data and apply it to the content.

        Return a boolean indicating whether a change was actually applied.

        This raises an error if there is no user input.
        """

    def hasInput():
        """Returns ``True`` if the widget has input.

        Input is used by the widget to calculate an 'input value', which is
        a value that can be legally assigned to a field.

        Note that the widget may return ``True``, indicating it has input, but
        still be unable to return a value from `getInputValue`. Use
        `hasValidInput` to determine whether or not `getInputValue` will return
        a valid value.

        A widget that does not have input should generally not be used
        to update its bound field.  Values set using
        `setRenderedValue()` do not count as user input.

        A widget that has been rendered into a form which has been
        submitted must report that it has input.  If the form
        containing the widget has not been submitted, the widget
        shall report that it has no input.

        """

    def hasValidInput():
        """Returns ``True`` is the widget has valid input.

        This method is similar to `hasInput` but it also confirms that the
        input provided by the user can be converted to a valid field value
        based on the field constraints.
        """

class IDisplayWidget(IWidget):
    """A widget for displaying a field value."""

    required = Bool(
        title=u"Required",
        description=u"""If True, widget should be displayed as requiring input.

        Display widgets should never be required.
        """)

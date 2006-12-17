##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Browser widgets for sequences

$Id: sequencewidget.py 69606 2006-08-17 15:06:37Z regebro $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.i18n import translate
from zope.schema.interfaces import ValidationError

from zope.app import zapi
from zope.app.form.interfaces import IDisplayWidget, IInputWidget
from zope.app.form.interfaces import WidgetInputError, MissingInputError
from zope.app.form import InputWidget
from zope.app.form.browser.widget import BrowserWidget
from zope.app.form.browser.widget import DisplayWidget, renderElement
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.i18n import ZopeMessageFactory as _


class SequenceWidget(BrowserWidget, InputWidget):
    """A widget baseclass for a sequence of fields.

    subwidget  - Optional CustomWidget used to generate widgets for the
                 items in the sequence
    """

    implements(IInputWidget)

    template = ViewPageTemplateFile('sequencewidget.pt')

    _type = tuple

    def __init__(self, context, field, request, subwidget=None):
        super(SequenceWidget, self).__init__(context, request)
        self.subwidget = subwidget

        # The subwidgets are cached in this dict if preserve_widgets is True.
        self._widgets = {}
        self.preserve_widgets = False

    def __call__(self):
        """Render the widget"""
        self._update()
        return self.template()

    def _update(self):
        """Set various attributes for the template"""
        sequence = self._getRenderedValue()
        num_items = len(sequence)
        self.need_add = (not self.context.max_length
                         or num_items < self.context.max_length)
        self.need_delete = num_items and num_items > self.context.min_length
        self.marker = self._getPresenceMarker(num_items)

    def widgets(self):
        """Return a list of widgets to display"""
        sequence = self._getRenderedValue()
        result = []
        for i, value in enumerate(sequence):
            widget = self._getWidget(i)
            widget.setRenderedValue(value)
            result.append(widget)
        return result

    def addButtonLabel(self):
        button_label = _('Add %s')
        button_label = translate(button_label, context=self.request,
                                 default=button_label)
        return button_label % (self.context.title or self.context.__name__)


    def _getWidget(self, i):
        """Return a widget for the i-th number of the sequence.

        Normally this method creates a new widget each time, but when
        the ``preserve_widgets`` attribute is True, it starts caching
        widgets.  We need it so that the errors on the subwidgets
        would appear only if ``getInputValue`` was called.

        ``getInputValue`` on the subwidgets gets called on each
        request that has data.
        """
        if i not in self._widgets:
            field = self.context.value_type
            if self.subwidget is not None:
                widget = self.subwidget(field, self.request)
            else:
                widget = zapi.getMultiAdapter((field, self.request),
                                              IInputWidget)
            widget.setPrefix('%s.%d.' % (self.name, i))
            if not self.preserve_widgets:
                return widget
            self._widgets[i] = widget
        return self._widgets[i]

    def hidden(self):
        """Render the list as hidden fields."""
        # length of sequence info
        sequence = self._getRenderedValue()
        num_items = len(sequence)

        # generate hidden fields for each value
        parts = [self._getPresenceMarker(num_items)]
        for i in range(num_items):
            value = sequence[i]
            widget = self._getWidget(i)
            widget.setRenderedValue(value)
            parts.append(widget.hidden())
        return "\n".join(parts)

    def _getRenderedValue(self):
        """Returns a sequence from the request or _data"""
        if self._renderedValueSet():
            sequence = list(self._data)
        elif self.hasInput():
            sequence = self._generateSequence()
        elif self.context.default is not None:
            sequence = self.context.default
        else:
            sequence = []
        # ensure minimum number of items in the form
        while len(sequence) < self.context.min_length:
            # Shouldn't this use self.field.value_type.missing_value,
            # instead of None?
            sequence.append(None)
        return sequence

    def _getPresenceMarker(self, count=0):
        return ('<input type="hidden" name="%s.count" value="%d" />'
                % (self.name, count))

    def getInputValue(self):
        """Return converted and validated widget data.

        If there is no user input and the field is required, then a
        ``MissingInputError`` will be raised.

        If there is no user input and the field is not required, then
        the field default value will be returned.

        A ``WidgetInputError`` is raised in the case of one or more
        errors encountered, inputting, converting, or validating the data.
        """
        if self.hasInput():
            self.preserve_widgets = True
            sequence = self._type(self._generateSequence())
            if sequence != self.context.missing_value:
                # catch and set field errors to ``_error`` attribute
                try:
                    self.context.validate(sequence)
                except WidgetInputError, error:
                    self._error = error
                    raise self._error
                except ValidationError, error:
                    self._error = WidgetInputError(
                        self.context.__name__, self.label, error)
                    raise self._error
            elif self.context.required:
                raise MissingInputError(self.context.__name__,
                                        self.context.title)
            return sequence
        raise MissingInputError(self.context.__name__, self.context.title)

    # TODO: applyChanges isn't reporting "change" correctly (we're
    # re-generating the sequence with every edit, and need to be smarter)
    def applyChanges(self, content):
        field = self.context
        value = self.getInputValue()
        change = field.query(content, self) != value
        if change:
            field.set(content, value)
        return change

    def hasInput(self):
        """Is there input data for the field

        Return ``True`` if there is data and ``False`` otherwise.
        """
        return (self.name + ".count") in self.request.form

    def _generateSequence(self):
        """Extract the values of the subwidgets from the request.

        Returns a list of values.

        This can only be called if self.hasInput() returns true.
        """
        if self.context.value_type is None:
            # Why would this ever happen?
            return []
        # the marker field tells how many individual items were
        # included in the input; we check for exactly that many input
        # widgets
        try:
            count = int(self.request.form[self.name + ".count"])
        except ValueError:
            # could not convert to int; the input was not generated
            # from the widget as implemented here
            raise WidgetInputError(self.context.__name__, self.context.title)

        # pre-populate
        sequence = [None] * count

        # now look through the request for interesting values
        # in reverse so that we can remove items as we go
        removing = self.name + ".remove" in self.request.form
        for i in reversed(range(count)):
            widget = self._getWidget(i)
            if widget.hasValidInput():
                # catch and set sequence widget errors to ``_error`` attribute
                try:
                    sequence[i] = widget.getInputValue()
                except WidgetInputError, error:
                    self._error = error
                    raise self._error

            remove_key = "%s.remove_%d" % (self.name, i)
            if remove_key in self.request.form and removing:
                del sequence[i]

        # add an entry to the list if the add button has been pressed
        if self.name + ".add" in self.request.form:
            # Should this be using self.context.value_type.missing_value
            # instead of None?
            sequence.append(None)

        return sequence


class TupleSequenceWidget(SequenceWidget):
    _type = tuple


class ListSequenceWidget(SequenceWidget):
    _type = list


# Basic display widget

class SequenceDisplayWidget(DisplayWidget):

    _missingValueMessage = _("sequence-value-not-provided",
                             u"(no value available)")

    _emptySequenceMessage = _("sequence-value-is-empty",
                              u"(no values)")

    tag = "ol"
    itemTag = "li"
    cssClass = "sequenceWidget"
    extra = ""

    def __init__(self, context, field, request, subwidget=None):
        super(SequenceDisplayWidget, self).__init__(context, request)
        self.subwidget = subwidget

    def __call__(self):
        # get the data to display:
        if self._renderedValueSet():
            data = self._data
        else:
            data = self.context.get(self.context.context)

        # deal with special cases:
        if data == self.context.missing_value:
            return translate(self._missingValueMessage, self.request)
        data = list(data)
        if not data:
            return translate(self._emptySequenceMessage, self.request)

        parts = []
        for i, item in enumerate(data):
            widget = self._getWidget(i)
            widget.setRenderedValue(item)
            s = widget()
            if self.itemTag:
                s = "<%s>%s</%s>" % (self.itemTag, s, self.itemTag)
            parts.append(s)
        contents = "\n".join(parts)
        if self.tag:
            contents = "\n%s\n" % contents
            contents = renderElement(self.tag,
                                     cssClass=self.cssClass,
                                     extra=self.extra,
                                     contents=contents)
        return contents

    def _getWidget(self, i):
        field = self.context.value_type
        if self.subwidget is not None:
            widget = self.subwidget(field, self.request)
        else:
            widget = zapi.getMultiAdapter(
                (field, self.request), IDisplayWidget)
        widget.setPrefix('%s.%d.' % (self.name, i))
        return widget

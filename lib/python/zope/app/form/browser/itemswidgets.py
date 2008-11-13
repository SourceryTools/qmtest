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
"""Browser widgets for items

$Id: itemswidgets.py 77294 2007-07-02 09:52:32Z mgedmin $
"""
__docformat__ = 'restructuredtext'
import sets
from xml.sax.saxutils import escape

from zope import component
from zope.interface import implements
from zope.i18n import translate
from zope.schema.interfaces import ValidationError, InvalidValue
from zope.schema.interfaces import ConstraintNotSatisfied, ITitledTokenizedTerm

from zope.app.form.browser.widget import SimpleInputWidget, renderElement
from zope.app.form.interfaces import IInputWidget, IDisplayWidget
from zope.app.form.interfaces import ConversionError
from zope.app.form.browser.i18n import _
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile


# For choices, we want to make the widget a view of the field and vocabulary.

def ChoiceDisplayWidget(field, request):
    return component.getMultiAdapter((field, field.vocabulary, request),
                                     IDisplayWidget)

def ChoiceInputWidget(field, request):
    return component.getMultiAdapter((field, field.vocabulary, request),
                                     IInputWidget)

# for collections, we want to make the widget a view of the field and the
# value_type.  If the value_type is None we may fall over.  We may
# not be able to do any better than that.

def CollectionDisplayWidget(field, request):
    return component.getMultiAdapter((field, field.value_type, request),
                                     IDisplayWidget)

def CollectionInputWidget(field, request):
    return component.getMultiAdapter((field, field.value_type, request),
                                     IInputWidget)

# for collections of choices, we want to make the widget a view of the field,
# the value type, and the vocabulary.

def ChoiceCollectionDisplayWidget(field, value_type, request):
    return component.getMultiAdapter((field, value_type.vocabulary, request),
                                     IDisplayWidget)

def ChoiceCollectionInputWidget(field, value_type, request):
    return component.getMultiAdapter((field, value_type.vocabulary, request),
                                     IInputWidget)

class TranslationHook(object):
    """A mixin class that provides the translation capabilities."""

    def translate(self, msgid):
        return translate(msgid, context=self.request, default=msgid)

class ItemsWidgetBase(TranslationHook, SimpleInputWidget):
    """Convenience base class for widgets displaying items/choices."""

    extra = ""

    def __init__(self, field, vocabulary, request):
        """Initialize the widget."""
        # only allow this to happen for a bound field
        assert field.context is not None
        self.vocabulary = vocabulary
        super(ItemsWidgetBase, self).__init__(field, request)
        self.empty_marker_name = self.name + "-empty-marker"

    def setPrefix(self, prefix):
        """Set the prefixes for the field names of the form."""
        super(ItemsWidgetBase, self).setPrefix(prefix)
        # names for other information from the form
        self.empty_marker_name = self.name + "-empty-marker"

    def __call__(self):
        """Render the widget to HTML."""
        raise NotImplementedError(
            "__call__() must be implemented by a subclass; use _getFormValue()"
            )

    def textForValue(self, term):
        """Extract a string from the `term`.

        The `term` must be a vocabulary tokenized term.

        This can be overridden to support more complex `term`
        objects. The token is returned here since it's the only thing
        known to be a string, or str()able.

        """
        titled = ITitledTokenizedTerm(term, None)
        if titled is None:
            return term.token
        return self.translate(titled.title)

    def convertTokensToValues(self, tokens):
        """Convert term tokens to the terms themselves.

        Tokens are used in the HTML form to represent terms. This method takes
        the form tokens and converts them back to terms.
        """
        values = []
        for token in tokens:
            try:
                term = self.vocabulary.getTermByToken(token)
            except LookupError, error:
                raise InvalidValue("token %r not found in vocabulary" % token)
            else:
                values.append(term.value)
        return values

    def _emptyMarker(self):
        """Mark the form so that empty selections are also valid."""
        return '<input name="%s" type="hidden" value="1" />' % (
            self.empty_marker_name)

    def hasInput(self):
        """Check whether we have any input."""
        return (self.name in self.request.form or
                self.empty_marker_name in self.request.form)

    def _toFieldValue(self, input):
        """See `SimpleInputWidget`"""
        raise NotImplementedError(
            "_toFieldValue(input) must be implemented by a subclass\n"
            "It may be inherited from the mix-in classes SingleDataHelper\n"
            "or MultiDataHelper")


class SingleDataHelper(object):
    """Mix-in helper class for getting the term from the HTML form.

    This is used when we expect a single input, i.e. the Choice field.
    """

    def _toFieldValue(self, input):
        if input:
            try:
                return self.convertTokensToValues([input])[0]
            except InvalidValue, e:
                raise ConversionError("Invalid value", e)
        else:
            return self.context.missing_value

    def hidden(self):
        #XXX: _getFormValue() should return a string value that can be
        #     used in a HTML form, but it doesn't. When
        #     http://www.zope.org/Collectors/Zope3-dev/584 gets fixed
        #     this hack should be reverted.
        #     -- Bjorn Tillenius, 2006-04-12
        value = self._getFormValue()
        if value == self._missing:
            form_value = ''
        else:
            form_value = self.vocabulary.getTerm(value).token
        return renderElement(u'input',
                             type='hidden',
                             name=self.name,
                             id=self.name,
                             value=form_value,
                             cssClass=self.cssClass,
                             extra=self.extra)


class MultiDataHelper(object):
    """Mix-in helper class for getting the term from the HTML form.

    This is used when we expect a multiple inputs, i.e. Sequence fields with a
    Choice field as value_type.
    """

    def _toFieldValue(self, input):
        """See SimpleInputWidget"""
        if input is None:
            input = []
        elif not isinstance(input, list):
            input = [input]
        try:
            values = self.convertTokensToValues(input)
        except InvalidValue, e:
            raise ConversionError("Invalid value", e)

        # All AbstractCollection fields have a `_type` attribute specifying
        # the type of collection. Use it to generate the correct type,
        # otherwise return a list.  TODO: this breaks encapsulation.
        if hasattr(self.context, '_type'):
            _type = self.context._type
            if isinstance(_type, tuple):
                _type = _type[0]
            return _type(values)
        else:
            return values


    def _getDefault(self):
        # Return the default value for this widget;
        # may be overridden by subclasses.
        val = self.context.default
        if val is None:
            val = []
        return val


## Display-Widgets for Items-related fields.

class ItemDisplayWidget(SingleDataHelper, ItemsWidgetBase):
    """Simple single-selection display that can be used in many cases."""

    def __init__(self, *args, **kw):
        ItemsWidgetBase.__init__(self, *args, **kw)
        self.required = False

    _messageNoValue = _("item-missing-single-value-for-display", "")

    def __call__(self):
        """See IBrowserWidget."""
        value = self._getFormValue()
        if not value:
            return self.translate(self._messageNoValue)
        else:
            term = self.vocabulary.getTerm(value)
            return self.textForValue(term)


class ItemsMultiDisplayWidget(MultiDataHelper, ItemsWidgetBase):
    """Displays a sequence of items."""

    def __init__(self, *args, **kw):
        ItemsWidgetBase.__init__(self, *args, **kw)
        self.required = False

    _messageNoValue = _("vocabulary-missing-multiple-value-for-display", "")

    itemTag = 'li'
    tag = 'ol'

    def __call__(self):
        """See IBrowserWidget."""
        value = self._getFormValue()
        if value:
            rendered_items = self.renderItems(value)
            return renderElement(self.tag,
                                 id=self.name,
                                 cssClass=self.cssClass,
                                 contents="\n".join(rendered_items),
                                 extra=self.extra)
        else:
            return self.translate(self._messageNoValue)

    def renderItems(self, value):
        """Render items of sequence."""
        items = []
        cssClass = self.cssClass or ''
        if cssClass:
            cssClass += "-item"
        tag = self.itemTag
        for item in value:
            term = self.vocabulary.getTerm(item)
            items.append(renderElement(
                tag,
                cssClass=cssClass,
                contents=escape(self.textForValue(term))))
        return items

class ListDisplayWidget(ItemsMultiDisplayWidget):
    """Display widget for ordered multi-selection fields.

    This can be used for both Sequence, List, and Tuple fields.
    """
    tag = 'ol'

class SetDisplayWidget(ItemsMultiDisplayWidget):
    """Display widget for unordered multi-selection fields.

    This can be used for both Set field.
    """
    tag = 'ul'


## Edit-Widgets for Items-related fields.

class ItemsEditWidgetBase(SingleDataHelper, ItemsWidgetBase):
    """Widget Base for rendering item-related fields.

    These widgets work with Choice fields and Sequence fields that have Choice
    as value_type.
    """
    implements(IInputWidget)

    size = 5
    tag = 'select'

    _displayItemForMissingValue = True

    def __init__(self, field, vocabulary, request):
        """Initialize the widget."""
        super(ItemsEditWidgetBase, self).__init__(field, vocabulary, request)

    def setPrefix(self, prefix):
        """Set the prefix of the input name.

        Once we set the prefix of input field, we use the name of the input
        field and the postfix '-query' for the associated query view.
        """
        super(ItemsEditWidgetBase, self).setPrefix(prefix)


    def __call__(self):
        """See IBrowserWidget."""
        value = self._getFormValue()
        contents = []
        have_results = False

        contents.append(self._div('value', self.renderValue(value)))
        contents.append(self._emptyMarker())

        return self._div(self.cssClass, "\n".join(contents))


    def _div(self, cssClass, contents, **kw):
        """Render a simple div tag."""
        if contents:
            return renderElement('div',
                                 cssClass=cssClass,
                                 contents="\n%s\n" % contents,
                                 **kw)
        return ""


    def renderItemsWithValues(self, values):
        """Render the list of possible values, with those found in
        `values` being marked as selected."""

        cssClass = self.cssClass

        # multiple items with the same value are not allowed from a
        # vocabulary, so that need not be considered here
        rendered_items = []
        count = 0

        # Handle case of missing value
        missing = self._toFormValue(self.context.missing_value)

        if self._displayItemForMissingValue and not self.context.required:
            if missing in values:
                render = self.renderSelectedItem
            else:
                render = self.renderItem

            missing_item = render(count,
                self.translate(self._messageNoValue),
                missing,
                self.name,
                cssClass)
            rendered_items.append(missing_item)
            count += 1

        # Render normal values
        for term in self.vocabulary:
            item_text = self.textForValue(term)

            if term.value in values:
                render = self.renderSelectedItem
            else:
                render = self.renderItem

            rendered_item = render(count,
                item_text,
                term.token,
                self.name,
                cssClass)

            rendered_items.append(rendered_item)
            count += 1

        return rendered_items

    def renderItem(self, index, text, value, name, cssClass):
        """Render an item for a particular `value`."""
        return renderElement('option',
                             contents=escape(text),
                             value=value,
                             cssClass=cssClass)

    def renderSelectedItem(self, index, text, value, name, cssClass):
        """Render an item for a particular `value` that is selected."""
        return renderElement('option',
                             contents=escape(text),
                             value=value,
                             cssClass=cssClass,
                             selected='selected')


class SelectWidget(ItemsEditWidgetBase):
    """Provide a selection list for the item."""

    _messageNoValue = _("vocabulary-missing-single-value-for-edit",
                        "(no value)")

    def renderValue(self, value):
        rendered_items = self.renderItems(value)
        contents = "\n%s\n" %"\n".join(rendered_items)
        return renderElement('select',
                             name=self.name,
                             id=self.name,
                             contents=contents,
                             size=self.size,
                             extra=self.extra)

    def renderItems(self, value):
        return self.renderItemsWithValues([value])


class DropdownWidget(SelectWidget):
    """Variation of the SelectWidget that uses a drop-down list."""
    size = 1


class RadioWidget(SelectWidget):
    """Radio widget for single item choices.

    This widget can be used when the number of selections is going
    to be small.
    """
    orientation = "vertical"

    _messageNoValue = _("vocabulary-missing-single-value-for-edit",
                        "(no value)")

    def renderItem(self, index, text, value, name, cssClass):
        """Render an item of the list."""
        return self._renderItem(index, text, value, name, cssClass)

    def renderSelectedItem(self, index, text, value, name, cssClass):
        """Render a selected item of the list."""
        return self._renderItem(index, text, value, name, cssClass,
                                checked=True)

    def _renderItem(self, index, text, value, name, cssClass, checked=False):
        kw = {}
        if checked:
            kw['checked'] = 'checked'
        id = '%s.%s' % (name, index)
        elem = renderElement(u'input',
                             value=value,
                             name=name,
                             id=id,
                             cssClass=cssClass,
                             type='radio',
                             **kw)
        return renderElement(u'label',
                             contents='%s&nbsp;%s' % (elem, text),
                             **{'for': id})

    def renderValue(self, value):
        rendered_items = self.renderItems(value)
        if self.orientation == 'horizontal':
            return "&nbsp;&nbsp;".join(rendered_items)
        else:
            return "<br />".join(rendered_items)


class ItemsMultiEditWidgetBase(MultiDataHelper, ItemsEditWidgetBase):
    """Items widget supporting multiple selections."""

    _messageNoValue = _("vocabulary-missing-multiple-value-for-edit",
                        "(no values)")
    _displayItemForMissingValue = False

    def renderItems(self, value):
        if value == self.context.missing_value:
            values = []
        else:
            values = list(value)
        return self.renderItemsWithValues(values)

    def renderValue(self, value):
        # All we really add here is the ':list' in the name argument
        # and mutliple='multiple' to renderElement().
        rendered_items = self.renderItems(value)
        return renderElement(self.tag,
                             name=self.name + ':list',
                             id=self.name,
                             multiple='multiple',
                             size=self.size,
                             contents="\n".join(rendered_items),
                             extra=self.extra)

    def hidden(self):
        items = []
        for item in self._getFormValue():
            items.append(
                renderElement(u'input',
                              type='hidden',
                              name=self.name+':list',
                              id=self.name,
                              value=self.vocabulary.getTerm(item).token,
                              cssClass=self.cssClass,
                              extra=self.extra))
        return '\n'.join(items)


class MultiSelectWidget(ItemsMultiEditWidgetBase):
    """Provide a selection list for the list to be selected."""


class MultiSelectSetWidget(MultiSelectWidget):
    """Provide a selection list for the set to be selected."""

    def _toFieldValue(self, input):
        value = super(MultiSelectSetWidget, self)._toFieldValue(input)
        if isinstance(value, list):
            value = sets.Set(value)
        return value


class MultiSelectFrozenSetWidget(MultiSelectWidget):
    """Provide a selection list for the set to be selected."""

    def _toFieldValue(self, input):
        value = super(MultiSelectFrozenSetWidget, self)._toFieldValue(input)
        if isinstance(value, list):
            value = frozenset(value)
        return value

class OrderedMultiSelectWidget(ItemsMultiEditWidgetBase):
    """A multi-selection widget with ordering support."""

    template = ViewPageTemplateFile('orderedSelectionList.pt')

    def choices(self):
        """Return a set of tuples (text, value) that are available."""
        # Not all content objects must necessarily support the attributes
        if hasattr(self.context.context, self.context.__name__):
            available_values = self.context.get(self.context.context)
        else:
            available_values = []
        return [{'text': self.textForValue(term), 'value': term.token}
                for term in self.vocabulary
                if term.value not in available_values]

    def selected(self):
        """Return a list of tuples (text, value) that are selected."""
        # Get form values
        values = self._getFormValue()
        # Not all content objects must necessarily support the attributes
        if hasattr(self.context.context, self.context.__name__):
            # merge in values from content
            for value in self.context.get(self.context.context):
                if value not in values:
                    values.append(value)

        terms = [self.vocabulary.getTerm(value)
                 for value in values]
        return [{'text': self.textForValue(term), 'value': term.token}
                for term in terms]

    def __call__(self):
        return self.template()


class MultiCheckBoxWidget(ItemsMultiEditWidgetBase):
    """Provide a list of checkboxes that provide the choice for the list."""

    orientation = "vertical"

    _joinButtonToMessageTemplate = u"%s&nbsp;%s"

    def renderValue(self, value):
        rendered_items = self.renderItems(value)
        if self.orientation == 'horizontal':
            return "&nbsp;&nbsp;".join(rendered_items)
        else:
            return "<br />".join(rendered_items)

    def renderItem(self, index, text, value, name, cssClass):
        """Render an item of the list."""
        return self._renderItem(index, text, value, name, cssClass)

    def renderSelectedItem(self, index, text, value, name, cssClass):
        """Render a selected item of the list."""
        return self._renderItem(index, text, value, name, cssClass,
                                checked=True)

    def _renderItem(self, index, text, value, name, cssClass, checked=False):
        kw = {}
        if checked:
            kw['checked'] = 'checked'
        id = '%s.%s' % (name, index)
        elem = renderElement('input',
                             type="checkbox",
                             cssClass=cssClass,
                             name=name,
                             id=id,
                             value=value,
                             **kw)
        contents = self._joinButtonToMessageTemplate % (elem, text)
        return renderElement(u'label',
                             contents=contents,
                             **{'for': id})


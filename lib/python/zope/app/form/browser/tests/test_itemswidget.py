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
"""Select Widget Tests

$Id: test_itemswidget.py 77294 2007-07-02 09:52:32Z mgedmin $
"""
import sets
import unittest

from zope.interface import Interface, implements
from zope.schema import Choice, List, Set, TextLine, FrozenSet
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.publisher.browser import TestRequest

from zope.app.form.interfaces import ConversionError
from zope.app.form.browser.itemswidgets import ItemsWidgetBase
from zope.app.form.browser.itemswidgets import ItemDisplayWidget
from zope.app.form.browser.itemswidgets import ItemsMultiDisplayWidget
from zope.app.form.browser.itemswidgets import ListDisplayWidget
from zope.app.form.browser.itemswidgets import SetDisplayWidget
from zope.app.form.browser.itemswidgets import ItemsEditWidgetBase
from zope.app.form.browser.itemswidgets import SelectWidget, DropdownWidget
from zope.app.form.browser.itemswidgets import RadioWidget
from zope.app.form.browser.itemswidgets import ItemsMultiEditWidgetBase
from zope.app.form.browser.itemswidgets import MultiSelectWidget
from zope.app.form.browser.itemswidgets import OrderedMultiSelectWidget
from zope.app.form.browser.itemswidgets import MultiCheckBoxWidget
from zope.app.form.browser.tests.support import VerifyResults
from zope.app.testing.placelesssetup import PlacelessSetup

vocab = SimpleVocabulary(
    [SimpleTerm(value, token, title) for value, token, title in (
        ('one', 'token1', 'One'),
        ('two', 'token2', 'Two'),
        ('three', 'token3', 'Three'))])

class ICollector(Interface):
    choice = Choice(
        title=u"Number",
        description=u"The Number",
        # we want to be able to distinguish between tokens and values
        vocabulary=vocab,
        required=True)

    numbers = List(
        title=u"Numbers",
        description=u"The Numbers",
        value_type=choice,
        required=False)

    letters = Set(
        title=u"Letters",
        description=u"The Letters",
        value_type=choice,
        required=False)

    frozenLetters = FrozenSet(
        title=u"Frozen Letters",
        description=u"The Frozen Letters",
        value_type=choice,
        required=False)


class Collector(object):
    implements(ICollector)

    def __init__(self, numbers=None):
        self.numbers = numbers or []


class ItemsWidgetBaseTest(VerifyResults, PlacelessSetup, unittest.TestCase):

    _widget = ItemsWidgetBase
    _field = ICollector.get('choice')
    _vocabulary = _field.vocabulary

    def _makeWidget(self, form=None, nums=None):
        request = TestRequest(form=form or {})
        collector = Collector(nums)
        bound = self._field.bind(collector)
        return self._widget(bound, self._vocabulary, request)

    def test_setPrefix(self):
        widget = self._makeWidget()
        name = self._field.getName()
        # Default prefix
        self.assertEqual(widget._prefix, 'field.')
        self.assertEqual(widget.name, 'field.%s' %name)
        self.assertEqual(widget.empty_marker_name,
                         'field.%s-empty-marker' %name)
        # Declaring custom prefix
        widget.setPrefix('foo')
        self.assertEqual(widget._prefix, 'foo.')
        self.assertEqual(widget.name, 'foo.%s' %name)
        self.assertEqual(widget.empty_marker_name,
                         'foo.%s-empty-marker' %name)
        # Declaring empty prefix
        widget.setPrefix('')
        self.assertEqual(widget._prefix, '')
        self.assertEqual(widget.name, name)
        self.assertEqual(widget.empty_marker_name,
                         '%s-empty-marker' %name)

    def test_convertTokensToValues(self):
        widget = self._makeWidget()
        self.assertEqual(widget.convertTokensToValues(['token1', 'token2']),
                         ['one', 'two'])


class ItemDisplayWidgetTest(ItemsWidgetBaseTest):

    _widget = ItemDisplayWidget

    def test_setVocabulary(self):
        widget = self._makeWidget()
        self.assert_(widget.vocabulary is not None)
        self.assertEqual(widget.vocabulary, self._field.vocabulary)

    def test__call__(self):
        widget = self._makeWidget()
        self.assertEqual(widget(), '')
        widget = self._makeWidget(form={'field.choice': 'token1'})
        self.assertEqual(widget(), 'One')

    def test_not_required(self):
        self.failIf(self._makeWidget().required)


class ItemsMultiDisplayWidgetTest(ItemsWidgetBaseTest):

    _widget = ItemsMultiDisplayWidget
    _field = ICollector.get('numbers')
    _vocabulary = _field.value_type.vocabulary
    _tag = 'ol'

    def test__call__(self):
        widget = self._makeWidget()
        self.assertEqual(widget(), '')
        widget = self._makeWidget(form={'field.numbers': ['token1', 'token2']})
        self.assertEqual(
            widget(),
            '<%s id="field.numbers" >'
            '<li>One</li>\n<li>Two</li>'
            '</%s>' %(self._tag, self._tag))

    def test_renderItems(self):
        widget = self._makeWidget()
        self.assertEqual(
            widget.renderItems(['one', 'two']),
            [u'<li>One</li>', u'<li>Two</li>'])
        self.assertRaises(LookupError, widget.renderItems, 'one')
        self.assertRaises(TypeError, widget.renderItems, 1)


    def test_not_required(self):
        numbers = List(value_type=ICollector['choice']).bind(Collector(None))
        request = TestRequest()
        widget = self._widget(numbers, self._vocabulary, request)
        self.failIf(widget.required)


class ListDisplayWidgetTest(ItemsMultiDisplayWidgetTest):
    _widget = ListDisplayWidget
    _tag = 'ol'


class SetDisplayWidgetTest(ItemsMultiDisplayWidgetTest):
    _widget = SetDisplayWidget
    _tag = 'ul'


class ItemsEditWidgetBaseTest(ItemsWidgetBaseTest):

    _widget = ItemsEditWidgetBase

    def test_div(self):
        widget = self._makeWidget()
        self.assertEqual(widget._div('', ''), '')
        self.assertEqual(widget._div('foo', ''), '')
        self.assertEqual(widget._div('', 'bar'), '<div>\nbar\n</div>')
        self.assertEqual(widget._div('foo', 'bar'),
                         '<div class="foo">\nbar\n</div>')
        self.assertEqual(widget._div('foo', 'bar', style='blah'),
                         '<div class="foo" style="blah">\nbar\n</div>')

    def test_renderItem(self):
        widget = self._makeWidget()
        self.assertEqual(widget.renderItem('', 'Foo', 'foo', '', None),
                         '<option value="foo">Foo</option>')
        self.assertEqual(widget.renderItem('', 'Foo', 'foo', '', 'klass'),
                         '<option class="klass" value="foo">Foo</option>')

    def test_renderSelectedItem(self):
        widget = self._makeWidget()
        self.verifyResult(
          widget.renderSelectedItem('', 'Foo', 'foo', '', None),
          ['<option', 'value="foo"', 'selected="selected"', '>Foo</option>'])
        self.verifyResult(
          widget.renderSelectedItem('', 'Foo', 'foo', '', 'klass'),
          ['<option', 'class="klass"', 'value="foo"', 'selected="selected"',
           '>Foo</option>'])

    def test_renderItemsWithValues(self):
        widget = self._makeWidget()
        self.assertEqual(
            widget.renderItemsWithValues(['one', 'two']),
            [u'<option selected="selected" value="token1">One</option>',
             u'<option selected="selected" value="token2">Two</option>',
             u'<option value="token3">Three</option>'])
        self.assertEqual(
            widget.renderItemsWithValues([]),
            [u'<option value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])

# This test is disabled because it tests for the presense of a missfeature,
# which has been removed.  Did someone actually *want* this?
##     def test_error(self):
##         widget = self._makeWidget(form={'field.choice': 'ten'})
##         widget.setPrefix('field.')
##         widget._getFormValue()
##         self.assert_(isinstance(widget._error, ConversionError))

    def test_hidden(self):
        widget = self._makeWidget(form={'field.choice': 'token2'})
        widget.setPrefix('field.')
        widget.context.required = False
        self.verifyResult(
            widget.hidden(),
            ['<input', 'type="hidden"', 'value="token2"', 'id="field.choice"',
             'name="field.choice"'])

class SelectWidgetTest(ItemsEditWidgetBaseTest):

    _widget = SelectWidget
    _size = 5

    def test__call__(self):
        widget = self._makeWidget(form={'field.choice': 'token1'})
        widget.setPrefix('field.')
        widget.context.required = False
        self.assertEqual(
            widget(),
            '<div>\n'
            '<div class="value">\n'
            '<select id="field.choice" name="field.choice" size="%i" >\n'
            '<option value="">(no value)</option>\n'
            '<option selected="selected" value="token1">One</option>\n'
            '<option value="token2">Two</option>\n'
            '<option value="token3">Three</option>\n'
            '</select>\n</div>\n'
            '<input name="field.choice-empty-marker" '
            'type="hidden" value="1" />\n</div>' %self._size)

    def test_renderValue(self):
        widget = self._makeWidget()
        widget.setPrefix('field.')
        self.assertEqual(
            widget.renderValue('one'),
            '<select id="field.choice" name="field.choice" size="%i" >\n'
            '<option selected="selected" value="token1">One</option>\n'
            '<option value="token2">Two</option>\n'
            '<option value="token3">Three</option>\n'
            '</select>' %self._size)

    def test_renderItems(self):
        widget = self._makeWidget()
        widget.setPrefix('field.')
        self.assertEqual(
            widget.renderItems('one'),
            [u'<option selected="selected" value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])
        self.assertEqual(
            widget.renderItems('two'),
            [u'<option value="token1">One</option>',
             u'<option selected="selected" value="token2">Two</option>',
             u'<option value="token3">Three</option>'])
        self.assertEqual(
            widget.renderItems(None),
            [u'<option value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])

    def test_renderItems_notRequired(self):
        widget = self._makeWidget()
        widget.setPrefix('field.')
        widget.context.required = False
        self.assertEqual(
            widget.renderItems([]),
            [u'<option value="">(no value)</option>',
             u'<option value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])

    def test_renderItems_firstItem(self):
        widget = self._makeWidget()
        widget.setPrefix('field.')
        widget.firstItem = True
        self.assertEqual(
            widget.renderItems(widget._toFormValue(widget.context.missing_value)),
            [u'<option value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])


class DropdownWidgetTest(SelectWidgetTest):

    _widget = DropdownWidget
    _size = 1


class RadioWidgetTest(ItemsEditWidgetBaseTest):

    _widget = RadioWidget

    def test_renderItem(self):
        widget = self._makeWidget()
        self.verifyResult(
            widget.renderItem('', 'Foo', 'foo', 'bar', None),
            ['<label', '<input', 'type="radio"', 'name="bar"', 'value="foo"',
             'class="radioType"', '>&nbsp;Foo'])
        self.verifyResult(
            widget.renderItem('bar', 'Foo', 'foo', 'bar', 'klass'),
            ['<input', 'type="radio"', 'name="bar"', 'value="foo"',
             'class="klass radioType"', '>&nbsp;Foo'])

    def test_renderSelectedItem(self):
        widget = self._makeWidget()
        self.verifyResult(
            widget.renderSelectedItem('', 'Foo', 'foo', 'bar', 'klass'),
            ['<label', '<input', 'type="radio"', 'name="bar"', 'value="foo"',
             'checked="checked"', '>&nbsp;Foo'])
        self.verifyResult(
            widget.renderSelectedItem('', 'Foo', 'foo', 'bar', 'klass'),
            ['<label', '<input', 'type="radio"', 'name="bar"', 'value="foo"',
             'class="klass radioType"', 'checked="checked"', '>&nbsp;Foo'])

    def test_renderItemsWithValues(self):
        widget = self._makeWidget()
        items = widget.renderItemsWithValues(['one'])
        values = [('token1','One'), ('token2','Two'), ('token3','Three')]
        for index, item in enumerate(items):
            self.verifyResult(
                item,
                ['<label', '<input', 'class="radioType"', 'name="field.choice"',
                 'id="field.choice.%i' %index, 'type="radio"',
                 'value="%s"' %values[index][0],
                 '&nbsp;%s' %values[index][1]])
        self.verifyResult(items[0], ['checked="checked"'])

    def test_renderItems(self):
        widget = self._makeWidget()
        items = widget.renderItems('one')
        values = [('token1','One'), ('token2','Two'), ('token3','Three')]
        for index, item in enumerate(items):
            self.verifyResult(
                item,
                ['<label', '<input', 'class="radioType"', 'name="field.choice"',
                 'id="field.choice.%i' %index, 'type="radio"',
                 'value="%s"' %values[index][0], '&nbsp;%s' %values[index][1]])
        self.verifyResult(items[0], ['checked="checked"'])

    def test_renderItems_notRequired(self):
        widget = self._makeWidget()
        widget.context.required = False
        items = widget.renderItems([])
        values = [('', '(no value)'),
                  ('token1','One'),
                  ('token2','Two'),
                  ('token3','Three')]
        for index, item in enumerate(items):
            self.verifyResult(
                item,
                ['<label', '<input', 'class="radioType"',
                 'name="field.choice"', 'type="radio"',
                 'value="%s"' %values[index][0], '&nbsp;%s' %values[index][1]])

    def test_renderItems_firstItem(self):
        widget = self._makeWidget()
        items = widget.renderItems(
                widget._toFormValue(widget.context.missing_value))
        values = [('token1','One'), ('token2','Two'), ('token3','Three')]
        for index, item in enumerate(items):
            self.verifyResult(
                item,
                ['<label', '<input', 'class="radioType"',
                 'name="field.choice"', 'id="field.choice.%i"' % index,
                 'type="radio"', 'value="%s"' % values[index][0],
                 '&nbsp;%s' % values[index][1]])

    def test_renderValue(self):
        widget = self._makeWidget()
        self.verifyResult(widget.renderValue(None), ['<br /><label for='])
        widget.orientation = 'horizontal'
        self.verifyResult(widget.renderValue(None),
                          ['&nbsp;&nbsp;<label for='])


class ItemsMultiEditWidgetBaseTest(ItemsEditWidgetBaseTest):

    _widget = ItemsMultiEditWidgetBase
    _field = ICollector.get('numbers')
    _vocabulary = _field.value_type.vocabulary

    def test_renderValue(self):
        widget = self._makeWidget()
        self.verifyResult(
            widget.renderValue(['one', 'two']),
            ['<select', 'multiple="multiple"', 'name="field.numbers:list"',
             'size="5"', '><option', 'selected="selected"', 'value="token1"',
             '>One</option>\n', 'value="token2"', '>Two</option>\n',
             'value="token3"', '>Three</option>', '</select>'])

    def test_renderItemsWithValues(self):
        widget = self._makeWidget()
        self.assertEqual(
            widget.renderItemsWithValues(['one', 'two']),
            [u'<option selected="selected" value="token1">One</option>',
             u'<option selected="selected" value="token2">Two</option>',
             u'<option value="token3">Three</option>'])
        self.assertEqual(
            widget.renderItemsWithValues([]),
            [u'<option value="token1">One</option>',
             u'<option value="token2">Two</option>',
             u'<option value="token3">Three</option>'])

# This test is disabled because it tests for the presense of a missfeature,
# which has been removed.  Did someone actually *want* this?
##     def test_error(self):
##         widget = self._makeWidget(form={'field.numbers': ['ten']})
##         widget.setPrefix('field.')
##         widget._getFormValue()
##         self.assert_(isinstance(widget._error, ConversionError))

    def test_hidden(self):
        widget = self._makeWidget(
            form={'field.numbers': ['two','three']})
        widget.setPrefix('field.')
        widget.context.required = False
        self.verifyResult(
            widget.hidden(),
            ['<input', 'type="hidden"', 'value="token2"', 'id="field.numbers"',
             'name="field.numbers:list"', 'value="token3"'])

    def test_getInputValue(self):
        widget = self._makeWidget(form={'field.numbers': ['token2', 'token3']})
        widget.setPrefix('field.')
        self.assertEqual(widget.getInputValue(), ['two', 'three'])

        self._field = ICollector.get('letters')
        widget = self._makeWidget(form={'field.letters-empty-marker': '1'})
        widget.setPrefix('field.')
        self.assertEqual(widget.getInputValue(), sets.Set())
        widget = self._makeWidget(form={'field.letters': ['token2', 'token3']})
        widget.setPrefix('field.')
        self.assertEqual(widget.getInputValue(), sets.Set(['two', 'three']))

        self._field = ICollector.get('frozenLetters')
        widget = self._makeWidget(form={'field.frozenLetters-empty-marker':
                                        '1'})
        widget.setPrefix('field.')
        field_value = widget.getInputValue()
        self.assertEqual(field_value, frozenset())
        widget = self._makeWidget(form={'field.frozenLetters':
                                        ['token2', 'token3']})
        widget.setPrefix('field.')
        field_value = widget.getInputValue()
        self.assertEqual(field_value, frozenset(['two', 'three']))
        self.assert_(isinstance(field_value, frozenset))


class MultiSelectWidgetTest(ItemsMultiEditWidgetBaseTest):

    _widget = MultiSelectWidget


class OrderedMultiSelectWidgetTest(ItemsMultiEditWidgetBaseTest):

    _widget = OrderedMultiSelectWidget

    def test_choices(self):
        widget = self._makeWidget()
        choices = [choice['text'] for choice in widget.choices()]
        choices.sort()
        self.assertEqual(choices, ['One', 'Three', 'Two'])

    def test_selected(self):
        widget = self._makeWidget(nums=['one'])
        widget._data = ['two']
        selected = [select['text'] for select in widget.selected()]
        selected.sort()
        self.assertEqual(selected, ['One', 'Two'])
        widget._data = ['one']
        selected = [select['text'] for select in widget.selected()]
        selected.sort()
        self.assertEqual(selected, ['One'])


class MultiCheckBoxWidgetTest(ItemsMultiEditWidgetBaseTest):

    _widget = MultiCheckBoxWidget

    def test_renderItem(self):
        widget = self._makeWidget()
        self.verifyResult(
            widget.renderItem('', 'Foo', 'foo', 'bar', None),
            ['<input', 'type="checkbox"', 'name="bar"', 'value="foo"',
             'class="checkboxType"', '>&nbsp;Foo'])
        self.verifyResult(
            widget.renderItem('bar', 'Foo', 'foo', 'bar', 'klass'),
            ['<input', 'type="checkbox"', 'name="bar"', 'value="foo"',
             'class="klass checkboxType"', '>&nbsp;Foo'])

    def test_renderSelectedItem(self):
        widget = self._makeWidget()
        self.verifyResult(
            widget.renderSelectedItem('', 'Foo', 'foo', 'bar', 'klass'),
            ['<input', 'type="checkbox"', 'name="bar"', 'value="foo"',
             'checked="checked"', '>&nbsp;Foo'])
        self.verifyResult(
            widget.renderSelectedItem('', 'Foo', 'foo', 'bar', 'klass'),
            ['<input', 'type="checkbox"', 'name="bar"', 'value="foo"',
             'class="klass checkboxType"', 'checked="checked"', '>&nbsp;Foo'])

    def test_renderValue(self):
        widget = self._makeWidget()
        self.verifyResult(widget.renderValue(None), ['<br /><label for='])
        widget.orientation='horizontal'
        self.verifyResult(widget.renderValue(None),
                          ['&nbsp;&nbsp;<label for='])

    def test_renderItemsWithValues(self):
        widget = self._makeWidget()
        items = widget.renderItemsWithValues(['one'])
        values = [('token1','One'), ('token2','Two'), ('token3','Three')]
        for index, item in enumerate(items):
            self.verifyResult(
                item,
                ['<input', 'class="checkboxType',
                 'id="field.numbers.%i"' %index, 'type="checkbox"',
                 'value="%s"' % values[index][0],
                 '/>&nbsp;%s' % values[index][1]])

        self.verifyResult(items[0], ['checked="checked"'])


def test_suite():
    suite = unittest.makeSuite(ItemDisplayWidgetTest)
    suite.addTest(unittest.makeSuite(ItemsMultiDisplayWidgetTest))
    suite.addTest(unittest.makeSuite(ListDisplayWidgetTest))
    suite.addTest(unittest.makeSuite(SetDisplayWidgetTest))
    suite.addTest(unittest.makeSuite(ItemsEditWidgetBaseTest))
    suite.addTest(unittest.makeSuite(SelectWidgetTest))
    suite.addTest(unittest.makeSuite(DropdownWidgetTest))
    suite.addTest(unittest.makeSuite(RadioWidgetTest))
    suite.addTest(unittest.makeSuite(ItemsMultiEditWidgetBaseTest))
    suite.addTest(unittest.makeSuite(MultiSelectWidgetTest))
    suite.addTest(unittest.makeSuite(OrderedMultiSelectWidgetTest))
    suite.addTest(unittest.makeSuite(MultiCheckBoxWidgetTest))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

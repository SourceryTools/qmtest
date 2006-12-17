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
"""Sequence Field Widget tests.

$Id: test_sequencewidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from zope.schema import Tuple, List, TextLine
from zope.schema.interfaces import ITextLine, ValidationError
from zope.publisher.browser import TestRequest
from zope.interface import Interface, implements
from zope.interface.verify import verifyClass

from zope.app import zapi
from zope.app.testing import ztapi, setup
from zope.app.form.browser import TextWidget, ObjectWidget, DisplayWidget
from zope.app.form.browser import TupleSequenceWidget, ListSequenceWidget
from zope.app.form.browser import SequenceDisplayWidget
from zope.app.form.browser import SequenceWidget
from zope.app.form.interfaces import IDisplayWidget
from zope.app.form.interfaces import IInputWidget, MissingInputError
from zope.app.form.interfaces import IWidgetInputError, WidgetInputError
from zope.app.form.browser.interfaces import IWidgetInputErrorView
from zope.app.form import CustomWidgetFactory
from zope.app.form.browser.exception import WidgetInputErrorView

from zope.app.form.browser.tests.support import VerifyResults
from zope.app.form.browser.tests.test_browserwidget import BrowserWidgetTest


class SequenceWidgetTestHelper(object):

    def setUpContent(self, desc=u'', title=u'Foo Title'):
        class ITestContent(Interface):
            foo = self._FieldFactory(
                    title=title,
                    description=desc,
                    )
        class TestObject(object):
            implements(ITestContent)

        self.content = TestObject()
        self.field = ITestContent['foo'].bind(self.content)
        self.request = TestRequest(HTTP_ACCEPT_LANGUAGE='pl')
        self.request.form['field.foo'] = u'Foo Value'
        self._widget = self._WidgetFactory(
            self.field, self.field.value_type, self.request)

    def setUp(self):
        setup.placefulSetUp()
        self.setUpContent()

    def _FieldFactory(self, **kw):
        kw.update({
            '__name__': u'foo', 
            'value_type': TextLine(__name__=u'bar')})
        return Tuple(**kw)


class SequenceWidgetTest(SequenceWidgetTestHelper, BrowserWidgetTest):
    """Documents and tests the tuple and list (sequence) widgets.
    
        >>> verifyClass(IInputWidget, TupleSequenceWidget)
        True
        >>> verifyClass(IInputWidget, ListSequenceWidget)
        True
    """

    _WidgetFactory = TupleSequenceWidget

    def testRender(self):
        pass

    def setUp(self):
        super(SequenceWidgetTest, self).setUp()
        ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)
        ztapi.browserViewProviding(IWidgetInputError, WidgetInputErrorView,
                                   IWidgetInputErrorView)

    def test_haveNoData(self):
        self.failIf(self._widget.hasInput())

    def test_hasInput(self):
        self._widget.request.form['field.foo.count'] = u'0'
        self.failUnless(self._widget.hasInput())

    def test_customWidgetFactory(self):
        """Verify that the widget can be constructed via the CustomWidgetFactory
        (Issue #293)
        """

        value_type = TextLine(__name__=u'bar')
        self.field = List( __name__=u'foo', value_type=value_type )
        request = TestRequest()

        # set up the custom widget factory and verify that it works
        sw = CustomWidgetFactory(ListSequenceWidget)
        widget = sw(self.field, request)
        assert widget.subwidget is None
        assert widget.context.value_type is value_type

        # set up a variant that specifies the subwidget to use and verify it
        class PollOption(object) : pass
        ow = CustomWidgetFactory(ObjectWidget, PollOption)
        sw = CustomWidgetFactory(ListSequenceWidget, subwidget=ow)
        widget = sw(self.field, request)
        assert widget.subwidget is ow
        assert widget.context.value_type is value_type

    def test_subwidget(self):
        """This test verifies that the specified subwidget is not ignored.
        (Issue #293)
        """
        self.field = List(__name__=u'foo',
                          value_type=TextLine(__name__=u'bar'))
        request = TestRequest()

        class PollOption(object) : pass
        ow = CustomWidgetFactory(ObjectWidget, PollOption)
        widget = SequenceWidget(
            self.field, self.field.value_type, request, subwidget=ow)
        assert widget.subwidget is ow

    def test_list(self):
        self.field = List(
            __name__=u'foo',
            value_type=TextLine(__name__=u'bar'))
        request = TestRequest()
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.failIf(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)

        request = TestRequest(form={'field.foo.add': u'Add bar',
                                    'field.foo.count': u'0'})
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertRaises(WidgetInputError, widget.getInputValue)

        request = TestRequest(form={'field.foo.0.bar': u'Hello world!',
                                    'field.foo.count': u'1'})
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertEquals(widget.getInputValue(), [u'Hello world!'])

    def test_new(self):
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.failIf(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = ('input', 'name="field.foo.add"')
        self.verifyResult(widget(), check_list)

    def test_add(self):
        request = TestRequest(form={'field.foo.add': u'Add bar',
                                    'field.foo.count': u'0'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertRaises(WidgetInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
            'submit', 'submit', 'field.foo.add'
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_request(self):
        request = TestRequest(form={'field.foo.0.bar': u'Hello world!',
                                    'field.foo.count': u'1'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertEquals(widget.getInputValue(), (u'Hello world!',))

    def test_existing(self):
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.failIf(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="1"',
        )
        self.verifyResult(widget(), check_list, inorder=True)
        widget.setRenderedValue((u'existing', u'second'))
        self.failIf(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'checkbox', 'field.foo.remove_1', 'input', 'field.foo.1.bar',
                'second',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="2"',
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_remove(self):
        request = TestRequest(form={
            'field.foo.remove_0': u'1',
            'field.foo.0.bar': u'existing', 'field.foo.1.bar': u'second',
            'field.foo.remove': u'Remove selected items',
            'field.foo.count': u'2'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing', u'second'))
        self.assertEquals(widget.getInputValue(), (u'second',))
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'checkbox', 'field.foo.remove_1', 'input', 'field.foo.1.bar',
                'second',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="2"',
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_min(self):
        request = TestRequest()
        self.field.min_length = 2
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'input', 'field.foo.0.bar', 'existing',
            'input', 'field.foo.1.bar', 'value=""',
            'submit', 'field.foo.add'
        )
        s = widget()
        self.verifyResult(s, check_list, inorder=True)
        self.assertEquals(s.find('checkbox'), -1)

    def test_max(self):
        request = TestRequest()
        self.field.max_length = 1
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.assertRaises(MissingInputError, widget.getInputValue)
        s = widget()
        self.assertEquals(s.find('field.foo.add'), -1)

    def test_anonymousfield(self):
        self.field = Tuple(__name__=u'foo', value_type=TextLine())
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        s = widget()
        check_list = (
            'input', '"field.foo.0."', 'existing',
            'submit', 'submit', 'field.foo.add'
        )
        s = widget()
        self.verifyResult(s, check_list, inorder=True)

    def test_usererror(self):
        self.field = Tuple(__name__=u'foo',
                           value_type=TextLine(__name__='bar'))
        request = TestRequest(form={
            'field.foo.0.bar': u'', 'field.foo.1.bar': u'nonempty',
            'field.foo.count': u'2'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        s = widget()
        # Rendering a widget should not raise errors!
        result = widget()

        data = widget._generateSequence()
        self.assertEquals(data, [None, u'nonempty'])

    def doctest_widgeterrors(self):
        """Test that errors on subwidgets appear

            >>> field = Tuple(__name__=u'foo',
            ...               value_type=TextLine(__name__='bar'))
            >>> request = TestRequest(form={
            ...     'field.foo.0.bar': u'',
            ...     'field.foo.1.bar': u'nonempty',
            ...     'field.foo.count': u'2'})
            >>> widget = TupleSequenceWidget(field, field.value_type, request)

         If we render the widget, we see no errors:

            >>> print widget()
            <BLANKLINE>
            ...
            <tr>
              <td>
                 <input class="editcheck" type="checkbox"
                        name="field.foo.remove_0" />
              </td>
              <td>
                 <input class="textType" id="field.foo.0.bar"
                        name="field.foo.0.bar"
                        size="20" type="text" value=""  />
              </td>
            </tr>
            ...

         However, if we call getInputValue or hasValidInput, the
         errors on the widgets are preserved and displayed:

            >>> widget.hasValidInput()
            False

            >>> print widget()
            <BLANKLINE>
            ...
            <tr>
              <td>
                 <input class="editcheck" type="checkbox"
                        name="field.foo.remove_0" />
              </td>
              <td>
                 <span class="error">Required input is missing.</span>
                 <input class="textType" id="field.foo.0.bar"
                        name="field.foo.0.bar"
                        size="20" type="text" value=""  />
              </td>
            </tr>
            ...
        """


class SequenceDisplayWidgetTest(
    VerifyResults, SequenceWidgetTestHelper, unittest.TestCase):

    def _WidgetFactory(self, *args, **kw):
        w = SequenceDisplayWidget(*args, **kw)
        w.cssClass = "testwidget"
        return w

    def setUp(self):
        self.setUpContent()
        self.request = TestRequest()
        self.widget = self._WidgetFactory(
            self.field, self.field.value_type, self.request)
        ztapi.browserViewProviding(ITextLine, DisplayWidget, IDisplayWidget)

    def test_render_empty(self):
        self.content.foo = ()
        self.assertEquals(self.widget(), '(no values)')

    def test_render_missing(self):
        self.content.foo = self.field.missing_value
        self.assertEquals(self.widget(), '(no value available)')

    def test_render_single(self):
        self.content.foo = (u'one value',)
        check_list = ['<ol', 'class=', 'testwidget',
                      '<li', 'one value', '</li', '</ol']
        self.verifyResult(self.widget(), check_list, inorder=True)

    def test_render_multiple(self):
        self.content.foo = (u'one', u'two', u'three', u'four')
        check_list = ['<ol', 'class=', 'testwidget',
                      '<li', 'one', '</li',
                      '<li', 'two', '</li',
                      '<li', 'three', '</li',
                      '<li', 'four', '</li',
                      '</ol']
        self.verifyResult(self.widget(), check_list, inorder=True)

    def test_render_alternate_cssClass(self):
        self.content.foo = (u'one value',)
        check_list = ['<ol', 'class=', 'altclass',
                      '<li', 'one value', '</li', '</ol']
        self.widget.cssClass = 'altclass'
        self.verifyResult(self.widget(), check_list, inorder=True)

    def test_honors_subwidget(self):
        self.widget = self._WidgetFactory(
            self.field, self.field.value_type, self.request,
            subwidget=UppercaseDisplayWidget)
        self.content.foo = (u'first value', u'second value')
        check_list = ['<ol', 'class=', 'testwidget',
                      '<li', 'FIRST VALUE', '</li',
                      '<li', 'SECOND VALUE', '</li',
                      '</ol']
        self.verifyResult(self.widget(), check_list, inorder=True)


class UppercaseDisplayWidget(DisplayWidget):

    def __call__(self):
        return super(UppercaseDisplayWidget, self).__call__().upper()


def setUp(test):
    setup.placefulSetUp()
    ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)
    ztapi.browserViewProviding(IWidgetInputError, WidgetInputErrorView,
                               IWidgetInputErrorView)


def tearDown(test):
    setup.placefulTearDown()


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SequenceWidgetTest),
        doctest.DocTestSuite(setUp=setUp, tearDown=tearDown,
                             optionflags=doctest.ELLIPSIS
                             |doctest.NORMALIZE_WHITESPACE
                             |doctest.REPORT_NDIFF),
        unittest.makeSuite(SequenceDisplayWidgetTest),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

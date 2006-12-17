##############################################################################
#
# Copyright (c) 2001, 2002, 2004, 2005 Zope Corporation and Contributors.
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
"""Text Widget tests

$Id: test_textwidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import datetime
import unittest
from zope.testing import doctest
from zope.interface.verify import verifyClass
from zope.schema import TextLine
from zope.publisher.browser import TestRequest

from zope.app.form.interfaces import IInputWidget

from zope.app.form.browser import TextWidget

from zope.app.form.browser import TextAreaWidget
from zope.app.form.browser import BytesAreaWidget
from zope.app.form.browser import PasswordWidget
from zope.app.form.browser import FileWidget
from zope.app.form.browser import IntWidget
from zope.app.form.browser import FloatWidget
from zope.app.form.browser import BytesWidget
from zope.app.form.browser import ASCIIWidget

from zope.app.form.browser import DateDisplayWidget
from zope.app.form.browser import DatetimeDisplayWidget
from zope.app.form.browser import URIDisplayWidget

from zope.app.testing.placelesssetup import setUp, tearDown
from zope.app.form.browser.tests.test_browserwidget import BrowserWidgetTest
from zope.app.form.browser.tests.test_browserwidget \
     import SimpleInputWidgetTest

class TextWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the text widget.
    >>> setUp()

        >>> verifyClass(IInputWidget, TextWidget)
        True

    Converting Missing Values
    -------------------------
    String fields (TextLine, Text, etc.) values can be classified as one of the
    following:

      - Non-empty string
      - Empty string
      - None

    Text browser widgets only support the first two types: non-empty strings
    and empty strings. There's no facility to explicitly set a None value in a
    text browser widget.

    However, it is possible to interpret an empty string as None for some
    applications. For example, when inputing a User Name, an empty string means
    'the user hasn't provided a value'. In another application, an empty string
    may mean 'the user has provided a value, specifically <empty string>'.

    To support both modes, the text widget provides a 'convert_missing_value'
    flag. When True, empty strings will be converted by the widget to the
    field's 'missing_value' (None by default). This mode accommodates the
    'user hasn't provided a value' scenario.

    To illustrate this mode, we'll use an optional field, where missing_value
    is None:

        >>> field = TextLine(
        ...     __name__='foo',
        ...     missing_value=None,
        ...     required=False)

    The HTTP form submission contains an empty string for the field value:

        >>> request = TestRequest(form={'field.foo':u''})

    A text widget configured for the field, where convert_missing_value is True
    (the default value)...

        >>> widget = TextWidget(field, request)
        >>> widget.convert_missing_value
        True

    will convert the form's empty string into the field's missing_value, which
    is None:

        >>> widget.getInputValue() is None
        True

    When 'convert_missing_value' is False, the text widget will not convert
    an empty string to the field's missing_value. This supports the 'user has
    provided a value, specifically <empty string>' mode:

        >>> widget.convert_missing_value = False
        >>> widget.getInputValue()
        u''

    >>> tearDown()
    """

    _WidgetFactory = TextWidget

    def testProperties(self):
        self.assertEqual(self._widget.tag, 'input')
        self.assertEqual(self._widget.type, 'text')
        self.assertEqual(self._widget.cssClass, '')
        self.assertEqual(self._widget.extra, '')
        self.assertEqual(self._widget.default, '')
        self.assertEqual(self._widget.displayWidth, 20)
        self.assertEqual(self._widget.displayMaxWidth, '')

    def testRender(self):
        value = 'Foo Value'
        self._widget.setRenderedValue(value)
        check_list = ('type="text"', 'id="field.foo"', 'name="field.foo"',
                      'value="Foo Value"', 'size="20"')
        self.verifyResult(self._widget(), check_list)
        check_list = ('type="hidden"',) + check_list[1:-1]
        self.verifyResult(self._widget.hidden(), check_list)
        check_list = ('style="color: red"',) + check_list
        self._widget.extra = 'style="color: red"'
        self.verifyResult(self._widget.hidden(), check_list)

class URIDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = URIDisplayWidget

    def testProperties(self):
        # check the default linkTarget
        self.failIf(self._widget.linkTarget)

    def testRender(self):
        value = "uri:fake"
        self._widget.setRenderedValue(value)
        self.verifyResult(self._widget(), ["<a", 'href="uri:fake"'])
        self._widget.linkTarget = "there"
        self.verifyResult(self._widget(), ["<a", 'href="uri:fake"',
                                           'target="there"'])

class DateDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = DateDisplayWidget

    expected_class = "date"

    def setUp(self):
        super(DateDisplayWidgetTest, self).setUp()
        self._value = datetime.date(2004, 12, 01)

    def testDefaultDisplayStyle(self):
        self.failIf(self._widget.displayStyle)

    def testRenderDefault(self):
        self._widget.setRenderedValue(self._value)
        self.verifyResult(self._widget(),
                          ["<span",
                           'class="%s"' % self.expected_class,
                           "01.12.2004",
                           "</span"])

    def testRenderShort(self):
        self._widget.setRenderedValue(self._value)
        self._widget.displayStyle = "short"
        self.verifyResult(self._widget(),
                          ["<span",
                           'class="%s"' % self.expected_class,
                           u"01.12.04",
                           "</span"])

    def testRenderMedium(self):
        self._widget.setRenderedValue(self._value)
        self._widget.displayStyle = "medium"
        self.verifyResult(self._widget(),
                          ["<span",
                           'class="%s"' % self.expected_class,
                           u"01.12.2004",
                           "</span"])

    def testRenderLong(self):
        self._widget.setRenderedValue(self._value)
        self._widget.displayStyle = "long"
        self.verifyResult(self._widget(),
                          ["<span",
                           'class="%s"' % self.expected_class,
                           u"1 \u0414\u0435\u043a\u0430\u0431\u0440\u044c"
                                u" 2004 \u0433.",
                           "</span"])

    def testRenderFull(self):
        self._widget.setRenderedValue(self._value)
        self._widget.displayStyle = "full"
        self.verifyResult(self._widget(),
                          ["<span",
                           'class="%s"' % self.expected_class,
                           u"1 \u0414\u0435\u043a\u0430\u0431\u0440\u044c"
                                u" 2004 \u0433.",
                           "</span"])


class DatetimeDisplayWidgetTest(DateDisplayWidgetTest):

    _WidgetFactory = DatetimeDisplayWidget

    expected_class = "dateTime"

    def setUp(self):
        super(DatetimeDisplayWidgetTest, self).setUp()
        self._value = datetime.datetime(2004, 12, 01, 14, 39, 01)

    def testRenderDefault(self):
        super(DatetimeDisplayWidgetTest, self).testRenderDefault()
        self.verifyResult(self._widget(), ["14:39:01"])

    def testRenderShort(self):
        super(DatetimeDisplayWidgetTest, self).testRenderShort()
        self.verifyResult(self._widget(), ["14:39"])

    def testRenderMedium(self):
        super(DatetimeDisplayWidgetTest, self).testRenderMedium()
        self.verifyResult(self._widget(), ["14:39:01"])

    def testRenderLong(self):
        super(DatetimeDisplayWidgetTest, self).testRenderLong()
        self.verifyResult(self._widget(), ["14:39:01 +000"])

    def testRenderFull(self):
        super(DatetimeDisplayWidgetTest, self).testRenderFull()
        self.verifyResult(self._widget(), ["14:39:01 +000"])

class TextAreaDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = TextAreaWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = u"""
        texttexttexttexttexttextexttexttext\xE9\xE9\xE9\xE9\xE9\xE9\xE9\xE9\xE9
        texttexttexttexttextte\xE9\xE9\xE9\xE9\xE9xttexttexttexttexttexttexttex
        texttexttexttexttexttexttexttexttexttexttexttexttexttexttext
        """
        self._widget.setRenderedValue(value)
        self.assert_(value, self._widget._toFieldValue(value))
        self.verifyResult(self._widget(), ["<textarea",
                                           self._widget._toFormValue(value)])
        check_list = (
            ('id', 'field.foo'),
            ('name', 'field.foo'),
            #('value', ), tested above
            ('cols', '60'),
            ('rows', '15'),
            )
        for a, v in check_list:
            self.verifyResult(self._widget(), [a, v])

class BytesAreaDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = BytesAreaWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = """
        texttexttexttexttexttexttexttexttexttexttexttexttexttexttext
        texttexttexttexttexttexttexttexttexttexttexttexttexttexttext
        texttexttexttexttexttexttexttexttexttexttexttexttexttexttext
        """
        self._widget.setRenderedValue(value)
        self.assert_(value, self._widget._toFieldValue(value))
        self.verifyResult(self._widget(), ["<textarea",
                                           self._widget._toFormValue(value)])
        check_list = (
            ('id', 'field.foo'),
            ('name', 'field.foo'),
            #('value', ), tested above
            ('cols', '60'),
            ('rows', '15'),
            )
        for a, v in check_list:
            self.verifyResult(self._widget(), [a, v])

class BytesDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = BytesWidget

    # It uses the BytesDisplayWidget
    def testRender(self):
        value = "Food Value"
        self._widget.setRenderedValue(value)
        check_list = ('type="text"', 'id="field.foo"', 'name="field.foo"',
                      'value="%s"'%value, 'size="20"')
        self.verifyResult(self._widget(), check_list)

class ASCIIDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = ASCIIWidget

    # It uses the default BytesDisplayWidget
    def testRender(self):
        value = "Food Value"
        self._widget.setRenderedValue(value)
        check_list = ('type="text"', 'id="field.foo"', 'name="field.foo"',
                      'value="%s"'%value, 'size="20"')
        self.verifyResult(self._widget(), check_list)

class PasswordDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = PasswordWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = 'Foo Value'
        self._widget.setRenderedValue(value)
        check_list = ('type="password"', 'id="field.foo"', 'name="field.foo"',
                      'value=""', 'size="20"')
        self.verifyResult(self._widget(), check_list)

class FileDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = FileWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = 'Foo Value'
        self._widget.setRenderedValue(value)
        check_list = ('type="file"', 'id="field.foo"', 'name="field.foo"',
                      'size="20"')
        self.verifyResult(self._widget(), check_list)
        check_list = ('type="hidden"',) + check_list[1:-1]
        self.verifyResult(self._widget.hidden(), check_list)
        check_list = ('style="color: red"',) + check_list
        self._widget.extra = 'style="color: red"'
        self.verifyResult(self._widget.hidden(), check_list)

class IntDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = IntWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = 1
        self._widget.setRenderedValue(value)
        check_list = ('type="text"', 'id="field.foo"', 'name="field.foo"',
                      'size="10"', 'value="%s"'%str(value))
        self.verifyResult(self._widget(), check_list)

class FloatDisplayWidgetTest(BrowserWidgetTest):

    _WidgetFactory = FloatWidget

    # It uses the default DisplayWidget
    def testRender(self):
        value = 1.2
        self._widget.setRenderedValue(value)
        check_list = ('type="text"', 'id="field.foo"', 'name="field.foo"',
                      'size="10"', 'value="%s"'%str(value))
        self.verifyResult(self._widget(), check_list)

def test_w_nonrequired_and_missing_value_and_no_inout():
    """
    There was a bug that caused the value attribute to be set to
    'value' under these circumstances.

    >>> from zope.schema import TextLine
    >>> field = TextLine(__name__='foo', title=u'on',
    ...                  required=False, missing_value=u'')
    >>> request = TestRequest()
    >>> widget = TextWidget(field, request)

    >>> def normalize(s):
    ...   return '\\n  '.join(filter(None, s.split(' ')))

    >>> print normalize( widget() )
    <input
      class="textType"
      id="field.foo"
      name="field.foo"
      size="20"
      type="text"
      value=""
      />

    """

def test_no_error_on_render_only():
    """This is really a test of a bug fix to SimpleInputWidget.

    _error shouldn't be set due to an *internal* call to getInputValue
    when rendering.

    >>> from zope.schema import TextLine
    >>> field = TextLine(__name__='foo')
    >>> request = TestRequest(form={'field.foo': ''})
    >>> widget = TextWidget(field, request)
    >>> ignored = widget()
    >>> unicode(widget.error())
    u''


    """

def test_text_area_works_with_missing_value():
    """
    >>> from zope.schema import Text
    >>> field = Text(__name__='foo', title=u'on',
    ...              required=False, missing_value=u'')
    >>> request = TestRequest()
    >>> widget = TextAreaWidget(field, request)
    >>> def normalize(s):
    ...   return '\\n  '.join(filter(None, s.split(' ')))

    >>> print normalize( widget() )
    <textarea
      cols="60"
      id="field.foo"
      name="field.foo"
      rows="15"
      ></textarea>

    >>> print normalize( widget.hidden() )
    <input
      class="hiddenType"
      id="field.foo"
      name="field.foo"
      type="hidden"
      value=""
      />
      """

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TextWidgetTest),
        unittest.makeSuite(URIDisplayWidgetTest),
        unittest.makeSuite(DateDisplayWidgetTest),
        unittest.makeSuite(DatetimeDisplayWidgetTest),
        unittest.makeSuite(TextAreaDisplayWidgetTest),
        unittest.makeSuite(BytesAreaDisplayWidgetTest),
        unittest.makeSuite(PasswordDisplayWidgetTest),
        unittest.makeSuite(FileDisplayWidgetTest),
        unittest.makeSuite(IntDisplayWidgetTest),
        unittest.makeSuite(FloatDisplayWidgetTest),
        unittest.makeSuite(BytesDisplayWidgetTest),
        unittest.makeSuite(ASCIIDisplayWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

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
"""Datetime Widget Tests

$Id: test_datetimewidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import datetime
import unittest
from zope.testing import doctest

from zope.schema import Datetime
from zope.datetime import parseDatetimetz, tzinfo
from zope.interface.verify import verifyClass

from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import DatetimeWidget
from zope.app.form.browser import DatetimeI18nWidget
from zope.app.form.interfaces import ConversionError, WidgetInputError


class DatetimeWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the datetime widget.

        >>> verifyClass(IInputWidget, DatetimeWidget)
        True
    """

    _FieldFactory = Datetime
    _WidgetFactory = DatetimeWidget

    def testRender(self):
        super(DatetimeWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="2004-03-26 12:58:59"'))

    def test_hasInput(self):
        del self._widget.request.form['field.foo']
        self.failIf(self._widget.hasInput())
        # widget has input, even if input is an empty string
        self._widget.request.form['field.foo'] = u''
        self.failUnless(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u'2003-03-26 12:00:00'
        self.failUnless(self._widget.hasInput())

    def test_getInputValue(self,
            value=u'2004-03-26 12:58:59',
            check_value=parseDatetimetz('2004-03-26 12:58:59')):
        self._widget.request.form['field.foo'] = u''
        self.assertRaises(WidgetInputError, self._widget.getInputValue)
        self._widget.request.form['field.foo'] = value
        self.assertEquals(self._widget.getInputValue(), check_value)
        self._widget.request.form['field.foo'] = u'abc'
        self.assertRaises(ConversionError, self._widget.getInputValue)

class DatetimeI18nWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the i18n datetime widget.

        >>> verifyClass(IInputWidget, DatetimeI18nWidget)
        True
    """

    _FieldFactory = Datetime
    _WidgetFactory = DatetimeI18nWidget

    def testDefaultDisplayStyle(self):
        self.failIf(self._widget.displayStyle)

    def testRender(self):
        super(DatetimeI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.2004 12:58:59"'))

    def testRenderShort(self):
        self._widget.displayStyle = "short"
        super(DatetimeI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.04 12:58"'))

    def testRenderMedium(self):
        self._widget.displayStyle = "medium"
        super(DatetimeI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.2004 12:58:59"'))

    def testRenderLong(self):
        self._widget.displayStyle = "long"
        super(DatetimeI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                u'value="26 \u041c\u0430\u0440\u0442 2004 \u0433.'
                u' 12:58:59 +000"'))

    def testRenderFull(self):
        self._widget.displayStyle = "full"
        super(DatetimeI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                u'value="26 \u041c\u0430\u0440\u0442 2004 \u0433.'
                u' 12:58:59 +000"'))

    def test_hasInput(self):
        del self._widget.request.form['field.foo']
        self.failIf(self._widget.hasInput())
        # widget has input, even if input is an empty string
        self._widget.request.form['field.foo'] = u''
        self.failUnless(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u'26.03.2003 12:00:00'
        self.failUnless(self._widget.hasInput())

    def test_getDefaultInputValue(self,
            value=u'26.03.2004 12:58:59',
            check_value=datetime.datetime(2004, 3, 26, 12, 58, 59)):
        self._widget.request.form['field.foo'] = u''
        self.assertRaises(WidgetInputError, self._widget.getInputValue)
        self._widget.request.form['field.foo'] = value
        self.assertEquals(self._widget.getInputValue(), check_value)
        self._widget.request.form['field.foo'] = u'abc'
        self.assertRaises(ConversionError, self._widget.getInputValue)

    def test_getShortInputValue(self):
        self._widget.displayStyle = "short"
        self.test_getDefaultInputValue(
            value=u'26.03.04 12:58:59',
            check_value=datetime.datetime(2004, 3, 26, 12, 58)
            )

    def test_getMediumInputValue(self):
        self._widget.displayStyle = "medium"
        self.test_getDefaultInputValue(
            value=u'26.03.2004 12:58:59',
            check_value=datetime.datetime(2004, 3, 26, 12, 58, 59)
            )

    def test_getLongInputValue(self):
        self._widget.displayStyle = "long"
        self.test_getDefaultInputValue(
            value=(u'26 \u041c\u0430\u0440\u0442 2004 \u0433.'
                u' 12:58:59 +030'),
            check_value=datetime.datetime(2004, 3, 26, 12, 58, 59,
                tzinfo=tzinfo(30))
            )

    def test_getFullInputValue(self):
        self._widget.displayStyle = "full"
        self.test_getDefaultInputValue(
            value=(u'26 \u041c\u0430\u0440\u0442 2004 \u0433.'
                u' 12:58:59 +030'),
            check_value=datetime.datetime(2004, 3, 26, 12, 58, 59,
                tzinfo=tzinfo(30))
            )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DatetimeWidgetTest),
        unittest.makeSuite(DatetimeI18nWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

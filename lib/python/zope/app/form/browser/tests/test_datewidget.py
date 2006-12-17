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
"""Date Widget tests

$Id: test_datewidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import datetime
import unittest
from zope.testing import doctest
from zope.datetime import parseDatetimetz
from zope.schema import Date
from zope.interface.verify import verifyClass

from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import DateWidget
from zope.app.form.browser import DateI18nWidget
from zope.app.form.interfaces import ConversionError, WidgetInputError


class DateWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the date widget.

        >>> verifyClass(IInputWidget, DateWidget)
        True
    """

    _FieldFactory = Date
    _WidgetFactory = DateWidget

    def testRender(self):
        super(DateWidgetTest, self).testRender(
            datetime.date(2003, 3, 26),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="2003-03-26"'))

    def test_hasInput(self):
        del self._widget.request.form['field.foo']
        self.failIf(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u''
        self.failUnless(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u'2003-03-26'
        self.failUnless(self._widget.hasInput())

    def test_getInputValue(self,
            value=u'2004-03-26',
            check_value=datetime.date(2004, 3, 26)):
        self._widget.request.form['field.foo'] = u''
        self.assertRaises(WidgetInputError, self._widget.getInputValue)
        self._widget.request.form['field.foo'] = value
        self.assertEquals(self._widget.getInputValue(), check_value)
        self._widget.request.form['field.foo'] = u'abc'
        self.assertRaises(ConversionError, self._widget.getInputValue)

class DateI18nWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the i18n date widget.

        >>> verifyClass(IInputWidget, DateI18nWidget)
        True
    """

    _FieldFactory = Date
    _WidgetFactory = DateI18nWidget

    def testDefaultDisplayStyle(self):
        self.failIf(self._widget.displayStyle)

    def testRender(self):
        super(DateI18nWidgetTest, self).testRender(
            datetime.date(2003, 3, 26),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.2003"'))

    def testRenderShort(self):
        self._widget.displayStyle = "short"
        super(DateI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.04"'))

    def testRenderMedium(self):
        self._widget.displayStyle = "medium"
        super(DateI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                'value="26.03.2004"'))

    def testRenderLong(self):
        self._widget.displayStyle = "long"
        super(DateI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                u'value="26 \u041c\u0430\u0440\u0442 2004 \u0433."'))

    def testRenderFull(self):
        self._widget.displayStyle = "full"
        super(DateI18nWidgetTest, self).testRender(
            datetime.datetime(2004, 3, 26, 12, 58, 59),
            ('type="text"', 'id="field.foo"', 'name="field.foo"',
                u'value="26 \u041c\u0430\u0440\u0442 2004 \u0433."'))

    def test_hasInput(self):
        del self._widget.request.form['field.foo']
        self.failIf(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u''
        self.failUnless(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u'26.03.2003'
        self.failUnless(self._widget.hasInput())

    def test_getDefaultInputValue(self,
            value=u'26.03.2004',
            check_value=datetime.date(2004, 3, 26)):
        self._widget.request.form['field.foo'] = u''
        self.assertRaises(WidgetInputError, self._widget.getInputValue)
        self._widget.request.form['field.foo'] = value
        self.assertEquals(self._widget.getInputValue(), check_value)
        self._widget.request.form['field.foo'] = u'abc'
        self.assertRaises(ConversionError, self._widget.getInputValue)

    def test_getShortInputValue(self):
        self._widget.displayStyle = "short"
        self.test_getDefaultInputValue(u'26.03.04')

    def test_getMediumInputValue(self):
        self._widget.displayStyle = "medium"
        self.test_getDefaultInputValue(u'26.03.2004')

    def test_getLongInputValue(self):
        self._widget.displayStyle = "long"
        self.test_getDefaultInputValue(
            u'26 \u041c\u0430\u0440\u0442 2004 \u0433.'
            )

    def test_getFullInputValue(self):
        self._widget.displayStyle = "full"
        self.test_getDefaultInputValue(
            u'26 \u041c\u0430\u0440\u0442 2004 \u0433.'
            )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DateWidgetTest),
        unittest.makeSuite(DateI18nWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

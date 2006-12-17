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
"""Integer Widget Tests

$Id: test_intwidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from unittest import main, makeSuite
from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import IntWidget
from zope.app.form.interfaces import ConversionError, WidgetInputError
from zope.interface.verify import verifyClass

from zope.schema import Int


class IntWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the int widget.

        >>> verifyClass(IInputWidget, IntWidget)
        True
    """

    _FieldFactory = Int
    _WidgetFactory = IntWidget

    def test_hasInput(self):
        del self._widget.request.form['field.foo']
        self.failIf(self._widget.hasInput())
        # widget has input, even if input is an empty string
        self._widget.request.form['field.foo'] = u''
        self.failUnless(self._widget.hasInput())
        self._widget.request.form['field.foo'] = u'123'
        self.failUnless(self._widget.hasInput())

    def test_getInputValue(self):
        self._widget.request.form['field.foo'] = u''
        self.assertRaises(WidgetInputError, self._widget.getInputValue)
        self._widget.request.form['field.foo'] = u'123'
        self.assertEquals(self._widget.getInputValue(), 123)
        self._widget.request.form['field.foo'] = u'abc'
        self.assertRaises(ConversionError, self._widget.getInputValue)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IntWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

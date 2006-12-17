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
"""Password Widget Tests

$Id: test_passwordwidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import PasswordWidget
from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest
from zope.interface.verify import verifyClass

class PasswordWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the password widget.

        >>> verifyClass(IInputWidget, PasswordWidget)
        True
    """

    _WidgetFactory = PasswordWidget

    def testProperties(self):
        self.assertEqual(self._widget.tag, 'input')
        self.assertEqual(self._widget.type, 'password')
        self.assertEqual(self._widget.cssClass, '')
        self.assertEqual(self._widget.extra, '')
        self.assertEqual(self._widget.default, '')
        self.assertEqual(self._widget.displayWidth, 20)
        self.assertEqual(self._widget.displayMaxWidth, '')

    def testRender(self):
        value = 'Foo Value'
        self._widget.setRenderedValue(value)
        check_list = ('type="password"', 'id="field.foo"',
                      'name="field.foo"', 'value=""', 'size="20"')
        self.verifyResult(self._widget(), check_list)

    def testHidden(self):
        self.assertRaises(NotImplementedError, self._widget.hidden)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(PasswordWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

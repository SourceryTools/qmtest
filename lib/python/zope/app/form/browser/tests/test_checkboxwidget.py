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
"""Checkbox Widget tests

$Id: test_checkboxwidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import CheckBoxWidget
from zope.publisher.browser import TestRequest
from zope.schema import Bool
from zope.interface.verify import verifyClass

from zope.app.form.interfaces import MissingInputError
from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest


class CheckBoxWidgetTest(SimpleInputWidgetTest):
    """Documents and tests thec checkbox widget.

        >>> verifyClass(IInputWidget, CheckBoxWidget)
        True

    The checkbox widget works with Bool fields:

        >>> field = Bool(__name__='foo', title=u'on')
        >>> request = TestRequest()
        >>> widget = CheckBoxWidget(field, request)

    hasInput returns True when the request contains the field.<name>.used
    value:

        >>> 'field.foo.used' in request.form
        False
        >>> widget.hasInput()
        False
        >>> request.form['field.foo.used'] = ''
        >>> widget.hasInput()
        True

    getInputValue returns True when field.<name> equals (and only equals) 'on':

        >>> 'field.foo' in request.form
        False
        >>> widget.getInputValue()
        False
        >>> request.form['field.foo'] = 'true'
        >>> widget.getInputValue()
        False
        >>> request.form['field.foo'] = 'on'
        >>> widget.getInputValue()
        True

    Below is HTML output of rendered checkbox widgets. We will first define
    a helper method condense the HTML output for display in this test:

        >>> def normalize(s):
        ...   return '\\n  '.join(s.split())

    Default widget rendering:

        >>> print normalize( widget() )
        <input
          class="hiddenType"
          id="field.foo.used"
          name="field.foo.used"
          type="hidden"
          value=""
          />
          <input
          class="checkboxType"
          checked="checked"
          id="field.foo"
          name="field.foo"
          type="checkbox"
          value="on"
          />

    Hidden rendering:

        >>> print normalize( widget.hidden() )
        <input
          class="hiddenType"
          id="field.foo"
          name="field.foo"
          type="hidden"
          value="on"
          />

    Calling setRenderedValue will change what gets output:

        >>> widget.setRenderedValue(False)
        >>> print normalize( widget() )
        <input
          class="hiddenType"
          id="field.foo.used"
          name="field.foo.used"
          type="hidden"
          value=""
          />
          <input
          class="checkboxType"
          id="field.foo"
          name="field.foo"
          type="checkbox"
          value="on"
          />

    The checkbox widget does not support None values, so a Bool required
    constraint will always be met with checkbox input:

        >>> field.required = True
        >>> widget.getInputValue()
        True
    """

    _FieldFactory = Bool
    _WidgetFactory = CheckBoxWidget

    def testProperties(self):
        self.assertEqual(self._widget.tag, 'input')
        self.assertEqual(self._widget.type, 'checkbox')
        self.assertEqual(self._widget.cssClass, '')
        self.assertEqual(self._widget.extra, '')
        self.assertEqual(self._widget.default, 0)

    def testRender(self):
        value = 1
        self._widget.setRenderedValue(value)
        check_list = ('type="checkbox"', 'id="field.foo"',
                      'name="field.foo"', 'checked="checked"')
        self.verifyResult(self._widget(), check_list)
        value = 0
        self._widget.setRenderedValue(value)
        check_list = check_list[:-1]
        self.verifyResult(self._widget(), check_list)
        check_list = ('type="hidden"',) + check_list[1:-1]
        self.verifyResult(self._widget.hidden(), check_list)
        check_list = ('style="color: red"',) + check_list
        self._widget.extra = 'style="color: red"'
        self.verifyResult(self._widget.hidden(), check_list)

    def test_getInputValue(self):
        self._widget.request.form['field.foo'] = 'on'
        self.assertEqual(self._widget.getInputValue(), True)
        self._widget.request.form['field.foo'] = 'positive'
        self.assertEqual(self._widget.getInputValue(), False)
        del self._widget.request.form['field.foo']
        self._widget.request.form['field.foo.used'] = ''
        self.assertEquals(self._widget.getInputValue(), False)
        del self._widget.request.form['field.foo.used']
        self.assertRaises(MissingInputError, self._widget.getInputValue)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CheckBoxWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

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
"""Multi-Checkbox Widget Tests 

$Id: test_multicheckboxwidget.py 69217 2006-07-20 03:56:26Z baijum $
"""
import unittest
from zope.testing import doctest
from zope.interface import Interface, implements
from zope.publisher.browser import TestRequest
from zope.schema import Choice, List

from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser import MultiCheckBoxWidget
from zope.app.form.browser.tests.test_browserwidget import SimpleInputWidgetTest
from zope.interface.verify import verifyClass

class MultiCheckBoxWidgetTest(SimpleInputWidgetTest):
    """Documents and tests the multi checkbox widget.
        
        >>> verifyClass(IInputWidget, MultiCheckBoxWidget)
        True
    """

    _WidgetFactory = MultiCheckBoxWidget
    _FieldFactory = List

    def setUpContent(self, desc=u'', title=u'Foo Title'):
        class ITestContent(Interface):
            foo = self._FieldFactory(
                    title=title,
                    description=desc,
                    value_type=Choice(values=[u'foo', u'bar'])
                    )
        class TestObject(object):
            implements(ITestContent)

        self.content = TestObject()
        field = ITestContent['foo']
        field = field.bind(self.content)
        request = TestRequest(HTTP_ACCEPT_LANGUAGE='pl',
                              form={'field.foo': u'bar'})
        self._widget = self._WidgetFactory(field, field.value_type.vocabulary,
                                           request)

    def testProperties(self):
        self.assertEqual(self._widget.cssClass, "")
        self.assertEqual(self._widget.extra, '')
        self.assertEqual(self._widget.orientation, 'vertical')


    def testRenderItem(self):
        check_list = ('type="checkbox"', 'id="field.bar.',
                      'name="field.bar"', 'value="foo"', 'Foo')
        self.verifyResult(
            self._widget.renderItem(0, 'Foo', 'foo', 'field.bar', None),
            check_list)
        check_list += ('checked="checked"',)
        self.verifyResult(
            self._widget.renderSelectedItem(
                0, 'Foo', 'foo', 'field.bar', None),
            check_list)


    def testRenderItems(self):
        check_list = ('type="checkbox"', 'id="field.foo.',
                      'name="field.foo"', 'value="bar"', 'bar',
                      'value="foo"', 'foo', 'checked="checked"')
        self.verifyResult('\n'.join(self._widget.renderItems(['bar'])),
                          check_list)


    def testRender(self):
        check_list = ('type="checkbox"', 'id="field.foo.',
                      'name="field.foo"', 'value="bar"', 'bar',
                      'value="foo"', 'foo', 'checked="checked"')
        self.verifyResult(self._widget(), check_list)

        check_list = ('type="hidden"', 'id="field.foo', 'name="field.foo:list"',
                      'value="bar"')
        self.verifyResult(self._widget.hidden(), check_list)
        check_list = ('style="color: red"',) + check_list
        self._widget.extra = 'style="color: red"'
        self.verifyResult(self._widget.hidden(), check_list)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MultiCheckBoxWidgetTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

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
"""Object Widget tests

$Id: test_objectwidget.py 68721 2006-06-17 22:10:04Z ctheune $
"""
import unittest
from zope.testing import doctest

from zope.app.testing import ztapi
from zope.interface import Interface, implements
from zope.schema.interfaces import ITextLine
from zope.publisher.browser import TestRequest
from zope.schema import Object, TextLine
from zope.app.form.interfaces import IInputWidget, MissingInputError
from zope.app.form.browser import TextWidget, ObjectWidget
from zope.interface.verify import verifyClass
from zope.app.form.browser.tests.test_browserwidget import BrowserWidgetTest
from zope.app.form.browser.interfaces import IWidgetInputErrorView

class ITestContact(Interface):
    name = TextLine()
    email = TextLine()
    
class TestContact(object):
    implements(ITestContact)

class ObjectWidgetInputErrorView(object):
    implements(IWidgetInputErrorView)

    def __init__(self, error, request):
        self.error = error
        self.request = request

    def snippet(self):
        return repr(self.error)

class ObjectWidgetTest(BrowserWidgetTest):
    """Documents and tests the object widget.
        
        >>> verifyClass(IInputWidget, ObjectWidget)
        True
    """

    _FieldFactory = Object
    def _WidgetFactory(self, context, request, **kw):
        kw.update({'factory': TestContact})
        return ObjectWidget(context, request, **kw)

    def setUpContent(self, desc=u'', title=u'Foo Title'):
        ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)

        class ITestContent(Interface):
            foo = self._FieldFactory(
                    ITestContact, 
                    title=title,
                    description=desc
                    )
        class TestObject(object):
            implements(ITestContent)

        self.content = TestObject()
        self.field = ITestContent['foo']
        self.request = TestRequest(HTTP_ACCEPT_LANGUAGE='pl')
        self.request.form['field.foo'] = u'Foo Value'
        self._widget = self._WidgetFactory(self.field, self.request)

    def setUp(self):
        super(ObjectWidgetTest, self).setUp()
        self.field = Object(ITestContact, __name__=u'foo')
        ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)

    def test_applyChanges(self):
        self.request.form['field.foo.name'] = u'Foo Name'
        self.request.form['field.foo.email'] = u'foo@foo.test'
        widget = self._WidgetFactory(self.field, self.request)

        self.assertEqual(widget.applyChanges(self.content), True)
        self.assertEqual(hasattr(self.content, 'foo'), True)
        self.assertEqual(isinstance(self.content.foo, TestContact), True)
        self.assertEqual(self.content.foo.name, u'Foo Name')
        self.assertEqual(self.content.foo.email, u'foo@foo.test')

    def test_error(self):
        ztapi.provideAdapter(
                required=(MissingInputError, TestRequest),
                provided=IWidgetInputErrorView,
                factory=ObjectWidgetInputErrorView)

        widget = self._WidgetFactory(self.field, self.request)
        self.assertRaises(MissingInputError, widget.getInputValue)
        error_html = widget.error()
        self.failUnless("email: <zope.app.form.interfaces.Mis" in error_html)
        self.failUnless("name: <zope.app.form.interfaces.Miss" in error_html)

    def test_applyChangesNoChange(self):
        self.content.foo = TestContact()
        self.content.foo.name = u'Foo Name'
        self.content.foo.email = u'foo@foo.test'

        self.request.form['field.foo.name'] = u'Foo Name'
        self.request.form['field.foo.email'] = u'foo@foo.test'
        widget = self._WidgetFactory(self.field, self.request)
        widget.setRenderedValue(self.content.foo)

        self.assertEqual(widget.applyChanges(self.content), False)
        self.assertEqual(hasattr(self.content, 'foo'), True)
        self.assertEqual(isinstance(self.content.foo, TestContact), True)
        self.assertEqual(self.content.foo.name, u'Foo Name')
        self.assertEqual(self.content.foo.email, u'foo@foo.test')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ObjectWidgetTest),
        doctest.DocFileSuite('../objectwidget.txt'),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

# vim: set filetype=python ts=4 sw=4 et si



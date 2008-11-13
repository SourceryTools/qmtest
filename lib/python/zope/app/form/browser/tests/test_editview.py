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
"""Edit View Tests

$Id: test_editview.py 71638 2006-12-20 23:34:35Z jacobholm $
"""
import unittest

from zope.interface import Interface, implements
from zope.publisher.browser import TestRequest
from zope.schema import TextLine, accessors
from zope.schema.interfaces import ITextLine
from zope.component.interfaces import ComponentLookupError
from zope.component.eventtesting import getEvents, clearEvents
from zope.location.interfaces import ILocation

from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup

from zope.app.form.browser import TextWidget
from zope.app.form.browser.editview import EditView
from zope.app.form.browser.submit import Update
from zope.app.form.interfaces import IInputWidget
from zope.app.form.tests import utils

class I(Interface):
    foo = TextLine(title=u"Foo")
    bar = TextLine(title=u"Bar")
    a   = TextLine(title=u"A")
    b   = TextLine(title=u"B", min_length=0, required=False)
    getbaz, setbaz = accessors(TextLine(title=u"Baz"))

class EV(EditView):
    schema = I
    object_factories = []

class C(object):
    implements(I)
    foo = u"c foo"
    bar = u"c bar"
    a   = u"c a"
    b   = u"c b"
    __Security_checker__ = utils.SchemaChecker(I)

    _baz = u"c baz"
    def getbaz(self): return self._baz
    def setbaz(self, v): self._baz = v


class IFoo(Interface):
    foo = TextLine(title=u"Foo")

class IBar(Interface):
    bar = TextLine(title=u"Bar")

class Foo(object):
    implements(IFoo)
    __Security_checker__ = utils.SchemaChecker(IFoo)

    foo = u'Foo foo'
    
class ConformFoo(object):
    implements(IFoo)

    foo = u'Foo foo'

    def __conform__(self, interface):
        if interface is IBar:
            return OtherFooBarAdapter(self)

            
class FooBarAdapter(object):
    implements(IBar, ILocation)
    __used_for__ = IFoo

    def __init__(self, context):
        self.context = context

    def getbar(self): return self.context.foo
    def setbar(self, v): self.context.foo = v

    bar = property(getbar, setbar)
    
    __Security_checker__ = utils.SchemaChecker(IBar)
    
class OtherFooBarAdapter(FooBarAdapter):
    pass

class BarV(EditView):
    schema = IBar
    object_factories = []

class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        ztapi.browserViewProviding(ITextLine, TextWidget, IInputWidget)
        ztapi.provideAdapter(IFoo, IBar, FooBarAdapter)
        clearEvents()

    def test_setPrefix_and_widgets(self):
        v = EV(C(), TestRequest())
        v.setPrefix("test")
        self.assertEqual(
            [w.name for w in v.widgets()],
            ['test.foo', 'test.bar', 'test.a', 'test.b', 'test.getbaz']
            )

    def test_empty_prefix(self):
        v = EV(C(), TestRequest())
        v.setPrefix("")
        self.assertEqual(
            [w.name for w in v.widgets()],
            ['foo', 'bar', 'a', 'b', 'getbaz']
            )

    def test_fail_wo_adapter(self):
        c = Foo()
        request = TestRequest()
        self.assertRaises(TypeError, EV, c, request)

    def test_update_no_update(self):
        c = C()
        request = TestRequest()
        v = EV(c, request)
        self.assertEqual(v.update(), '')
        self.assertEqual(c.foo, u'c foo')
        self.assertEqual(c.bar, u'c bar')
        self.assertEqual(c.a  , u'c a')
        self.assertEqual(c.b  , u'c b')
        self.assertEqual(c.getbaz(), u'c baz')
        request.form['field.foo'] = u'r foo'
        request.form['field.bar'] = u'r bar'
        request.form['field.a']   = u'r a'
        request.form['field.b']   = u'r b'
        request.form['field.getbaz'] = u'r baz'
        self.assertEqual(v.update(), '')
        self.assertEqual(c.foo, u'c foo')
        self.assertEqual(c.bar, u'c bar')
        self.assertEqual(c.a  , u'c a')
        self.assertEqual(c.b  , u'c b')
        self.assertEqual(c.getbaz(), u'c baz')
        self.failIf(getEvents())

    def test_update(self):
        c = C()
        request = TestRequest()
        v = EV(c, request)
        request.form[Update] = ''
        request.form['field.foo'] = u'r foo'
        request.form['field.bar'] = u'r bar'
        request.form['field.getbaz'] = u'r baz'
        request.form['field.a'] = u'c a'

        message = v.update()
        self.failUnless(message.startswith('Updated '), message)
        self.assertEqual(c.foo, u'r foo')
        self.assertEqual(c.bar, u'r bar')
        self.assertEqual(c.a  , u'c a')
        self.assertEqual(c.b  , u'c b') # missing from form - unchanged
        self.assertEqual(c.getbaz(), u'r baz')

        # Verify that calling update multiple times has no effect

        c.__dict__.clear()
        self.assertEqual(v.update(), message)
        self.assertEqual(c.foo, u'c foo')
        self.assertEqual(c.bar, u'c bar')
        self.assertEqual(c.a  , u'c a')
        self.assertEqual(c.b  , u'c b')
        self.assertEqual(c.getbaz(), u'c baz')

    def test_update_via_adapter(self):
        f = Foo()
        request = TestRequest()
        v = BarV(f, request)
        # check adapter
        self.assertEqual(f.foo, u'Foo foo')
        a = IBar(f)
        self.assertEqual(a.bar, u'Foo foo')
        # update
        request.form[Update] = ''
        request.form['field.bar'] = u'r bar'
        message = v.update()
        self.failUnless(message.startswith('Updated '), message)
        self.assertEqual(a.bar, u'r bar')
        # wrong update
        self.failIf(getEvents())

    def test_setUpWidget_via_conform_adapter(self):
        
        f = ConformFoo()
        request = TestRequest()
        v = BarV(f, request)
        
def test_suite():
    return unittest.makeSuite(Test)

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

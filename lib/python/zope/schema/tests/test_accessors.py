##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Test Interface accessor methods.

$Id: test_accessors.py 29436 2005-03-11 04:11:07Z poster $
"""
import unittest
from zope.interface import Interface, implements
from zope.schema import Text, accessors
from zope.schema.interfaces import IText
from zope.schema.accessors import FieldReadAccessor, FieldWriteAccessor
from zope.interface.verify import verifyClass, verifyObject
from zope.interface import document
from zope.interface.interfaces import IMethod

class Test(unittest.TestCase):

    def test(self):

        field = Text(title=u"Foo thing")

        class I(Interface):

            getFoo, setFoo = accessors(field)

        class Bad(object):
            implements(I)

        class Good(object):
            implements(I)
            
            def __init__(self):
                self.set = 0

            def getFoo(self):
                return u"foo"

            def setFoo(self, v):
                self.set += 1

        names = I.names()
        names.sort()
        self.assertEqual(names, ['getFoo', 'setFoo'])
        self.assertEqual(I['getFoo'].field, field)
        self.assertEqual(I['getFoo'].__name__, 'getFoo')
        self.assertEqual(I['getFoo'].__doc__, u'get Foo thing')
        self.assertEqual(I['getFoo'].__class__, FieldReadAccessor)
        self.assertEqual(I['getFoo'].writer, I['setFoo'])

        # test some field attrs
        for attr in ('title', 'description', 'readonly'):
            self.assertEqual(getattr(I['getFoo'], attr), getattr(field, attr))

        self.assert_(IText.providedBy(I['getFoo']))
        
        self.assert_(IMethod.providedBy(I['getFoo']))
        self.assert_(IMethod.providedBy(I['setFoo']))

        self.assertEqual(I['setFoo'].field, field)
        self.assertEqual(I['setFoo'].__name__, 'setFoo')
        self.assertEqual(I['setFoo'].__doc__, u'set Foo thing')
        self.assertEqual(I['setFoo'].__class__, FieldWriteAccessor)

        self.assertRaises(Exception, verifyClass, I, Bad)
        self.assertRaises(Exception, verifyObject, I, Bad())
        
        self.assertEquals(I['getFoo'].query(Bad(), 42), 42)
        self.assertRaises(AttributeError, I['getFoo'].get, Bad())

        verifyClass(I, Good)
        verifyObject(I, Good())

        self.assertEquals(I['getFoo'].query(Good(), 42), u'foo')
        self.assertEquals(I['getFoo'].get(Good()), u'foo')
        instance = Good()
        I['getFoo'].set(instance, u'whatever')
        self.assertEquals(instance.set, 1)

    def test_doc(self):

        field = Text(title=u"Foo thing")

        class I(Interface):

            getFoo, setFoo = accessors(field)
            def bar(): pass
            x = Text()

        d = document.asStructuredText(I)
        self.assertEqual(d,
                         "I\n"
                         "\n"
                         " Attributes:\n"
                         "\n"
                         "  x -- no documentation\n"
                         "\n"
                         " Methods:\n"
                         "\n"
                         "  bar() -- no documentation\n"
                         "\n"
                         "  getFoo() -- get Foo thing\n"
                         "\n"
                         "  setFoo(newvalue) -- set Foo thing\n"
                         "\n"
                         )


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    return suite


if __name__ == '__main__':
    unittest.main()

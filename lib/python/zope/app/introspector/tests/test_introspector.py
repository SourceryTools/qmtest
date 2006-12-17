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
"""Introspector Tests.

$Id: test_introspector.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.deprecation

from unittest import TestCase, TestSuite, main, makeSuite

from zope.interface import Interface, Attribute, implements, directlyProvides
from zope.interface.verify import verifyObject
from zope.component.interface import provideInterface

from zope.app.testing import placelesssetup

zope.deprecation.__show__.off()
from zope.app.introspector import Introspector
from zope.app.introspector.interfaces import IIntrospector
zope.deprecation.__show__.on()

class ITestClass(Interface):
    def drool():
        """...drool..."""

class BaseTestClass(object):
    """This is stupid base class"""
    pass

class TestClass(BaseTestClass):
    """This is my stupid doc string"""
    implements(ITestClass)
    def drool(self):
        pass

class I(Interface):
    """bah blah"""

class I2(I):
    """eek"""

class I3(I, I2):
    """This is dummy doc string"""

    testAttribute1 = Attribute("""This is a dummy attribute.""")
    testAttribute2 = Attribute("""This is a dummy attribute.""")

    def one(param):
        """method one"""

    def two(param1, param2):
        """method two"""

class WeirdClass(object):
    def namesAndDescriptions(self):
        return "indeed"

class TestIntrospector(TestCase):
    """Test Introspector."""

    def setUp(self):
        placelesssetup.setUp()
        provideInterface('zope.app.tests.test_introspector.I', I)
        provideInterface('zope.app.tests.test_introspector.I2', I2)
        provideInterface('zope.app.tests.test_introspector.I3', I3)
        provideInterface('zope.app.tests.test_introspector.I4', I4)
        provideInterface('zope.app.tests.test_introspector.M1', M1)
        provideInterface('zope.app.tests.test_introspector.M2', M2)
        provideInterface('zope.app.tests.test_introspector.M3', M3)
        provideInterface('zope.app.tests.test_introspector.M4', M4)
        provideInterface('zope.app.tests.test_introspector.ITestClass',
                         ITestClass)

    def test_isInterface(self):
        ints = Introspector(ITestClass)
        self.assertEqual(ints.isInterface(), 1)

        ints = Introspector(TestClass())
        self.assertEqual(ints.isInterface(), 0)

        ints = Introspector(WeirdClass())
        self.assertEqual(ints.isInterface(), 0)

        verifyObject(IIntrospector, ints)

    def test_setRequest(self):
        ints = Introspector(Interface)
        request = {'PATH_INFO': '++module++zope.app.introspector.Introspector'}
        zope.deprecation.__show__.off()
        ints.setRequest(request)
        zope.deprecation.__show__.on()
        self.assertEqual(ints.currentclass, Introspector)

    def test_getClass(self):
        ints = Introspector(TestClass())
        request = {}
        ints.setRequest(request)
        self.assertEqual(ints.getClass(), 'TestClass')

    def testIntrospectorOnClass(self):
        request = {}
        ints = Introspector(TestClass)
        self.assertEqual(ints.isInterface(), 0)
        request['PATH_INFO'] = (
            '++module++zope.app.tests.test_introspector.TestClass')
        ints.setRequest(request)
        self.assertEqual(ints.getClass(), 'TestClass')

        self.assertEqual(
            ints.getBaseClassNames(),
            ['zope.app.introspector.tests.test_introspector.BaseTestClass'])
        self.assertEqual(
            ints.getModule(),
            'zope.app.introspector.tests.test_introspector')
        self.assertEqual(ints.getDocString(), "This is my stupid doc string")
        self.assertEqual(ints.getInterfaces(), (ITestClass,))
        self.assertEqual(
            ints.getInterfaceNames(),
            ['zope.app.introspector.tests.test_introspector.ITestClass'])
        self.assertEqual(ints.getExtends(), (BaseTestClass,))

    def testIntrospectorOnInterface(self):
        request = {}
        ints = Introspector(I3)
        self.assertEqual(ints.isInterface(), 1)
        request['PATH_INFO'] = (
            '++module++zope.app.introspector.tests.test_introspector.I3')
        ints.setRequest(request)
        self.assertEqual(
            ints.getModule(),
            'zope.app.introspector.tests.test_introspector')
        self.assertEqual(ints.getExtends(), (I, I2, ))
        self.assertEqual(
            ints.getDocString(),
            "This is dummy doc string")
        Iname = 'I3'
        bases = ['zope.app.introspector.tests.test_introspector.I',
                 'zope.app.introspector.tests.test_introspector.I2']
        desc = 'This is dummy doc string'
        m1_name = 'one'
        m1_signature = '(param)'
        m1_desc = 'method one'
        m2_name = 'two'
        m2_signature = '(param1, param2)'
        m2_desc = 'method two'
        methods = [(m1_name, m1_signature, m1_desc),
                   (m2_name, m2_signature, m2_desc),]
        attr_name1 = 'testAttribute1'
        attr_desc1 = 'This is a dummy attribute.'
        attr_name2 = 'testAttribute2'
        attr_desc2 = 'This is a dummy attribute.'
        attributes = [(attr_name1, attr_desc1),
                      (attr_name2, attr_desc2), ]
        details = [Iname, bases, desc, methods, attributes]
        self.assertEqual(ints.getInterfaceDetails(), details)

    def test_getDirectlyProvided(self):
        ob = TestClass()
        ints = Introspector(ob)
        self.assertEqual(tuple(ints.getDirectlyProvided()), ())
        directlyProvides(ob, I, I2)
        ints = Introspector(ob)
        self.assertEqual(tuple(ints.getDirectlyProvided()), (I, I2))

    def test_getDirectlyProvidedNames(self):
        ob = TestClass()
        ints = Introspector(ob)
        self.assertEqual(tuple(ints.getDirectlyProvidedNames()), ())
        directlyProvides(ob, I, I2)
        ints = Introspector(ob)
        self.assertEqual(tuple(ints.getDirectlyProvidedNames()),
                         ('zope.app.introspector.tests.test_introspector.I',
                          'zope.app.introspector.tests.test_introspector.I2'))
        
    def tearDown(self):
        placelesssetup.tearDown()


class I4(I3):
    foo = Attribute("Not a marker")

class M1(Interface): pass

class M2(I2): pass

class M3(I3): pass

class M4(I4): pass

class Content(object):
    implements(I3)

    def one(self, a): pass
    def two(self, a, b): pass

class TestMarkerInterfaces(TestCase):

    def setUp(self):
        placelesssetup.setUp()
        provideInterface('zope.app.introspector.tests.test_introspector.I', I)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.I2', I2)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.I3', I3)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.I4', I4)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.M1', M1)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.M2', M2)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.M3', M3)
        provideInterface(
            'zope.app.introspector.tests.test_introspector.M4', M4)

    def test_getMarkerInterfaces(self):
        ints = Introspector(Content())
        expected = [M1, M2, M3]
        expected.sort()
        self.assertEqual(ints.getMarkerInterfaces(), tuple(expected))

    def test_getMarkerInterfaceNames(self):
        ints = Introspector(Content())
        expected = ['zope.app.introspector.tests.test_introspector.M1',
                    'zope.app.introspector.tests.test_introspector.M2',
                    'zope.app.introspector.tests.test_introspector.M3']
        expected.sort()
        self.assertEqual(ints.getMarkerInterfaceNames(), tuple(expected))


    def test_getDirectMarkers(self):
        ints = Introspector(Content())
        self.assertEqual(ints.getDirectMarkersOf(I3), (M3,))

    def tearDown(self):
        placelesssetup.tearDown()
        

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestIntrospector))
    suite.addTest(makeSuite(TestMarkerInterfaces))
    return suite


if __name__ == '__main__':
    main(defaultTest='test_suite')

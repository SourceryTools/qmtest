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
"""Component Directives Tests

$Id: test_directives.py 67630 2006-04-27 00:54:03Z jim $
"""
import re
import unittest
import pprint
import warnings
from cStringIO import StringIO

from zope.interface import Interface, implements
from zope.testing.doctestunit import DocTestSuite
from zope.component import createObject
from zope.component.interfaces import IDefaultViewName
from zope.component.registry import SubscriptionRegistration
from zope.component.interfaces import ComponentLookupError
from zope.component.interface import queryInterface

from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.xmlconfig import ZopeXMLConfigurationError
from zope.security.proxy import removeSecurityProxy, getTestProxyItems
from zope.security.checker import ProxyFactory, selectChecker

import zope.app.component
from zope.app import zapi
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.component.tests.adapter import A1, A2, A3, Handler
from zope.app.component.tests.adapter import I1, I2, I3, IS
from zope.app.component.tests.components import IContent, Content, Comp, comp
from zope.app.component.tests.components import IApp
from zope.app.component.tests.views import Request, IV, IC, V1, R1, IR
from zope.app.content.interfaces import IContentType

from zope.app.component.tests import module, exampleclass

# TODO: tests for other directives needed

atre = re.compile(' at [0-9a-fA-Fx]+')

class Context(object):
    actions = ()

    def action(self, discriminator, callable, args):
        self.actions += ((discriminator, callable, args), )

    def __repr__(self):
        stream = StringIO()
        pprinter = pprint.PrettyPrinter(stream=stream, width=60)
        pprinter.pprint(self.actions)
        r = stream.getvalue()
        return (''.join(atre.split(r))).strip()


template = """<configure
   xmlns='http://namespaces.zope.org/zope'
   xmlns:test='http://www.zope.org/NS/Zope3/test'
   i18n_domain='zope'>
   %s
   </configure>"""

class Ob(object):
    implements(IC)

def definePermissions():
    XMLConfig('meta.zcml', zope.app.component)()


class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.app.component)()
        XMLConfig('meta.zcml', zope.app.security)()

    def testView(self):
        ob = Ob()
        request = Request(IV)
        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name=u'test'), None)

        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"/>
            '''
            ))

        self.assertEqual(
            zapi.queryMultiAdapter((ob, request), name=u'test').__class__,
            V1)


    def testMultiView(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.adapter.A3"
                  for="zope.app.component.tests.views.IC
                       zope.app.component.tests.adapter.I1
                       zope.app.component.tests.adapter.I2"
                  type="zope.app.component.tests.views.IV"/>
            '''
            ))


        ob = Ob()
        a1 = A1()
        a2 = A2()
        request = Request(IV)
        view = zapi.queryMultiAdapter((ob, a1, a2, request), name=u'test')
        self.assertEqual(view.__class__, A3)
        self.assertEqual(view.context, (ob, a1, a2, request))


    def testMultiView_fails_w_multiple_factories(self):
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
              '''
              <view name="test"
                    factory="zope.app.component.tests.adapter.A3
                             zope.app.component.tests.adapter.A2"
                    for="zope.app.component.tests.views.IC
                         zope.app.component.tests.adapter.I1
                         zope.app.component.tests.adapter.I2"
                    type="zope.app.component.tests.views.IV"/>
              '''
              )
            )

    def testView_w_multiple_factories(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.adapter.A1
                           zope.app.component.tests.adapter.A2
                           zope.app.component.tests.adapter.A3
                           zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"/>
            '''
            ))

        ob = Ob()

        # The view should be a V1 around an A3, around an A2, around
        # an A1, anround ob:
        view = zapi.queryMultiAdapter((ob, Request(IV)), name=u'test')
        self.assertEqual(view.__class__, V1)
        a3 = view.context
        self.assertEqual(a3.__class__, A3)
        a2 = a3.context[0]
        self.assertEqual(a2.__class__, A2)
        a1 = a2.context[0]
        self.assertEqual(a1.__class__, A1)
        self.assertEqual(a1.context[0], ob)

    def testView_fails_w_no_factories(self):
        self.assertRaises(ConfigurationError,
                          xmlconfig,
                          StringIO(template %
                                   '''
                                   <view name="test"
                                   factory=""
                                   for="zope.app.component.tests.views.IC"
                                   type="zope.app.component.tests.views.IV"/>
                                   '''
                                   ),
                          )


    def testViewThatProvidesAnInterface(self):
        ob = Ob()
        self.assertEqual(
            zapi.queryMultiAdapter((ob, Request(IR)), IV, u'test'), None)

        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IR"
                  />
            '''
            ))

        self.assertEqual(
            zapi.queryMultiAdapter((ob, Request(IR)), IV, u'test'), None)

        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IR"
                  provides="zope.app.component.tests.views.IV"
                  />
            '''
            ))

        v = zapi.queryMultiAdapter((ob, Request(IR)), IV, u'test')
        self.assertEqual(v.__class__, V1)


    def testUnnamedViewThatProvidesAnInterface(self):
        ob = Ob()
        self.assertEqual(
            zapi.queryMultiAdapter((ob, Request(IR)), IV), None)

        xmlconfig(StringIO(template %
            '''
            <view factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IR"
                  />
            '''
            ))

        v = zapi.queryMultiAdapter((ob, Request(IR)), IV)
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <view factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IR"
                  provides="zope.app.component.tests.views.IV"
                  />
            '''
            ))

        v = zapi.queryMultiAdapter((ob, Request(IR)), IV)
        self.assertEqual(v.__class__, V1)

    def testViewHavingARequiredClass(self):
        xmlconfig(StringIO(template % (
            '''
            <view
              for="zope.app.component.tests.components.Content"
              type="zope.app.component.tests.views.IR"
              factory="zope.app.component.tests.adapter.A1"
              />
            '''
            )))

        content = Content()
        a1 = zapi.getMultiAdapter((content, Request(IR)))
        self.assert_(isinstance(a1, A1))

        class MyContent:
            implements(IContent)

        self.assertRaises(ComponentLookupError, zapi.getMultiAdapter,
                          (MyContent(), Request(IR)))

    def testInterfaceProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.Public"
              allowed_interface="zope.app.component.tests.views.IV"
                  />
            '''
            ))

        v = ProxyFactory(zapi.getMultiAdapter((Ob(), Request(IV)), name='test'))
        self.assertEqual(v.index(), 'V1 here')
        self.assertRaises(Exception, getattr, v, 'action')

    def testAttributeProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.Public"
                  allowed_attributes="action"
                  />
            '''
            ))

        v = ProxyFactory(zapi.getMultiAdapter((Ob(), Request(IV)), name='test'))
        self.assertEqual(v.action(), 'done')
        self.assertRaises(Exception, getattr, v, 'index')

    def testInterfaceAndAttributeProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.Public"
                  allowed_attributes="action"
              allowed_interface="zope.app.component.tests.views.IV"
                  />
            '''
            ))

        v = zapi.getMultiAdapter((Ob(), Request(IV)), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testDuplicatedInterfaceAndAttributeProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.Public"
                  allowed_attributes="action index"
              allowed_interface="zope.app.component.tests.views.IV"
                  />
            '''
            ))

        v = zapi.getMultiAdapter((Ob(), Request(IV)), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testIncompleteProtectedViewNoPermission(self):
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  allowed_attributes="action index"
                  />
            '''
            ))

    def testViewUndefinedPermission(self):
        config = StringIO(template % (
            '''
            <view name="test"
                  factory="zope.app.component.tests.views.V1"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.UndefinedPermission"
                  allowed_attributes="action index"
              allowed_interface="zope.app.component.tests.views.IV"
                  />
            '''
            ))
        self.assertRaises(ValueError, xmlconfig, config, testing=1)


    def testDefaultView(self):
        ob = Ob()
        self.assertEqual(
            zapi.queryMultiAdapter((Ob(), Request(IV)), name='test'), None)

        xmlconfig(StringIO(template % (
            '''
            <defaultView name="test"
                  for="zope.app.component.tests.views.IC"
                  type="zope.app.component.tests.views.IV"/>
            '''
            )))

        self.assertEqual(
            zapi.queryMultiAdapter((Ob(), Request(IV)), name='test'), None)
        self.assertEqual(
            zapi.getGlobalSiteManager().adapters.lookup((IC, IV),
                                                        IDefaultViewName),
            'test')

    def testResource(self):
        ob = Ob()
        self.assertEqual(
            zapi.queryAdapter(Request(IV), name=u'test'), None)
        xmlconfig(StringIO(template % (
            '''
            <resource name="test"
                  factory="zope.app.component.tests.views.R1"
                  type="zope.app.component.tests.views.IV"/>
            '''
            )))

        self.assertEqual(
            zapi.queryAdapter(Request(IV), name=u'test').__class__,
            R1)

    def testResourceThatProvidesAnInterface(self):
        ob = Ob()
        self.assertEqual(zapi.queryAdapter(Request(IR), IV, u'test'), None)

        xmlconfig(StringIO(template %
            '''
            <resource
                name="test"
                factory="zope.app.component.tests.views.R1"
                type="zope.app.component.tests.views.IR"
                />
            '''
            ))

        v = zapi.queryAdapter(Request(IR), IV, name=u'test')
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <resource
                name="test"
                factory="zope.app.component.tests.views.R1"
                type="zope.app.component.tests.views.IR"
                provides="zope.app.component.tests.views.IV"
                />
            '''
            ))

        v = zapi.queryAdapter(Request(IR), IV, name=u'test')
        self.assertEqual(v.__class__, R1)

    def testUnnamedResourceThatProvidesAnInterface(self):
        ob = Ob()
        self.assertEqual(zapi.queryAdapter(Request(IR), IV), None)

        xmlconfig(StringIO(template %
            '''
            <resource
                factory="zope.app.component.tests.views.R1"
                type="zope.app.component.tests.views.IR"
                />
            '''
            ))

        v = zapi.queryAdapter(Request(IR), IV)
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <resource
                factory="zope.app.component.tests.views.R1"
                type="zope.app.component.tests.views.IR"
                provides="zope.app.component.tests.views.IV"
                />
            '''
            ))

        v = zapi.queryAdapter(Request(IR), IV)
        self.assertEqual(v.__class__, R1)

    def testResourceUndefinedPermission(self):

        config = StringIO(template % (
            '''
            <resource name="test"
                  factory="zope.app.component.tests.views.R1"
                  type="zope.app.component.tests.views.IV"
                  permission="zope.UndefinedPermission"/>
            '''
            ))
        self.assertRaises(ValueError, xmlconfig, config, testing=1)

    # BBB 2006/02/24, to be removed after 12 months
    def testFactory(self):
        showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None
        
        self.assertRaises(ComponentLookupError, zapi.createObject, 'foo')

        xmlconfig(StringIO(template % (
            '''
            <factory
               id="foo.bar"
               component="zope.app.component.tests.factory.f"
               />
            '''
            )))

        from factory import X
        self.assertEqual(zapi.createObject('foo.bar').__class__, X)

        warnings.showwarning = showwarning

class ParticipationStub(object):

    def __init__(self, principal):
        self.principal = principal
        self.interaction = None


def configfile(s):
    return StringIO("""<configure
      xmlns='http://namespaces.zope.org/zope'
      i18n_domain='zope'>
      %s
      </configure>
      """ % s)

class TestFactoryDirective(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        super(TestFactoryDirective, self).setUp()
        XMLConfig('meta.zcml', zope.app.component)()
        XMLConfig('meta.zcml', zope.app.security)()

    def testFactory(self):
        f = configfile('''
<permission id="zope.Foo" title="Zope Foo Permission" />
<class class="zope.app.component.tests.exampleclass.ExampleClass">
    <factory
      id="test.Example"
      title="Example content"
      description="Example description"
       />
</class>''')
        xmlconfig(f)
        obj = createObject('test.Example')
        self.failUnless(zapi.isinstance(obj, exampleclass.ExampleClass))



PREFIX = module.__name__ + '.'

def defineDirectives():
    XMLConfig('meta.zcml', zope.app.component)()
    XMLConfig('meta.zcml', zope.app.security)()
    xmlconfig(StringIO("""<configure
        xmlns='http://namespaces.zope.org/zope'
        i18n_domain='zope'>
       <permission id="zope.Extravagant" title="extravagant" />
       <permission id="zope.Paltry" title="paltry" />
    </configure>"""))

NOTSET = []

P1 = "zope.Extravagant"
P2 = "zope.Paltry"

class TestRequireDirective(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(TestRequireDirective, self).setUp()
        defineDirectives()

        class B(object):
            def m1(self):
                return "m1"
            def m2(self):
                return "m2"
        class C(B):
            implements(module.I)
            def m3(self):
                return "m3"
            def m4(self):
                return "m4"
        module.test_base = B
        module.test_class = C
        module.test_instance = C()
        self.assertState()

    def tearDown(self):
        PlacelessSetup.tearDown(self)
        module.test_class = None

    def assertState(self, m1P=NOTSET, m2P=NOTSET, m3P=NOTSET):
        "Verify that class, instance, and methods have expected permissions."

        from zope.security.checker import selectChecker

        checker = selectChecker(module.test_instance)
        self.assertEqual(checker.permission_id('m1'), (m1P or None))
        self.assertEqual(checker.permission_id('m2'), (m2P or None))
        self.assertEqual(checker.permission_id('m3'), (m3P or None))

    def assertDeclaration(self, declaration, **state):
        apply_declaration(module.template_bracket % declaration)
        self.assertState(**state)

    # "testSimple*" exercises tags that do NOT have children.  This mode
    # inherently sets the instances as well as the class attributes.

    def testSimpleMethodsPlural(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                attributes="m1 m3"/>
                          </class>'''
                       % (PREFIX+"test_class", P1))
        self.assertDeclaration(declaration, m1P=P1, m3P=P1)

    def assertSetattrState(self, m1P=NOTSET, m2P=NOTSET, m3P=NOTSET):
        "Verify that class, instance, and methods have expected permissions."

        from zope.security.checker import selectChecker

        checker = selectChecker(module.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), (m1P or None))
        self.assertEqual(checker.setattr_permission_id('m2'), (m2P or None))
        self.assertEqual(checker.setattr_permission_id('m3'), (m3P or None))

    def assertSetattrDeclaration(self, declaration, **state):
        self.assertSetattrState(**state)

    def test_set_attributes(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                set_attributes="m1 m3"/>
                          </class>'''
                       % (PREFIX+"test_class", P1))
        apply_declaration(module.template_bracket % declaration)
        checker = selectChecker(module.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), P1)
        self.assertEqual(checker.setattr_permission_id('m2'), None)
        self.assertEqual(checker.setattr_permission_id('m3'), P1)

    def test_set_schema(self):

        self.assertEqual(queryInterface(PREFIX+"S"), None)

        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                set_schema="%s"/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"S"))
        apply_declaration(module.template_bracket % declaration)

        self.assertEqual(queryInterface(PREFIX+"S"), module.S)


        checker = selectChecker(module.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), None)
        self.assertEqual(checker.setattr_permission_id('m2'), None)
        self.assertEqual(checker.setattr_permission_id('m3'), None)
        self.assertEqual(checker.setattr_permission_id('foo'), P1)
        self.assertEqual(checker.setattr_permission_id('bar'), P1)
        self.assertEqual(checker.setattr_permission_id('baro'), None)

    def test_multiple_set_schema(self):

        self.assertEqual(queryInterface(PREFIX+"S"), None)
        self.assertEqual(queryInterface(PREFIX+"S2"), None)

        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                set_schema="%s %s"/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"S", PREFIX+"S2"))
        apply_declaration(module.template_bracket % declaration)

        self.assertEqual(queryInterface(PREFIX+"S"), module.S)
        self.assertEqual(queryInterface(PREFIX+"S2"), module.S2)


        checker = selectChecker(module.test_instance)
        self.assertEqual(checker.setattr_permission_id('m1'), None)
        self.assertEqual(checker.setattr_permission_id('m2'), None)
        self.assertEqual(checker.setattr_permission_id('m3'), None)
        self.assertEqual(checker.setattr_permission_id('foo'), P1)
        self.assertEqual(checker.setattr_permission_id('bar'), P1)
        self.assertEqual(checker.setattr_permission_id('foo2'), P1)
        self.assertEqual(checker.setattr_permission_id('bar2'), P1)
        self.assertEqual(checker.setattr_permission_id('baro'), None)

    def testSimpleInterface(self):

        self.assertEqual(queryInterface(PREFIX+"I"), None)

        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                interface="%s"/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"I"))
        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertDeclaration(declaration, m1P=P1, m2P=P1)

        # Make sure we know about the interfaces
        self.assertEqual(queryInterface(PREFIX+"I"), module.I)


    def testMultipleInterface(self):

        self.assertEqual(queryInterface(PREFIX+"I3"), None)
        self.assertEqual(queryInterface(PREFIX+"I4"), None)

        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                interface="  %s
                                             %s  "/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"I3", PREFIX+"I4"))
        self.assertDeclaration(declaration, m3P=P1, m2P=P1)

        # Make sure we know about the interfaces
        self.assertEqual(queryInterface(PREFIX+"I3"), module.I3)
        self.assertEqual(queryInterface(PREFIX+"I4"), module.I4)

    # "testComposite*" exercises tags that DO have children.
    # "testComposite*TopPerm" exercises tags with permission in containing tag.
    # "testComposite*ElementPerm" exercises tags w/permission in children.

    def testCompositeNoPerm(self):
        # Establish rejection of declarations lacking a permission spec.
        declaration = ('''<class class="%s">
                            <require
                                attributes="m1"/>
                          </class>'''
                       % (PREFIX+"test_class"))
        self.assertRaises(ZopeXMLConfigurationError,
                          self.assertDeclaration,
                          declaration)



    def testCompositeMethodsPluralElementPerm(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                attributes="m1 m3"/>
                          </class>'''
                       % (PREFIX+"test_class", P1))
        self.assertDeclaration(declaration,
                               m1P=P1, m3P=P1)

    def testCompositeInterfaceTopPerm(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                interface="%s"/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"I"))
        self.assertDeclaration(declaration,
                               m1P=P1, m2P=P1)


    def testSubInterfaces(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                interface="%s"/>
                          </class>'''
                       % (PREFIX+"test_class", P1, PREFIX+"I2"))
        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertDeclaration(declaration, m1P=P1, m2P=P1)


    def testMimicOnly(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                attributes="m1 m2"/>
                          </class>
                          <class class="%s">
                            <require like_class="%s" />
                          </class>
                          ''' % (PREFIX+"test_base", P1,
                PREFIX+"test_class", PREFIX+"test_base"))
        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertDeclaration(declaration,
                               m1P=P1, m2P=P1)


    def testMimicAsDefault(self):
        declaration = ('''<class class="%s">
                            <require
                                permission="%s"
                                attributes="m1 m2"/>
                          </class>
                          <class class="%s">
                            <require like_class="%s" />
                            <require
                                permission="%s"
                                attributes="m2 m3"/>
                          </class>
                          ''' % (PREFIX+"test_base", P1,
                PREFIX+"test_class", PREFIX+"test_base", P2))

        # m1 and m2 are in the interface, so should be set, and m3 should not:
        self.assertDeclaration(declaration,
                               m1P=P1, m2P=P2, m3P=P2)


def apply_declaration(declaration):
    '''Apply the xmlconfig machinery.'''
    return xmlconfig(StringIO(declaration))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        unittest.makeSuite(TestFactoryDirective),
        unittest.makeSuite(TestRequireDirective),
        DocTestSuite(),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner().run(test_suite())

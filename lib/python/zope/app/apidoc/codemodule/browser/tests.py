##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Tests for the Code Documentation Module

$Id: tests.py 80813 2007-10-11 03:13:44Z srichter $
"""
import os
import unittest
import re
from zope.component.interfaces import IFactory
from zope.configuration import xmlconfig
from zope.interface import directlyProvides, implements
from zope.testing import doctest, doctestunit, renormalizing
from zope.traversing.interfaces import IContainmentRoot

import zope.app
import zope.app.appsetup.appsetup
from zope.app.renderer.rest import ReStructuredTextSourceFactory
from zope.app.renderer.rest import IReStructuredTextSource
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer
from zope.app.testing import placelesssetup, setup, ztapi
from zope.app.testing.functional import BrowserTestCase
from zope.app.testing.functional import FunctionalDocFileSuite

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.codemodule.interfaces import IAPIDocRootModule
from zope.app.apidoc.codemodule.codemodule import CodeModule
from zope.app.apidoc.testing import APIDocLayer
from zope.app.apidoc.zcmlmodule import ZCMLModule

# Just for loading purposes
import zope.app.apidoc.codemodule.browser.module
import zope.app.apidoc.codemodule.browser.class_
import zope.app.apidoc.codemodule.browser.function
import zope.app.apidoc.codemodule.browser.text
import zope.app.apidoc.codemodule.browser.zcml


def foo(cls, bar=1, *args):
    """This is the foo function."""
foo.deprecated = True

meta = '''
<configure
    xmlns:meta="http://namespaces.zope.org/meta"
    i18n_domain="zope">
  <meta:provides feature="devmode" />
  <include package="zope.app.zcmlfiles" file="meta.zcml" />
  <include package="zope.app.apidoc" file="meta.zcml" />
  <include package="zope.app.zcmlfiles" file="menus.zcml" />
</configure>
'''

def setUp(test):
    test.globs['rootFolder'] = setup.placefulSetUp(True)

    class RootModule(str):
        implements(IAPIDocRootModule)
    ztapi.provideUtility(IAPIDocRootModule, RootModule('zope'), "zope")

    module = CodeModule()
    module.__name__ = ''
    directlyProvides(module, IContainmentRoot)
    ztapi.provideUtility(IDocumentationModule, module, "Code")

    module = ZCMLModule()
    module.__name__ = ''
    directlyProvides(module, IContainmentRoot)
    ztapi.provideUtility(IDocumentationModule, module, "ZCML")

    # Register Renderer Components
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.rest')
    ztapi.browserView(IReStructuredTextSource, '',
                      ReStructuredTextToHTMLRenderer)
    # Cheat and register the ReST factory for STX as well.
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.stx')

    # Register ++apidoc++ namespace
    from zope.app.apidoc.apidoc import apidocNamespace
    from zope.traversing.interfaces import ITraversable
    ztapi.provideAdapter(None, ITraversable, apidocNamespace, name="apidoc")
    ztapi.provideView(None, None, ITraversable, "apidoc", apidocNamespace)

    # Register ++apidoc++ namespace
    from zope.traversing.namespace import view
    from zope.traversing.interfaces import ITraversable
    ztapi.provideAdapter(None, ITraversable, view, name="view")
    ztapi.provideView(None, None, ITraversable, "view", view)

    context = xmlconfig.string(meta)

    # Fix up path for tests.
    global old_context
    old_context = zope.app.appsetup.appsetup.__config_context
    zope.app.appsetup.appsetup.__config_context = context

    # Fix up path for tests.
    global old_source_file
    old_source_file = zope.app.appsetup.appsetup.__config_source
    zope.app.appsetup.appsetup.__config_source = os.path.join(
        os.path.dirname(zope.app.zcmlfiles.__file__), 'meta.zcml')

    # Register the index.html view for codemodule.class_.Class
    from zope.publisher.browser import BrowserView
    from zope.app.apidoc.codemodule.class_ import Class
    from zope.app.apidoc.codemodule.browser.class_ import ClassDetails
    class Details(ClassDetails, BrowserView):
        pass
    ztapi.browserView(Class, 'index.html', Details)


def tearDown(test):
    setup.placefulTearDown()
    global old_context, old_source_file
    zope.app.appsetup.appsetup.__config_context = old_context
    zope.app.appsetup.appsetup.__config_source = old_source_file


class CodeModuleTests(BrowserTestCase):
    """Just a couple of tests ensuring that the templates render."""

    def testMenu(self):
        response = self.publish('/++apidoc++/Code/menu.html',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Zope Source') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/Code/menu.html',
                                 basic='mgr:mgrpw')

    def testMenuCodeFinder(self):
        response = self.publish('/++apidoc++/Code/menu.html',
                                basic='mgr:mgrpw',
                                form={'path': 'Code', 'SUBMIT': 'Find'})
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(
            body.find('zope.app.apidoc.codemodule.codemodule.CodeModule') > 0)
        self.checkForBrokenLinks(body, '/++apidoc++/Code/menu.html',
                                 basic='mgr:mgrpw')

    def testModuleDetailsView(self):
        response = self.publish('/++apidoc++/Code/zope/app/apidoc/apidoc',
                                basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Zope 3 API Documentation') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc', basic='mgr:mgrpw')

    def testClassDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/apidoc/APIDocumentation',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('Represent the complete API Documentation.') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc/APIDocumentation',
            basic='mgr:mgrpw')

    def testFunctionDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/apidoc/handleNamespace',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_(body.find('handleNamespace(ob, name)') > 0)
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/apidoc/handleNamesapce',
            basic='mgr:mgrpw')

    def testTextFileDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/README.txt/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/README.txt/index.html',
            basic='mgr:mgrpw')

    def testZCMLFileDetailsView(self):
        response = self.publish(
            '/++apidoc++/Code/zope/app/apidoc/configure.zcml/index.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.checkForBrokenLinks(
            body, '/++apidoc++/Code/zope/app/apidoc/configure.zcml/index.html',
            basic='mgr:mgrpw')


def test_suite():
    checker = renormalizing.RENormalizing([
        (re.compile(r" with base 10: 'text'"), r': text'),
        ])
    CodeModuleTests.layer = APIDocLayer
    introspector = FunctionalDocFileSuite(
        "introspector.txt",
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    introspector.layer = APIDocLayer
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            setUp=setUp, tearDown=tearDown,checker=checker,
            globs={'pprint': doctestunit.pprint},
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocTestSuite(
            'zope.app.apidoc.codemodule.browser.menu',
            setUp=setUp, tearDown=tearDown,
            globs={'pprint': doctestunit.pprint},
            optionflags=doctest.NORMALIZE_WHITESPACE),
        unittest.makeSuite(CodeModuleTests),
        introspector,
        ))

if __name__ == '__main__':
    unittest.main(default="test_suite")

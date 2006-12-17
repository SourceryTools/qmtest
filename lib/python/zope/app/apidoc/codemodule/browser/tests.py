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

$Id: tests.py 29269 2005-02-23 22:22:48Z srichter $
"""
import os
import unittest
from zope.component.interfaces import IFactory
from zope.configuration import xmlconfig
from zope.interface import directlyProvides, implements
from zope.testing import doctest, doctestunit
from zope.traversing.interfaces import IContainmentRoot

import zope.app
import zope.app.appsetup.appsetup
from zope.app.renderer.rest import ReStructuredTextSourceFactory
from zope.app.renderer.rest import IReStructuredTextSource
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer
from zope.app.testing import placelesssetup, setup, ztapi

from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.codemodule.interfaces import IAPIDocRootModule
from zope.app.apidoc.codemodule.codemodule import CodeModule
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
  <include package="zope.app" file="meta.zcml" />
  <include package="zope.app.apidoc" file="meta.zcml" />
  <include package="zope.app" file="menus.zcml" />
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
        os.path.dirname(zope.app.__file__), 'meta.zcml')

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


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            setUp=setUp, tearDown=tearDown,
            globs={'pprint': doctestunit.pprint},
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        doctest.DocTestSuite(
            'zope.app.apidoc.codemodule.browser.menu',
            setUp=setUp, tearDown=tearDown,
            globs={'pprint': doctestunit.pprint},
            optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(default="test_suite")

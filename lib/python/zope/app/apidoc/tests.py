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
"""Tests for the Interface Documentation Module

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""
from pprint import PrettyPrinter
import unittest

import zope.component.testing
from zope.component.interfaces import IFactory
from zope.interface import implements
from zope.testing import doctest, doctestunit
from zope.traversing.interfaces import IContainmentRoot
from zope.location import LocationProxy

from zope.app.testing import placelesssetup, ztapi, setup
from zope.app.renderer.rest import ReStructuredTextSourceFactory
from zope.app.renderer.rest import IReStructuredTextSource
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer


def setUp(test):
    zope.component.testing.setUp()
    # Register Renderer Components
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.rest')
    ztapi.browserView(IReStructuredTextSource, '',
                      ReStructuredTextToHTMLRenderer)
    # Cheat and register the ReST renderer as the STX one as well.
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.stx')
    ztapi.browserView(IReStructuredTextSource, '',
                      ReStructuredTextToHTMLRenderer)
    setup.setUpTestAsModule(test, 'zope.app.apidoc.doctest')


def tearDown(test):
    placelesssetup.tearDown()
    setup.tearDownTestAsModule(test)

# Generally useful classes and functions

class Root:
    implements(IContainmentRoot)

    __parent__ = None
    __name__ = ''

def rootLocation(obj, name):
    return LocationProxy(obj, Root(), name)


def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.app.apidoc.browser.apidoc',
                             setUp=setUp, tearDown=placelesssetup.tearDown),
        doctest.DocFileSuite('README.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('classregistry.txt',
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('interface.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('component.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('presentation.txt',
                             setUp=zope.component.testing.setUp,
                             tearDown=zope.component.testing.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('utilities.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

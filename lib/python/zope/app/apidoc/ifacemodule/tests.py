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

$Id: tests.py 65511 2006-02-27 05:24:24Z philikon $
"""
import unittest

from zope.component.interfaces import IFactory
from zope.interface.interfaces import IInterface
from zope.testing import doctest, doctestunit

from zope.app.renderer.rest import ReStructuredTextSourceFactory
from zope.app.renderer.rest import IReStructuredTextSource
from zope.app.renderer.rest import ReStructuredTextToHTMLRenderer
from zope.app.testing import placelesssetup, ztapi, setup
from zope.app.tree.interfaces import IUniqueId
from zope.app.tree.adapters import LocationUniqueId 

def setUp(test):
    placelesssetup.setUp()
    setup.setUpTraversal()
    
    ztapi.provideAdapter(IInterface, IUniqueId, LocationUniqueId)

    # Register Renderer Components
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.rest')    
    ztapi.browserView(IReStructuredTextSource, '', 
                      ReStructuredTextToHTMLRenderer)
    # Cheat and register the ReST factory for STX as well
    ztapi.provideUtility(IFactory, ReStructuredTextSourceFactory,
                         'zope.source.stx')    

    
def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('browser.txt',
                             setUp=setUp, tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")

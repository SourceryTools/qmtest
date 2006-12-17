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
"""Tests for the Utility Documentation Module

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.testing import doctest, doctestunit
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location.traversing import LocationPhysicallyLocatable

from zope.app.testing import placelesssetup, ztapi
from zope.app.tree.interfaces import IUniqueId
from zope.app.tree.adapters import LocationUniqueId 

def setUp(test):
    placelesssetup.setUp()

    ztapi.provideAdapter(None, IUniqueId, LocationUniqueId)
    ztapi.provideAdapter(None, IPhysicallyLocatable,
                         LocationPhysicallyLocatable)


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE|
                                         doctest.ELLIPSIS),
        doctest.DocFileSuite('browser.txt',
                             setUp=setUp,
                             tearDown=placelesssetup.tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(default="test_suite")

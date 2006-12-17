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
"""Tests for the ZCML Documentation Module

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""
import os
import unittest
from zope.configuration import xmlconfig
from zope.testing import doctest, doctestunit
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location.traversing import LocationPhysicallyLocatable

import zope.app.appsetup.appsetup
from zope.app.tree.interfaces import IUniqueId
from zope.app.tree.adapters import LocationUniqueId
from zope.app.testing import placelesssetup, ztapi

from zope.app.apidoc.tests import Root
from zope.app.apidoc.zcmlmodule import Namespace, Directive
from zope.app.apidoc.zcmlmodule import ZCMLModule
from zope.app.apidoc.tests import Root


def setUp(test):
    placelesssetup.setUp()

    ztapi.provideAdapter(None, IUniqueId, LocationUniqueId)
    ztapi.provideAdapter(None, IPhysicallyLocatable,
                         LocationPhysicallyLocatable)

    config_file = os.path.join(os.path.dirname(zope.app.__file__), 'meta.zcml')

    # Fix up path for tests.
    global old_context
    old_context = zope.app.appsetup.appsetup.getConfigContext()
    zope.app.appsetup.appsetup.__config_context = xmlconfig.file(
        config_file, execute=False)

def tearDown(test):
    placelesssetup.tearDown()
    zope.app.appsetup.appsetup.__config_context = old_context
    from zope.app.apidoc import zcmlmodule
    zcmlmodule.namespaces = None
    zcmlmodule.subdirs = None

def getDirective():
    module = ZCMLModule()
    module.__parent__ = Root()
    module.__name__ = 'ZCML'

    def foo(): pass

    ns = Namespace(module, 'http://namespaces.zope.org/browser')
    return Directive(ns, 'page', None, foo, None, ())


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('browser.txt',
                             setUp=setUp, tearDown=tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(default='test_suite')

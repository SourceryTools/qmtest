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

$Id: tests.py 71649 2006-12-23 14:17:45Z baijum $
"""
import os
import unittest
from zope.configuration import xmlconfig
from zope.testing import doctest, doctestunit

import zope.app.appsetup.appsetup
from zope.app.testing import placelesssetup


def setUp(test):
    placelesssetup.setUp()

    meta = '''
    <configure
        xmlns:meta="http://namespaces.zope.org/meta"
        i18n_domain="zope">
      <meta:provides feature="devmode" />
      <include package="zope.app.zcmlfiles" file="meta.zcml" />
      <include package="zope.app.zcmlfiles" file="menus.zcml" />
    </configure>
    '''
    xmlconfig.string(meta)

    meta = os.path.join(os.path.dirname(zope.app.zcmlfiles.__file__), 'meta.zcml')
    context = xmlconfig.file(meta, zope.app.zcmlfiles)
    context.provideFeature('devmode')
    meta = os.path.join(os.path.dirname(zope.app.apidoc.__file__), 'meta.zcml')
    context = xmlconfig.file(meta, zope.app.apidoc, context)

    # Fix up path for tests.
    global old_context
    old_context = zope.app.appsetup.appsetup.__config_context
    zope.app.appsetup.appsetup.__config_context = context

def tearDown(test):
    placelesssetup.tearDown()
    global old_context
    zope.app.appsetup.appsetup.__config_context = old_context


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=tearDown,
                             globs={'pprint': doctestunit.pprint},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        doctest.DocFileSuite('directives.txt',
                             setUp=placelesssetup.setUp,
                             tearDown=placelesssetup.tearDown),
        ))

if __name__ == '__main__':
    unittest.main(default="test_suite")

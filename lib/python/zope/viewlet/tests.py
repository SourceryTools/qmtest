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
"""Viewlet tests

$Id: tests.py 70028 2006-09-07 13:40:42Z flox $
"""
__docformat__ = 'restructuredtext'

import unittest
import zope.component
import zope.interface
import zope.security
from zope.testing import doctest
from zope.testing.doctestunit import DocTestSuite, DocFileSuite
from zope.app.testing import setup

class TestParticipation(object):
    principal = 'foobar'
    interaction = None

def setUp(test):
    setup.placefulSetUp()

    # resource namespace setup
    from zope.traversing.interfaces import ITraversable
    from zope.traversing.namespace import resource
    zope.component.provideAdapter(
        resource, (None,), ITraversable, name = "resource")
    zope.component.provideAdapter(
        resource, (None, None), ITraversable, name = "resource")

    from zope.app.pagetemplate import metaconfigure
    from zope.contentprovider import tales
    metaconfigure.registerType('provider', tales.TALESProviderExpression)

    zope.security.management.getInteraction().add(TestParticipation())

def directivesSetUp(test):
    setUp(test)
    setup.setUpTestAsModule(test, 'zope.viewlet.directives')


def tearDown(test):
    setup.placefulTearDown()

def directivesTearDown(test):
    tearDown(test)
    setup.tearDownTestAsModule(test)


def test_suite():
    return unittest.TestSuite((
        DocFileSuite('README.txt',
                     setUp=setUp, tearDown=tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     ),
        DocFileSuite('directives.txt',
                     setUp=directivesSetUp, tearDown=directivesTearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

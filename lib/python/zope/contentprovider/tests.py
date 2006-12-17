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

$Id: tests.py 39606 2005-10-25 02:59:26Z srichter $
"""
__docformat__ = 'restructuredtext'
import os.path
import unittest
import zope.interface
import zope.security
from zope.testing import doctest
from zope.testing.doctestunit import DocTestSuite, DocFileSuite
from zope.app.testing import setup

from zope.contentprovider import interfaces


class TestParticipation(object):
    principal = 'foobar'
    interaction = None

counter = 0
mtime_func = None

def setUp(test):
    setup.placefulSetUp()

    from zope.app.pagetemplate import metaconfigure
    from zope.contentprovider import tales
    metaconfigure.registerType('provider', tales.TALESProviderExpression)

    zope.security.management.getInteraction().add(TestParticipation())

    # Make sure we are always reloading page template files ;-)
    global mtime_func
    mtime_func = os.path.getmtime
    def number(x):
        global counter
        counter += 1
        return counter
    os.path.getmtime = number


def tearDown(test):
    setup.placefulTearDown()
    os.path.getmtime = mtime_func
    global counter
    counter = 0

def test_suite():
    return unittest.TestSuite((
        DocFileSuite('README.txt',
                     setUp=setUp, tearDown=tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

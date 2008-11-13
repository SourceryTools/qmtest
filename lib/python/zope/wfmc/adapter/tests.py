##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test hookup

$Id: tests.py 30314 2005-05-09 17:07:09Z jim $
"""
import os
import unittest
import zope.event
from zope.component import testing
from zope.testing import doctest

def tearDown(test):
    testing.tearDown(test)
    zope.event.subscribers.pop()

def setUp(test):
    test.globs['this_directory'] = os.path.dirname(__file__)
    testing.setUp(test)

def test_suite():
    return doctest.DocFileSuite('integration.txt',
                                setUp=testing.setUp, tearDown=tearDown)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

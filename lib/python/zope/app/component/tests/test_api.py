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
"""Registration Tests

$Id: test_api.py 70826 2006-10-20 03:41:16Z baijum $
"""
__docformat__ = "reStructuredText"
import unittest

from zope.testing import doctest
from zope.app.testing import setup

def setUp(test):
    setup.placefulSetUp()

def tearDown(test):
    setup.placefulTearDown()

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../README.txt',
                             setUp=setUp, tearDown=tearDown),
        ))

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
    

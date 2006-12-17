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
"""Test zope.publisher.browser doctests

$Id: test_browser.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite

__docformat__ = "reStructuredText"

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.publisher.browser'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

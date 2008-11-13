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

$Id: test_browser.py 72134 2007-01-20 13:04:08Z mgedmin $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.app.testing import setup

__docformat__ = "reStructuredText"

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.publisher.browser',
                     setUp=setup.placelessSetUp,
                     tearDown=setup.placelessTearDown),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

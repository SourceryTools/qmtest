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
"""Tests for the Book Documentation Module

$Id: tests.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.app.testing import placelesssetup

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.app.apidoc.typemodule.type',
                     setUp=placelesssetup.setUp,
                     tearDown=placelesssetup.tearDown),
        ))

if __name__ == '__main__':
    unittest.main(default='test_suite')

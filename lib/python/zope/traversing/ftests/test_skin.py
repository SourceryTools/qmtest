##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Functional tests for skin traversing

$Id: test_skin.py 68699 2006-06-17 03:29:43Z ctheune $
"""
import unittest
from zope.app.testing import functional
from zope.publisher.interfaces import NotFound

class TestSkin(functional.BrowserTestCase):

    def test_missing_skin(self):
        self.assertRaises(NotFound, self.publish, "/++skin++missingskin")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSkin))
    return suite


if __name__ == '__main__':
    unittest.main()

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Test 'rdb' ZCML Namespace Directives

$Id: test_gadflyrootdirective.py 70826 2006-10-20 03:41:16Z baijum $
"""

import os
import unittest

from zope.configuration import xmlconfig

import zope.rdb.tests
from zope.rdb.gadflyda import getGadflyRoot

class DirectiveTest(unittest.TestCase):

    def test_gadflyRoot(self):

        self.assertEqual(getGadflyRoot(), 'gadfly')
        self.context = xmlconfig.file("gadflyroot.zcml", zope.rdb.tests)
        self.assert_(
            os.path.join('zope', 'rdb', 'tests', 'test', 'dir')
            in getGadflyRoot()
            )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectiveTest),
        ))

if __name__ == '__main__':
    unittest.main()

##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Context Tests

$Id: test_decorator.py 78753 2007-08-12 09:38:54Z ctheune $
"""
import unittest
from zope.testing import doctest

def test_suite():
    suite = doctest.DocTestSuite()
    suite.addTest(doctest.DocTestSuite('zope.security.decorator'))
    return suite


if __name__ == '__main__':
    unittest.main()

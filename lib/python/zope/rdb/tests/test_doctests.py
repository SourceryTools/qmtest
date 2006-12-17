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
"""Test RDB implementation

$Id: test_doctests.py 66859 2006-04-11 17:32:49Z jinty $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite

def test_suite():
    return DocTestSuite('zope.rdb')

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

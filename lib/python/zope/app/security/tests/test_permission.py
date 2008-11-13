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
"""Doctests for 'permission' module.

$Id: test_permission.py 26201 2004-07-08 10:42:46Z srichter $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.app.security.permission'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


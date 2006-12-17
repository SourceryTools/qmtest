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
"""Untrusted python tests

$Id: tests.py 26819 2004-07-28 19:37:35Z jim $
"""
import unittest
from zope.testing import doctestunit

def test_suite():
    return unittest.TestSuite((
        doctestunit.DocFileSuite('builtins.txt',
                                 'rcompile.txt',
                                 'interpreter.txt',
                                 ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


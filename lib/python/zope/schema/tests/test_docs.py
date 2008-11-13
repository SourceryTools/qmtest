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
"""Tests for the schema package's documentation files

$Id: test_docs.py 70826 2006-10-20 03:41:16Z baijum $
"""
import unittest
from zope.testing import doctest

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../sources.txt', optionflags=doctest.ELLIPSIS),
        doctest.DocFileSuite('../fields.txt'),
        doctest.DocFileSuite('../README.txt'),
        ))

if __name__ == '__main__':
    unittest.main(default='test_suite')

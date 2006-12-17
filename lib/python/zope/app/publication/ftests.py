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
"""Test not found errors

$Id: ftests.py 39083 2005-10-11 23:09:36Z srichter $
"""
import unittest
from zope.app.testing import functional

def test_suite():
    return unittest.TestSuite((
        functional.FunctionalDocFileSuite('notfound.txt'),
        functional.FunctionalDocFileSuite('methodnotallowed.txt'),
        functional.FunctionalDocFileSuite('httpfactory.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


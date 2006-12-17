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
"""Int Id Utility Functional Tests

$Id: ftests.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.app.testing import functional

def test_suite():
    return unittest.TestSuite((
        functional.FunctionalDocFileSuite('tracking.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


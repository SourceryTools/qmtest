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
"""Generation-browser tests

$Id: tests.py 28597 2004-12-09 17:52:40Z srichter $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.app.generations.browser.managers'),
        DocTestSuite('zope.app.generations.browser.managerdetails'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


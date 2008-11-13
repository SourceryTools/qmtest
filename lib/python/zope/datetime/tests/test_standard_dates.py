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
"""Tests standard date parsing

$Id: test_standard_dates.py 68457 2006-06-02 11:03:06Z hdima $
"""
import unittest

from zope.datetime import time

class Test(unittest.TestCase):

    def testiso8601_date(self):
        from zope.datetime import iso8601_date
        self.assertEqual(iso8601_date(time("2000-01-01T01:01:01.234Z")),
                         "2000-01-01T01:01:01Z")

    def testrfc850_date(self):
        from zope.datetime import rfc850_date
        self.assertEqual(rfc850_date(time("2002-01-12T01:01:01.234Z")),
                         "Saturday, 12-Jan-02 01:01:01 GMT")

    def testrfc1123_date(self):
        from zope.datetime import rfc1123_date
        self.assertEqual(rfc1123_date(time("2002-01-12T01:01:01.234Z")),
                         "Sat, 12 Jan 2002 01:01:01 GMT")

def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

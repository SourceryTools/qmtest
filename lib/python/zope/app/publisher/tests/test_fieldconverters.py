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
"""Test of field converters.

$Id: test_fieldconverters.py 26560 2004-07-15 21:38:42Z srichter $
"""
from unittest import TestCase, TestSuite, main, makeSuite
from datetime import datetime

class TestFieldConverters(TestCase):

    def test_field2date_dateonly(self):

        from zope.app.publisher.fieldconverters \
            import field2date_via_datetimeutils

        dt = field2date_via_datetimeutils('2003/05/04')
        self.failUnless(isinstance(dt, datetime))
        self.assertEqual(dt.year, 2003)
        self.assertEqual(dt.month, 5)
        self.assertEqual(dt.day, 4)
        self.assertEqual(dt.hour, 0)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.tzinfo, None)

    def test_field2date_timestamp(self):

        from zope.app.publisher.fieldconverters \
            import field2date_via_datetimeutils

        dt = field2date_via_datetimeutils('2003/05/04 19:26:54')
        self.failUnless(isinstance(dt, datetime))
        self.assertEqual(dt.year, 2003)
        self.assertEqual(dt.month, 5)
        self.assertEqual(dt.day, 4)
        self.assertEqual(dt.hour, 19)
        self.assertEqual(dt.minute, 26)
        self.assertEqual(dt.second, 54)
        self.assertEqual(dt.tzinfo, None)

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestFieldConverters))
    return suite


if __name__ == '__main__':
    main()

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
"""Test for the 'tzinfo() function 

$Id: test_tzinfo.py 66343 2006-04-03 04:59:49Z philikon $
"""

from unittest import TestCase, TestSuite, main, makeSuite
import pickle
import datetime

from zope.datetime import tzinfo
class Test(TestCase):

    def test(self):

        for minutes in 1439, 600, 1, 0, -1, -600, -1439:
            info1 = tzinfo(minutes)
            info2 = tzinfo(minutes)

            self.assertEqual(info1, info2)
            self.assert_(info1 is info2)
            self.assert_(pickle.loads(pickle.dumps(info1)) is info1)


            self.assertEqual(info1.utcoffset(None),
                             datetime.timedelta(minutes=minutes))

            self.assertEqual(info1.dst(None), None)
            self.assertEqual(info1.tzname(None), None)

        for minutes in 900000, 1440*60, -1440*60, -900000:
            self.assertRaises(ValueError, tzinfo, minutes)



def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

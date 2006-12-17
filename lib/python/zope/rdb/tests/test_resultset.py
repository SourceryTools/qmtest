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
"""ResultSet unit tests.

$Id: test_resultset.py 66859 2006-04-11 17:32:49Z jinty $
"""

from unittest import TestCase, TestSuite, main, makeSuite

class TestResultSet(TestCase):

    def testPickling(self):
        from zope.rdb import ResultSet
        from pickle import dumps, loads

        columns = ('foo', 'bar')
        rows =  (('1', '2'), ('3', '4'))
        rs = ResultSet(columns, rows)

        pickled = dumps(rs)
        unpickled = loads(pickled)

        #self.assertEqual(unpickled.columns, rs.columns)
        self.assertEqual(rs, unpickled)

    def test__cmp__(self):
        from zope.rdb import ResultSet
        from copy import deepcopy

        # See if equal to a copy
        columns = ('foo', 'bar')
        rows =  (('1', '2'), ('3', '4'))
        rs1 = ResultSet(columns, rows)
        rs2 = ResultSet(deepcopy(columns), deepcopy(rows))
        self.assertEqual(rs1, rs2, "deep copy not equal")
        self.assertEqual(rs1, rs1, "not equal to self")

        # Test if the columns are different
        columns1 = ('foo', 'bar')
        rows =  (('1', '2'), ('3', '4'))
        rs1 = ResultSet(columns1, rows)
        columns2 = ('Foo', 'Bar')
        rs2 = ResultSet(columns2, rows)
        self.assert_(rs1 > rs2, "different columns compared incorrectly")

        # Test if the data is different
        columns = ('foo', 'bar')
        rows1 =  (('1', '2'), ('3', '4'))
        rows2 =  (('2', '2'), ('3', '4'))
        rs1 = ResultSet(columns, rows1)
        rs2 = ResultSet(columns, rows2)
        self.assert_(rs1 < rs2, "different columns compared incorrectly")



def test_suite():
    return TestSuite((
        makeSuite(TestResultSet),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

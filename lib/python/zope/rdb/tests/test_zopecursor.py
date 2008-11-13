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
"""Test Zope Cursor component

$Id: test_zopecursor.py 72141 2007-01-20 13:32:07Z mgedmin $
"""
from unittest import TestCase, main, makeSuite

import transaction
from zope.rdb import ZopeConnection
from zope.rdb import ZopeCursor
from zope.rdb.tests.stubs import *


class MyConnectionStub(ConnectionStub):
    def cursor(self):
        return MyCursorStub()

class MyConnectionStub2(ConnectionStub):
    def cursor(self):
        return MyCursorStub2()


raw       = [['mano',      2,    'buvo batai'],
             ['dingo',     1,    'nerandu'],
             ['as su',     1,    'batuku'],
             ['eiti i',    None, 'galiu']]

converted = [['my',        42,   'shoes were'],
             ['were lost', 41,   "can't find"],
             ['with',      41,   'shoe'],
             ['go to',     None, 'I can']]


class MyCursorStub(CursorStub):

    _raw = raw

    description = ((None, 'string'), (None, 'int'), (None, 'foo'))

    def execute(self, query, args=None):
        self.method = "execute"
        self.query = query
        self.args = args

    def fetchone(self):
        if self._raw:
            return self._raw[0]
        else:
            return None

    def fetchall(self):
        return self._raw

    def fetchmany(self, size=2):
        return self._raw[:size]

class MyCursorStub2(MyCursorStub):

    def executemany(self, query, args):
        self.method = "executemany"
        self.query = query
        self.args = args


class MyTypeInfoStub(TypeInfoStub):

    def getConverter(self, type):

        def stringConverter(x):
            return {'mano': 'my',
                    'dingo': 'were lost',
                    'as su': 'with',
                    'eiti i': 'go to'}[x]

        def intConverter(x):
            if x is None:
                return None
            else:
                return x + 40

        def fooConverter(x):
            return {'buvo batai': 'shoes were',
                    'nerandu': "can't find",
                    'batuku': 'shoe',
                    'galiu': 'I can'}[x]

        return {'string': stringConverter,
                'int': intConverter,
                'foo': fooConverter}[type]


class ZopeCursorTests(TestCase):

    def setUp(self):
        self.typeInfo = MyTypeInfoStub()
        zc = ZopeConnection(MyConnectionStub(), self.typeInfo)
        self.cursor = ZopeCursor(zc.conn.cursor(), zc)

    def tearDown(self):
        transaction.abort()

    def test_cursor_fetchone(self):
        results = self.cursor.fetchone()
        expected = converted[0]
        self.assertEqual(results, expected,
                   'type conversion was not performed in cursor.fetchone:\n'
                   'got %r, expected %r' % (results, expected))

    def test_cursor_fetchone_no_more_results(self):
        self.cursor.cursor._raw = []
        results = self.cursor.fetchone()
        expected = None
        self.assertEqual(results, expected,
                   'type conversion was not performed in cursor.fetchone:\n'
                   'got %r, expected %r' % (results, expected))

    def test_cursor_fetchmany(self):
        results = self.cursor.fetchmany()
        expected = converted[:2]
        self.assertEqual(results, expected,
                   'type conversion was not performed in cursor.fetchmany:\n'
                   'got      %r,\n'
                   'expected %r' % (results, expected))

    def test_cursor_fetchall(self):
        results = self.cursor.fetchall()
        expected = converted
        self.assertEqual(results, expected,
                   'type conversion was not performed in cursor.fetchall:\n'
                   'got      %r,\n'
                   'expected %r' % (results, expected))

    def test_cursor_executemany(self):
        self.cursor.executemany("SELECT", [("A",), ("B",)])
        self.assertEqual("execute", self.cursor.cursor.method)
        self.assertEqual("SELECT", self.cursor.cursor.query)
        self.assertEqual([("A",), ("B",)], self.cursor.cursor.args)

        zc = ZopeConnection(MyConnectionStub2(), self.typeInfo)
        self.cursor = ZopeCursor(zc.conn.cursor(), zc)
        self.cursor.executemany("SELECT", [("A",), ("B",)])
        self.assertEqual("executemany", self.cursor.cursor.method)
        self.assertEqual("SELECT", self.cursor.cursor.query)
        self.assertEqual([("A",), ("B",)], self.cursor.cursor.args)

    def test_cursor_query_encoding(self):
        self.cursor.execute(u'\u0422\u0435\u0441\u0442')
        self.assertEqual('\xd0\xa2\xd0\xb5\xd1\x81\xd1\x82',
            self.cursor.cursor.query)

        self.typeInfo.setEncoding("windows-1251")
        self.cursor.execute(u'\u0422\u0435\u0441\u0442')
        self.assertEqual('\xd2\xe5\xf1\xf2', self.cursor.cursor.query)

    def test_cursor_tuple_args_encoding(self):
        self.typeInfo.setEncoding("windows-1251")
        self.cursor.execute("SELECT * FROM table",
            (u'\u0422\u0435\u0441\u0442',))
        self.assertEqual(('\xd2\xe5\xf1\xf2',), self.cursor.cursor.args)

    def test_cursor_list_args_encoding(self):
        self.typeInfo.setEncoding("windows-1251")
        self.cursor.execute(u'\u0422\u0435\u0441\u0442',
            [u'\u0422\u0435\u0441\u0442'])
        self.assertEqual('\xd2\xe5\xf1\xf2', self.cursor.cursor.query)
        self.assertEqual(['\xd2\xe5\xf1\xf2'], self.cursor.cursor.args)

        self.cursor.execute("SELECT * FROM table",
            [(u'\u0422\u0435\u0441\u0442',)])
        self.assertEqual([('\xd2\xe5\xf1\xf2',)], self.cursor.cursor.args)

        self.cursor.execute("SELECT * FROM table",
            [[u'\u0422\u0435\u0441\u0442']])
        self.assertEqual([['\xd2\xe5\xf1\xf2']], self.cursor.cursor.args)

        self.cursor.execute("SELECT * FROM table",
            [{"value": u'\u0422\u0435\u0441\u0442'}])
        self.assertEqual([{"value": '\xd2\xe5\xf1\xf2'}],
            self.cursor.cursor.args)

    def test_cursor_dict_args_encoding(self):
        self.typeInfo.setEncoding("windows-1251")
        self.cursor.execute("SELECT * FROM table",
            {"value": u'\u0422\u0435\u0441\u0442'})
        self.assertEqual({"value": '\xd2\xe5\xf1\xf2'},
            self.cursor.cursor.args)


def test_suite():
    return makeSuite(ZopeCursorTests)

if __name__=='__main__':
    main(defaultTest='test_suite')

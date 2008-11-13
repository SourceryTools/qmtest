##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Gadfly Database adapter phatom tests

$Id: test_gadflyphantom.py 72141 2007-01-20 13:32:07Z mgedmin $
"""
__docformat__ = 'restructuredtext'
import os, shutil
import tempfile, threading
from unittest import TestCase, TestSuite, main, makeSuite

import transaction
from zope.rdb.gadflyda import GadflyAdapter, setGadflyRoot

class GadflyTestBase(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.tempdir = None

    def tearDown(self):
        TestCase.tearDown(self)
        if self.tempdir:
            shutil.rmtree(self.tempdir)
        setGadflyRoot()

    def getGadflyRoot(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp('gadfly')
        setGadflyRoot(self.tempdir)
        return self.tempdir

    def _create(self, *args):
        return GadflyAdapter(*args)

def exec_sql(adapter, sql, args, fetch=False):

    conn = adapter()
    cur =conn.cursor()
    cur.execute(sql, args)
    rows = []
    if fetch:
        rows = cur.fetchall()
    conn.commit()
    return rows

class TestPhantom(GadflyTestBase):

    def setUp(self):
        GadflyTestBase.setUp(self)
        dir = self.getGadflyRoot()
        os.mkdir(os.path.join(dir, "demo"))
        self.adapter = self._create("dbi://demo")
        conn = self.adapter()
        cur = conn.cursor()
        cur.execute("create table t1 (name varchar)")
        conn.commit()

    def tearDown(self):
        GadflyTestBase.tearDown(self)
        transaction.abort()

    def test_Phantom(self):

        adapter = self.adapter
        insert = "insert into t1 values (?)"
        select = "select name from t1"
        delete = "delete from t1"

        count = 0
        for name in ('a', 'b', 'c'):
            t = threading.Thread(target=exec_sql,
                                 args=(adapter, insert, (name,)))
            t.start()
            t.join()
            rows = exec_sql(adapter, select, args=(), fetch=True)
            count += 1
            self.assertEqual(len(rows), count)

        exec_sql(adapter, delete, args=())
        t = threading.Thread(target=exec_sql,
                             args=(adapter, delete, ()))
        t.start()
        t.join()
        rows = exec_sql(adapter, select, args=(), fetch=True)
        self.assertEqual(len(rows), 0)

def test_suite():
    return TestSuite((
        makeSuite(TestPhantom),
        ))

if __name__=='__main__':

    main(defaultTest='test_suite')

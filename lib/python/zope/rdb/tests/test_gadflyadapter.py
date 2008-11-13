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
"""Gadfly database adapter unit tests.

$Id: test_gadflyadapter.py 72141 2007-01-20 13:32:07Z mgedmin $
"""
import os
import tempfile
from unittest import TestCase, TestSuite, main, makeSuite

import transaction
from zope.interface.verify import verifyObject

from zope.rdb import DatabaseAdapterError
from zope.rdb.interfaces import IZopeConnection, IZopeCursor
from zope.rdb.gadflyda import GadflyAdapter, setGadflyRoot


class GadflyTestBase(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.tempdir = None

    def tearDown(self):
        TestCase.tearDown(self)
        if self.tempdir:
            os.rmdir(self.tempdir)
        setGadflyRoot()

    def getGadflyRoot(self):
        # note that self is GadflyTestBase here
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp('gadfly')
        setGadflyRoot(self.tempdir)
        return self.tempdir

    def _create(self, *args):
        return GadflyAdapter(*args)


class TestGadflyAdapter(GadflyTestBase):
    """Test incorrect connection strings"""

    def test__connection_factory_nonexistent(self):
        # Should raise an exception on nonexistent dirs.
        a = self._create("dbi://demo;dir=nonexistent")
        self.assertRaises(DatabaseAdapterError, a._connection_factory)

    def test__connection_factory_bad_dsn(self):
        a = self._create("dbi://user:pass/demo;dir=nonexistent")
        self.assertRaises(DatabaseAdapterError, a._connection_factory)

        a = self._create("dbi://localhost:1234/demo;dir=nonexistent")
        self.assertRaises(DatabaseAdapterError, a._connection_factory)


class TestGadflyAdapterNew(GadflyTestBase):
    """Test with nonexistent databases"""

    def test__connection_factory_create(self):
        # Should create a database if the directory is empty.
        a = self._create("dbi://demo;dir=test")
        conn = a._connection_factory()
        conn.rollback()         # is it really a connection?

    def test__connection_factory_existing(self):
        # Should fail gracefully if the directory is a file.
        open(os.path.join(self.getGadflyRoot(), "regular"), "w").close()
        a = self._create("dbi://demo;dir=regular")
        self.assertRaises(DatabaseAdapterError, a._connection_factory)

    def setUp(self):
        # Create a directory for the database.
        GadflyTestBase.setUp(self)
        dir = self.getGadflyRoot()
        os.mkdir(os.path.join(dir, "test"))

    def tearDown(self):
        # Remove the files and directories created.
        dir = self.getGadflyRoot()
        try: os.unlink(os.path.join(dir, "test", "demo.gfd"))
        except: pass
        os.rmdir(os.path.join(dir, "test"))
        try:
            os.unlink(os.path.join(dir, "regular"))
        except:
            pass
        GadflyTestBase.tearDown(self)


class TestGadflyAdapterDefault(GadflyTestBase):
    """Test with pre-existing databases"""

    def setUp(self):
        # Create a directory for the database.
        GadflyTestBase.setUp(self)
        dir = self.getGadflyRoot()
        os.mkdir(os.path.join(dir, "demo"))

    def tearDown(self):
        # Remove the files and directories created.
        dir = self.getGadflyRoot()
        try:
            os.unlink(os.path.join(dir, "demo", "demo.gfd"))
        except:
            pass
        os.rmdir(os.path.join(dir, "demo"))
        GadflyTestBase.tearDown(self)

    def test__connection_factory_create(self):
        # Should create a database if the directory is empty.
        a = self._create("dbi://demo")
        conn = a._connection_factory()
        conn.rollback()         # is it really a connection?

    def test__connection_factory_reopen(self):
        # Should open an existing database.
        a = self._create("dbi://demo")
        conn = a._connection_factory()
        conn.rollback()         # is it really a connection?
        conn.close()

        conn = a._connection_factory()
        conn.rollback()         # is it really a connection?

    def test__interfaces(self):
        a = self._create("dbi://demo")
        connection = a()
        verifyObject(IZopeConnection, connection)
        cursor = connection.cursor()
        verifyObject(IZopeCursor, cursor)

class GadflyCursorStub(object):

    def __init__(self):
        self.operations = []

    def execute(self, operation, parameters=None):
        self.operations.append((operation, parameters))

class GadflyConnectionStub(object):

    def cursor(self):
        return GadflyCursorStub()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

class GadflyTestAdapter(GadflyAdapter):

    def _connection_factory(self):
        return GadflyConnectionStub()

class GadflyAdapterTests(TestCase):

    def setUp(self):
        self.adapter = GadflyTestAdapter("dbi://")
        self.connection = self.adapter()
        self.cursor = self.connection.cursor()

    def tearDown(self):
        transaction.abort()

    def testBadExecutemanyOperations(self):
        raises = self.assertRaises
        for operation in [
                "SELECT",
                "CREATE",
                "DROP",
                ]:
            raises(DatabaseAdapterError,
                self.cursor.executemany, operation, [])

    def testExecutemanyInsert(self):
        operation = "INSERT INTO table(v1, v2) VALUES (?, ?)"
        parameters = [(1, 2), (3, 4)]
        self.cursor.executemany(operation, parameters)
        self.failUnlessEqual([(operation, parameters)],
            self.cursor.operations)

    def testExecutemanyUpdate(self):
        operation = "UPDATE table SET value=0 WHERE id=?"
        parameters = [(1,), (2,)]
        self.cursor.executemany(operation, parameters)
        self.failUnlessEqual([
            (operation, parameters[0]),
            (operation, parameters[1]),
            ], self.cursor.operations)

    def testExecutemanyDelete(self):
        operation = "DELETE FROM table WHERE id=?"
        parameters = [(1,), (2,)]
        self.cursor.executemany(operation, parameters)
        self.failUnlessEqual([
            (operation, parameters[0]),
            (operation, parameters[1]),
            ], self.cursor.operations)


def test_suite():
    return TestSuite((
        makeSuite(TestGadflyAdapter),
        makeSuite(TestGadflyAdapterNew),
        makeSuite(TestGadflyAdapterDefault),
        makeSuite(GadflyAdapterTests),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

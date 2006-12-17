##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""DT_SQLVar Tests

$Id: test_sqlscript.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from zope.interface import implements, classImplements
from zope.component.testing import PlacelessSetup
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.annotation.interfaces import IAnnotatable, IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations
from zope.rdb.interfaces import IZopeDatabaseAdapter
from zope.rdb.interfaces import IZopeConnection, IZopeCursor

from zope.app.testing import ztapi
from zope.app.cache.interfaces import ICacheable, ICache
from zope.app.cache.annotationcacheable import AnnotationCacheable
from zope.app.cache.caching import getCacheForObject

from zope.app.sqlscript.sqlscript import SQLScript, Arguments
from zope.app.sqlscript.interfaces import ISQLScript


class CursorStub(object):

    implements(IZopeCursor)

    description = (('name', 'string'), ('counter', 'int'))
    count = 0

    def execute(self, operation, parameters=None):
        CursorStub.count += 1
        self.result = {"SELECT name, counter FROM Table WHERE id = 1":
                       (('stephan', CursorStub.count),),
                       "SELECT name, counter FROM Table WHERE id = 2":
                       (('marius', CursorStub.count),),
                       "SELECT name, counter FROM Table WHERE id = 3":
                       (('erik', CursorStub.count),)
                      }[operation]

    def fetchall(self):
        return self.result



class ConnectionStub(object):
    implements(IZopeConnection)

    def cursor(self):
        return CursorStub()


class ConnectionUtilityStub(object):
    implements(IZopeDatabaseAdapter)

    def __init__(self):
        self.connection = ConnectionStub()

    def __call__(self):
        return  self.connection


class CacheStub(object):
    implements(ICache)
    def __init__(self):
        self.cache = {}

    def set(self, data, obj, key=None):
        if key:
            keywords = key.items()
            keywords.sort()
            keywords = tuple(keywords)
        self.cache[obj, keywords] = data

    def query(self, obj, key=None, default=None):
        if key:
            keywords = key.items()
            keywords.sort()
            keywords = tuple(keywords)
        return self.cache.get((obj, keywords), default)


class LocatableStub(object):

    implements(IPhysicallyLocatable)

    def __init__(self, obj):
        self.obj = obj

    def getRoot(self):
        return None

    def getPath(self):
        return str(id(self.obj))


class SQLScriptNoICacheableTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(SQLScriptNoICacheableTest, self).setUp()
        classImplements(SQLScript, IAttributeAnnotatable)
        self.connectionUtilityStub = ConnectionUtilityStub()
        ztapi.provideUtility(IZopeDatabaseAdapter, self.connectionUtilityStub,
                             'my_connection')
        ztapi.provideAdapter(ISQLScript, IPhysicallyLocatable,
                             LocatableStub)

    def _getScript(self):
        return SQLScript("my_connection",
                         "SELECT name, counter FROM Table WHERE"
                         " <dtml-sqltest id type=int>",
                         'id')

    def testConnectionName(self):
        # Test that we can still set the connection name
        # in the absence of a ICacheable adapter.
        script = self._getScript()
        self.assertEqual(getCacheForObject(script), None)
        self.assertEqual('my_connection', script.connectionName)
        script.connectionName = 'test_conn'
        self.assertEqual('test_conn', script.connectionName)

class SQLScriptTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(SQLScriptTest, self).setUp()
        classImplements(SQLScript, IAttributeAnnotatable)
        self.connectionUtilityStub = ConnectionUtilityStub()
        ztapi.provideUtility(IZopeDatabaseAdapter, self.connectionUtilityStub,
                             'my_connection')

        ztapi.provideAdapter(IAttributeAnnotatable, IAnnotations,
                             AttributeAnnotations)
        ztapi.provideAdapter(ISQLScript, IPhysicallyLocatable,
                             LocatableStub)
        ztapi.provideAdapter(IAnnotatable, ICacheable,
                             AnnotationCacheable)

    def tearDown(self):
        pass

    def _getScript(self):
        return SQLScript("my_connection",
                         "SELECT name, counter FROM Table WHERE"
                         " <dtml-sqltest id type=int>",
                         'id')

    def testGetArguments(self):
        result = Arguments({'id': {}})
        args = self._getScript().getArguments()
        self.assertEqual(args, result)

    def testGetArgumentsString(self):
        self.assertEqual('id', self._getScript().getArgumentsString())

    def testSetSource(self):
        script = self._getScript()
        script.setSource('SELECT * FROM Table')
        self.assertEqual('SELECT * FROM Table', script.getSource())

    def testGetSource(self):
        expected = ("SELECT name, counter FROM Table"
                    " WHERE <dtml-sqltest id type=int>")
        self.assertEqual(expected,
                         self._getScript().getSource())

    def testConnectionName(self):
        script = self._getScript()
        self.assertEqual('my_connection', script.connectionName)
        script.connectionName = 'test_conn'
        self.assertEqual('test_conn', script.connectionName)

    def testgetConnection(self):
        script = self._getScript()
        name = script.connectionName
        conns = script.getConnection()
        self.assertEqual(conns, self.connectionUtilityStub.connection)

    def testSQLScript(self):
        result = self._getScript()(id=1)
        self.assertEqual(result.columns, ('name','counter'))
        self.assertEqual(result[0].name, 'stephan')

    def testSQLScriptCaching(self):
        script = self._getScript()
        CursorStub.count = 0
        # no caching: check that the counter grows
        result = script(id=1)
        self.assertEqual(result[0].counter, 1)
        result = script(id=1)
        self.assertEqual(result[0].counter, 2)
        # caching: and check that the counter stays still
        AnnotationCacheable(script).setCacheId('dumbcache')
        ztapi.provideUtility(ICache, CacheStub(), 'dumbcache')
        result = script(id=1)
        self.assertEqual(result[0].counter, 3)
        result = script(id=1)
        self.assertEqual(result[0].counter, 3)
        result = script(id=2)
        self.assertEqual(result[0].counter, 4)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SQLScriptTest))
    suite.addTest(unittest.makeSuite(SQLScriptNoICacheableTest))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

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
"""DSN Parser tests

$Id: test_dsnparser.py 66859 2006-04-11 17:32:49Z jinty $
"""
import unittest
from zope.rdb import parseDSN


class TestDSNParser(unittest.TestCase):

    def testDBNameOnly(self):
        dsn = 'dbi://test'
        result = {'parameters': {}, 'dbname': 'test', 'username': '',
                  'password': '', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testDBNameWithSpecialCharacters(self):
        dsn = 'dbi://test%2Fmore+'
        result = {'parameters': {}, 'dbname': 'test/more ', 'username': '',
                  'password': '', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testDBNameAndParams(self):
        dsn = 'dbi://test;param1=value1;param2=value2'
        result = {'parameters': {'param1': 'value1', 'param2': 'value2'},
                  'dbname': 'test', 'username': '', 'password': '',
                  'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUser(self):
        dsn = 'dbi://mike/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': '', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUserPassword(self):
        dsn = 'dbi://mike:muster/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': 'muster', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUserPasswordWithSpecialCharacters(self):
        dsn = 'dbi://m+i+k+e:m%7Bu%7Dster/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'm i k e',
                  'password': 'm{u}ster', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testPasswordWithColon(self):
        dsn = 'dbi://mike:before:after/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': 'before:after', 'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUserPasswordAndParams(self):
        dsn = 'dbi://mike:muster/test;param1=value1;param2=value2'
        result = {'parameters': {'param1': 'value1', 'param2': 'value2'},
                  'dbname': 'test', 'username': 'mike', 'password': 'muster',
                  'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testParamsWithSpecialCharacters(self):
        dsn = 'dbi://test;param%40=value%21;param%23=value%24'
        result = {'parameters': {'param@': 'value!', 'param#': 'value$'},
                  'dbname': 'test', 'username': '', 'password': '',
                  'host': '', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUserAndHostWithoutPort(self):
        dsn = 'dbi://mike@bohr/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': '', 'host': 'bohr', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testUserPasswordAndHostWithoutPort(self):
        dsn = 'dbi://mike:muster@bohr/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': 'muster', 'host': 'bohr', 'port': ''}
        self.assertEqual(result, parseDSN(dsn))

    def testAllOptions(self):
        dsn = 'dbi://mike:muster@bohr:5432/test'
        result = {'parameters': {}, 'dbname': 'test', 'username': 'mike',
                  'password': 'muster', 'host': 'bohr', 'port': '5432'}
        self.assertEqual(result, parseDSN(dsn))

    def testAllOptionsAndParams(self):
        dsn = 'dbi://mike:muster@bohr:5432/test;param1=value1;param2=value2'
        result = {'parameters': {'param1': 'value1', 'param2': 'value2'},
                  'dbname': 'test', 'username': 'mike', 'password': 'muster',
                  'host': 'bohr', 'port': '5432'}
        self.assertEqual(result, parseDSN(dsn))

    def testFailures(self):
        self.assertRaises(ValueError, parseDSN, None)
        self.assertRaises(ValueError, parseDSN, 'dfi://')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDSNParser))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

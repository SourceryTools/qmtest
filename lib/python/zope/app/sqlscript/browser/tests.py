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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""DTML Page Evaluation Tests

$Id: tests.py 81155 2007-10-28 02:17:04Z srichter $
"""
import unittest
from xml.sax.saxutils import escape
from zope.testing import doctest
from zope.app.testing import setup
from zope.app.testing.functional import BrowserTestCase
from zope.app.sqlscript.sqlscript import SQLScript
from zope.app.sqlscript.testing import SQLScriptLayer


class SQLScriptTest(BrowserTestCase):

    content = u'SELECT * FROM foo'

    def addSQLScript(self):
        sqlscript = SQLScript()
        sqlscript.source = self.content
        root = self.getRootFolder()
        root['sqlscript'] = sqlscript
        self.commit()


    def testAddForm(self):
        response = self.publish(
            '/+/zope.app.sqlscript.SQLScript=',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Add a SQL Script' in body)
        self.assert_('Connection Name' in body)
        self.assert_('(no value)' in body)
        self.assert_('Arguments' in body)
        self.assert_('Source' in body)
        self.assert_('Object Name' in body)
        self.assert_('"Add"' in body)
        self.assert_('"Add and Test"' in body)
        self.checkForBrokenLinks(body, '/+/zope.app.sqlscript.SQLScript=',
                                 'mgr:mgrpw')


    def testAdd(self):
        response = self.publish(
            '/+/zope.app.sqlscript.SQLScript=',
            form={'type_name': u'zope.app.sqlscript.SQLScript',
                  'field.source': u'SELECT * FROM foo',
                  'field.connectionName.used': u'',
                  'field.connectionName': u'',
                  'add_input_name': u'sqlscript',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        root = self.getRootFolder()
        self.assert_('sqlscript' in root)
        sqlscript = root['sqlscript']
        self.assertEqual(sqlscript.source, self.content)
        self.assertEqual(sqlscript.arguments, '')
        self.assertEqual(sqlscript.connectionName, None)

        response = self.publish(
            '/+/zope.app.sqlscript.SQLScript=',
            form={'type_name': u'zope.app.sqlscript.SQLScript',
                  'field.source': u'SELECT * FROM foo',
                  'field.arguments': u'table',
                  'field.connectionName.used': u'',
                  'field.connectionName': u'',
                  'add_input_name': u'sqlscript1',
                  'UPDATE_SUBMIT': u'Add'},
            basic='mgr:mgrpw')
        root = self.getRootFolder()
        sqlscript = root['sqlscript1']
        self.assertEqual(sqlscript.source, 'SELECT * FROM foo')
        self.assertEqual(sqlscript.arguments, 'table')
        self.assertEqual(sqlscript.connectionName, None)


    def testEditForm(self):
        self.addSQLScript()
        response = self.publish(
            '/sqlscript/@@edit.html',
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Connection Name' in body)
        self.assert_('(no value)' in body)
        self.assert_('Arguments' in body)
        self.assert_('Source' in body)
        self.assert_('Connection Name' in body)
        self.assert_('"Change"' in body)
        self.assert_('"Change and Test"' in body)
        self.assert_(escape(self.content) in body)
        self.checkForBrokenLinks(body, '/sqlscript/@@edit.html', 'mgr:mgrpw')


    def testEdit(self):
        self.addSQLScript()
        response = self.publish(
            '/sqlscript/@@edit.html',
            form={'field.source': u'SELECT * FROM bar',
                  'field.connectionName.used': u'',
                  'field.connectionName': u'',
                  'UPDATE_SUBMIT': u'Change'},
            basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('Edit an SQL script' in body)
        self.assert_(escape(u'SELECT * FROM bar') in body)
        root = self.getRootFolder()
        sqlscript = root['sqlscript']
        self.assertEqual(sqlscript.source, 'SELECT * FROM bar')

    def testTestForm(self):
        self.addSQLScript()
        response = self.publish(
            '/sqlscript/@@test.html',
            basic='mgr:mgrpw')
        body = response.getBody()
        self.assert_('"Test"' in body)
        self.assert_(escape(self.content) in body)
        self.assertEqual(response.getStatus(), 200)
        self.checkForBrokenLinks(body, '/sqlscript/@@test.html', 'mgr:mgrpw')


def test_suite():
    SQLScriptTest.layer = SQLScriptLayer
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.app.sqlscript.browser.sqlscript',
                             setUp=setup.placelessSetUp,
                             tearDown=setup.placelessTearDown),
        unittest.makeSuite(SQLScriptTest),
        ))

if __name__ == '__main__': unittest.main()

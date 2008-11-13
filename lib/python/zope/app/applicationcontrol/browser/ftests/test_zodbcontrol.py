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
"""ZODB Control Tests

$Id: test_zodbcontrol.py 72480 2007-02-09 09:14:25Z baijum $
"""
import unittest
import ZODB.tests.util
from ZODB.interfaces import IDatabase
from zope.app.testing import functional
from zope import component

from zope.app.applicationcontrol.testing import ApplicationControlLayer

def setUp(test):
    test.databases = test.globs['getRootFolder']()._p_jar.db().databases
    db2 = ZODB.tests.util.DB(databases=test.databases, database_name='2')

    for name, db in test.databases.items():
        component.provideUtility(db, IDatabase, name=name)


def tearDown(test):
    for db in test.databases.values():
        db.close()


def test_suite():
    suite = unittest.TestSuite()
    zodb = functional.FunctionalDocFileSuite('zodb.txt',
                                             setUp=setUp,
                                             tearDown=tearDown)
    zodb.layer = ApplicationControlLayer
    suite.addTest(zodb)
    return suite


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

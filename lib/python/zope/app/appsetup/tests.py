##############################################################################
#
# Copyright (c) 2003, 2004 Zope Corporation and Contributors.
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
"""Bootstrap tests

$Id: tests.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
import transaction

from ZODB.tests.util import DB
from zope.testing import doctest
from zope.traversing.api import traverse

from zope.app import zapi
from zope.app.component import hooks
from zope.app.component.testing import PlacefulSetup
from zope.app.error.error import ErrorReportingUtility
from zope.app.error.interfaces import IErrorReportingUtility
from zope.app.folder import rootFolder, Folder
from zope.app.folder.interfaces import IRootFolder
from zope.app.publication.zopepublication import ZopePublication
from zope.app.component.site import LocalSiteManager

from zope.app.appsetup.bootstrap import bootStrapSubscriber
from zope.app.appsetup.bootstrap import getInformationFromEvent, \
     ensureObject, ensureUtility

from zope.app.testing import placelesssetup

class EventStub(object):

    def __init__(self, db):
        self.database = db

#
# TODO: some methods from the boostap modue are not tested
#

class TestBootstrapSubscriber(PlacefulSetup, unittest.TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)
        self.db = DB()

    def tearDown(self):
        PlacefulSetup.tearDown(self)
        self.db.close()

    def createRootFolder(self):
        cx = self.db.open()
        root = cx.root()
        self.root_folder = rootFolder()
        root[ZopePublication.root_name] = self.root_folder
        transaction.commit()
        cx.close()

    def createRFAndSM(self):
        cx = self.db.open()
        root = cx.root()
        self.root_folder = rootFolder()
        root[ZopePublication.root_name] = self.root_folder
        self.site_manager = LocalSiteManager(self.root_folder)
        self.root_folder.setSiteManager(self.site_manager)

        sub_folder = Folder()
        self.root_folder["sub_folder"] = sub_folder
        sub_site_manager = LocalSiteManager(sub_folder)
        sub_folder.setSiteManager(sub_site_manager)

        transaction.commit()
        cx.close()

    def test_notify(self):
        for setup in (lambda: None), self.createRootFolder, self.createRFAndSM:
            setup()
        bootStrapSubscriber(EventStub(self.db))
        cx = self.db.open()
        root = cx.root()
        root_folder = root.get(ZopePublication.root_name, None)
        self.assert_(IRootFolder.providedBy(root_folder))
        package_name = '/++etc++site/default'
        package = traverse(root_folder, package_name)
        cx.close()

    def test_ensureUtilityForSubSite(self):
        self.createRFAndSM()

        db, connection, root, root_folder = getInformationFromEvent(
            EventStub(self.db))

        sub_folder = root_folder['sub_folder']
        ensureUtility(sub_folder, IErrorReportingUtility,
                     'ErrorReporting', ErrorReportingUtility,
                     'ErrorReporting', asObject=True)
    
        # Make sure it was created on the sub folder, not the root folder
        got_utility = zapi.getUtility(IErrorReportingUtility, name='ErrorReporting',
                context=sub_folder)
        got_path = zapi.getPath(got_utility)
        self.assertEquals("/sub_folder/++etc++site/default/ErrorReporting", got_path)

    def test_ensureUtility(self):
        self.createRFAndSM()

        db, connection, root, root_folder = getInformationFromEvent(
            EventStub(self.db))

        # TODO: check EventSub
        root_folder = self.root_folder
        for i in range(2):
            cx = self.db.open()
            utility = ensureUtility(root_folder, IErrorReportingUtility,
                                 'ErrorReporting', ErrorReportingUtility,
                                 'ErrorReporting', asObject=True)
            if utility != None:
                name = utility.__name__
            else:
                name = None
            if i == 0:
                self.assertEqual(name, 'ErrorReporting')
            else:
                self.assertEqual(name, None)

            root = cx.root()
            root_folder = root[ZopePublication.root_name]

            package_name = '/++etc++site/default'
            package = traverse(self.root_folder, package_name)

            self.assert_(IErrorReportingUtility.providedBy(
                traverse(package, 'ErrorReporting')))
            transaction.commit()

        cx.close()

def bootstraptearDown(test):
    test.globs['db'].close()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBootstrapSubscriber))
    suite.addTest(doctest.DocTestSuite(
        'zope.app.appsetup.appsetup',
        setUp=placelesssetup.setUp, tearDown=placelesssetup.tearDown))
    suite.addTest(doctest.DocFileSuite(
        'bootstrap.txt',
        setUp=placelesssetup.setUp, tearDown=placelesssetup.tearDown,
        ))
    return suite

if __name__ == '__main__':
    unittest.main()

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
"""Onlinehelp tree view Tests

$Id$
"""
import os

from unittest import TestCase, TestLoader, TextTestRunner

from zope import component
from zope.pagetemplate.tests.util import check_xml
from zope.publisher.browser import TestRequest
from zope.app.component.testing import PlacefulSetup
from zope.app.onlinehelp.tests import util
from zope.app.onlinehelp.interfaces import IOnlineHelp, IOnlineHelpTopic
from zope.app.onlinehelp.onlinehelp import OnlineHelp
from zope.app.onlinehelp.onlinehelptopic import OnlineHelpTopic
from zope.app.onlinehelp.browser.tree import OnlineHelpTopicTreeView


def testdir():
    import zope.app.onlinehelp.tests
    return os.path.dirname(zope.app.onlinehelp.tests.__file__)


class TestOnlineHelpTopicTreeView(PlacefulSetup, TestCase):
    
    def setUp(self):
        PlacefulSetup.setUp(self, site=True)
        path = os.path.join(testdir(), 'help.txt')
        self.onlinehelp = OnlineHelp('Help', path)
        component.provideUtility(self.onlinehelp, IOnlineHelp, "OnlineHelp")

    def test_onlinehelp(self):
        view = OnlineHelpTopicTreeView
        treeView = view(self.rootFolder, TestRequest()).getTopicTree
        check_xml(treeView(), util.read_output('test1.xml'))

    def test_topics(self):
        path = os.path.join(testdir(), 'help.txt')
        
        id = 'topic1'
        title = 'Topic1'
        parentPath = ""
        topic1 = OnlineHelpTopic(id, title, path, parentPath)
        self.onlinehelp['topic1'] = topic1

        id = 'topic1_1'
        title = 'Topic1_1'
        parentPath = 'topic1'
        topic1_1 = OnlineHelpTopic(id, title, path, parentPath)
        topic1['topic1_1']  = topic1_1

        id = 'topic1_1_1'
        title = 'Topic1_1_1'
        parentPath = 'topic1/topic1_1'
        topic1_1_1 = OnlineHelpTopic(id, title, path, parentPath)
        topic1_1['topic1_1_1']  = topic1_1_1

        id = 'topic2'
        title = 'Topic2'
        parentPath = ""
        topic2 = OnlineHelpTopic(id, title, path, parentPath)
        self.onlinehelp['topic2'] = topic2
        
        view = OnlineHelpTopicTreeView
        treeView = view(self.rootFolder, TestRequest()).getTopicTree
        check_xml(treeView(), util.read_output('test2.xml'))


def test_suite():
    loader = TestLoader()
    return loader.loadTestsFromTestCase(TestOnlineHelpTopicTreeView)

if __name__=='__main__':
    TextTestRunner().run(test_suite())

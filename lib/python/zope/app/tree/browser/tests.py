##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Static Tree Tests

$Id: tests.py 68951 2006-07-02 13:02:27Z philikon $
"""

import unittest
import zope.component
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest
from zope.interface import alsoProvides
from zope.traversing.interfaces import IContainmentRoot
from zope.location.traversing import LocationPhysicallyLocatable
from zope.app.testing import ztapi
from zope.app.component.interfaces import ISite

from zope.app.tree.utils import TreeStateEncoder
from zope.app.tree.browser import StatefulTreeView
from zope.app.tree.browser.cookie import CookieTreeView
from zope.app.tree.tests.basetest import BaseTestCase

class StatefulTreeViewTest(BaseTestCase):

    def setUp(self):
        super(StatefulTreeViewTest, self).setUp()
        self.makeItems()
        # provide the view for all objects (None)
        ztapi.browserView(None, 'stateful_tree', StatefulTreeView)

    def makeRequest(self):
        request = self.request = TestRequest()

    # TODO: test stateful tree view

class CookieTreeViewTest(StatefulTreeViewTest):

    def setUp(self):
        super(CookieTreeViewTest, self).setUp()
        ztapi.browserView(None, 'cookie_tree', CookieTreeView)
        zope.component.provideAdapter(LocationPhysicallyLocatable)

    def makeRequestWithVar(self):
        varname = CookieTreeView.request_variable 
        encoder = TreeStateEncoder()
        tree_state = encoder.encodeTreeState(self.expanded_nodes)
        environ = {varname: tree_state}
        request = TestRequest(environ=environ)
        return request

    def test_cookie_tree_pre_expanded(self):
        request = self.makeRequestWithVar()
        view = getMultiAdapter((self.root_obj, request),
                                    name='cookie_tree')
        cookie_tree = view.cookieTree()
        self.assert_(self.root_node.expanded)
        for node in self.root_node.getFlatNodes():
            self.assertEqual(node.expanded, node.getId() in self.expanded_nodes)

    def test_cookie_tree_sets_cookie(self):
        request = self.makeRequestWithVar()
        view = getMultiAdapter((self.root_obj, request),
                               name='cookie_tree')
        cookie_tree = view.cookieTree()
        self.failIf(request.response.getCookie(view.request_variable) is None)

    def test_cookie_tree_site_tree(self):
        request = self.makeRequestWithVar()
        alsoProvides(self.items['a'], IContainmentRoot)
        alsoProvides(self.items['c'], ISite)
        view = getMultiAdapter((self.items['f'], request),
                               name='cookie_tree')
        cookie_tree = view.siteTree()
        self.assert_(cookie_tree.context is self.items['c'])

    def test_cookie_tree_root_tree(self):
        request = self.makeRequestWithVar()
        alsoProvides(self.items['c'], IContainmentRoot)
        view = getMultiAdapter((self.items['f'], request),
                               name='cookie_tree')
        cookie_tree = view.rootTree()
        self.assert_(cookie_tree.context is self.items['c'])
        

def test_suite():
    suite = unittest.makeSuite(StatefulTreeViewTest)
    suite.addTest(unittest.makeSuite(CookieTreeViewTest))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

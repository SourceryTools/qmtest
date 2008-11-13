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
"""Test tree node code.

$Id: test_node.py 26551 2004-07-15 07:06:37Z srichter $
"""
import unittest
from basetest import BaseTestCase
from zope.interface import implements
from zope.app.container.interfaces import IObjectFindFilter
from zope.app.tree.node import Node

class FilterByObject(object):
    """Simple filter that filters out any objects that wasn't passed
    in as a valid object before
    """
    implements(IObjectFindFilter)

    def __init__(self, *objects):
        self.objects = objects

    def match(self, obj):
        return obj in self.objects

class NodeTestCase(BaseTestCase):

    def setUp(self):
        super(NodeTestCase, self).setUp()
        self.makeItems()

    def test_expand_collapse(self):
        # first the node is expanded
        root_node = self.root_node
        self.failUnless(root_node.expanded)
        # now collapse it
        root_node.collapse()
        self.failIf(root_node.expanded)
        # make sure there are no children nodes returned!
        self.assertEqual(root_node.getChildNodes(), [])
        # expand it again
        root_node.expand()
        self.failUnless(root_node.expanded)

    def test_children(self):
        # test hasChildren()
        root_node = self.root_node
        self.failUnless(root_node.hasChildren())
        
        # test getChildNodes()
        children = [node.context for node in root_node.getChildNodes()]
        expected = [self.items['b'], self.items['c']]
        self.assertEqual(children, expected)

        # test with filter
        expand_all = self.items.keys() # expand all nodes
        # emulate node expansion with the FilterByObject filter
        filter = FilterByObject([self.items[id] for id in self.expanded_nodes])
        filtered_root = Node(self.root_obj, expand_all, filter)
        children = [node.context for node in root_node.getChildNodes()]
        expected = [self.items['b'], self.items['c']]
        self.assertEqual(children, expected)

    def test_flat(self):
        # test getFlatNodes()
        root_node = self.root_node
        flat = root_node.getFlatNodes()
        children = [node.context for node in flat]
        # 'a' is not expected because the node on which getFlatNodes()
        # is called is not in the list
        expected = [self.items[i] for i in "bcfg"]
        self.assertEqual(children, expected)

    def test_pre_expanded(self):
        # 'a' is not expected because the node on which getFlatNodes()
        # is called is not in the list
        expected = [self.items[i] for i in "bcfg"]
        # test against to getFlatNodes()
        flat = [node.context for node in self.root_node.getFlatNodes()]
        self.assertEqual(flat, expected)

    def test_flat_dicts(self):
        flat, maxdepth = self.root_node.getFlatDicts()
        self.assertEqual(maxdepth, 2)
        self.assertEqual(len(flat), len(self.root_node.getFlatNodes()))
        bdict = flat[0]
        node = bdict['node']
        self.assertEqual(bdict['row-state'], [])
        self.assertEqual(node.getId(), 'b')
        self.assert_(node.hasChildren())
        self.assert_(node.context is self.items['b'])

    def test_depth(self):
        expanded = ['a', 'c', 'f']
        root_node = Node(self.root_obj, expanded)
        flat, maxdepth = root_node.getFlatDicts()

def test_suite():
    return unittest.makeSuite(NodeTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

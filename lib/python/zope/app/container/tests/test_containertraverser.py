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
"""Container Traverser Tests

$Id: test_containertraverser.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.app.container.traversal import ContainerTraverser
from zope.app.container.interfaces import IReadContainer
from zope.app.testing import ztapi, placelesssetup
from zope.publisher.interfaces import NotFound
from zope.publisher.browser import TestRequest
from zope.interface import implements

class TestContainer(object):
    implements(IReadContainer)

    def __init__(self, **kw):
        for name, value in kw.items():
            setattr(self, name , value)

    def get(self, name, default=None):
        return getattr(self, name, default)


class View(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request


class TraverserTest(placelesssetup.PlacelessSetup, unittest.TestCase):

    # The following two methods exist, so that other container traversers can
    # use these tests as a base.
    def _getTraverser(self, context, request):
        return ContainerTraverser(context, request)

    def _getContainer(self, **kw):
        return TestContainer(**kw)

    def setUp(self):
        super(TraverserTest, self).setUp()
        # Create a small object tree
        self.foo = self._getContainer()
        foo2 = self._getContainer(Foo=self.foo)
        # Initiate a request
        self.request = TestRequest()
        # Create the traverser
        self.traverser = self._getTraverser(foo2, self.request)
        # Define a simple view for the container
        ztapi.browserView(IReadContainer, 'viewfoo', View)
        
    def test_itemTraversal(self):
        self.assertEqual(
            self.traverser.publishTraverse(self.request, 'Foo'),
            self.foo)
        self.assertRaises(
            NotFound,
            self.traverser.publishTraverse, self.request, 'morebar')

    def test_viewTraversal(self):
        self.assertEquals(
            self.traverser.publishTraverse(self.request, 'viewfoo').__class__,
            View)
        self.assertEquals(
            self.traverser.publishTraverse(self.request, 'Foo'),
            self.foo)
        self.assertRaises(
            NotFound,
            self.traverser.publishTraverse, self.request, 'morebar')
        self.assertRaises(
            NotFound,
            self.traverser.publishTraverse, self.request, '@@morebar')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TraverserTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

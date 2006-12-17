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
"""Sample Component Traverser Test

$Id$
"""
import unittest
from zope.publisher.interfaces import NotFound
from zope.interface import Interface, directlyProvides

from zope.app.publication.traversers import SimpleComponentTraverser
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.testing import ztapi

class I(Interface):
    pass


class Container(object):
    def __init__(self, **kw):
        for k in kw:
            setattr(self, k , kw[k])

    def get(self, name, default=None):
        return getattr(self, name, default)


class Request(object):

    def __init__(self, type):
        directlyProvides(self, type)

    def getEffectiveURL(self):
        return ''


class View(object):
    def __init__(self, comp, request):
        self._comp = comp


class Test(PlacelessSetup, unittest.TestCase):
    def testAttr(self):
        # test container traver
        foo = Container()
        c   = Container(foo=foo)
        req = Request(I)

        T = SimpleComponentTraverser(c, req)

        self.assertRaises(NotFound , T.publishTraverse, req ,'foo')


    def testView(self):
        # test getting a view
        foo = Container()
        c   = Container(foo=foo)
        req = Request(I)

        T = SimpleComponentTraverser(c, req)
        ztapi.provideView(None, I, Interface, 'foo', View)

        self.failUnless(T.publishTraverse(req, 'foo').__class__ is View)

        self.assertRaises(NotFound, T.publishTraverse, req , 'morebar')



def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

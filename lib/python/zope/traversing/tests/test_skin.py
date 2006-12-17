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
"""Test skin traversal.

$Id: test_skin.py 68699 2006-06-17 03:29:43Z ctheune $
"""
from unittest import TestCase, main, makeSuite

import zope.component
from zope.testing.cleanup import CleanUp
from zope.interface import Interface, directlyProvides
from zope.publisher.interfaces.browser import IBrowserSkinType

class FauxRequest(object):
    def shiftNameToApplication(self):
        self.shifted = 1

class IFoo(Interface):
    pass
directlyProvides(IFoo, IBrowserSkinType)


class Test(CleanUp, TestCase):

    def setUp(self):
        super(Test, self).setUp()
        zope.component.provideUtility(IFoo, IBrowserSkinType, name='foo')

    def test(self):
        from zope.traversing.namespace import skin

        request = FauxRequest()
        ob = object()
        ob2 = skin(ob, request).traverse('foo', ())
        self.assertEqual(ob, ob2)
        self.assert_(IFoo.providedBy(request))
        self.assertEqual(request.shifted, 1)

    def test_missing_skin(self):
        from zope.traversing.namespace import skin
        from zope.traversing.interfaces import TraversalError
        request = FauxRequest()
        ob = object()
        traverser = skin(ob, request)
        self.assertRaises(TraversalError, traverser.traverse, 'bar', ())

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

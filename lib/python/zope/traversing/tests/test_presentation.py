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
"""Presentation Traverser Tests

$Id: test_presentation.py 66584 2006-04-05 22:10:54Z philikon $
"""
from unittest import TestCase, main, makeSuite
from zope.testing.cleanup import CleanUp
from zope.interface import Interface, implements
from zope.publisher.browser import TestRequest
from zope.traversing.namespace import view, resource
from zope.traversing.testing import browserView, browserResource

class IContent(Interface):
    pass

class Content(object):
    implements(IContent)

class Resource(object):

    def __init__(self, request):
        pass

class View(object):

    def __init__(self, content, request):
        self.content = content


class Test(CleanUp, TestCase):

    def testView(self):
        browserView(IContent, 'foo', View)

        ob = Content()
        v = view(ob, TestRequest()).traverse('foo', ())
        self.assertEqual(v.__class__, View)

    def testResource(self):
        browserResource('foo', Resource)

        ob = Content()
        r = resource(ob, TestRequest()).traverse('foo', ())
        self.assertEqual(r.__class__, Resource)


def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

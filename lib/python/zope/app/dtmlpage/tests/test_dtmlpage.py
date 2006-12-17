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
"""Basic tests for Page Templates used in content-space.

$Id: test_dtmlpage.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

from zope.security.checker import NamesChecker, defineChecker
from zope.traversing.adapters import Traverser, DefaultTraversable
from zope.traversing.interfaces import ITraverser, ITraversable

from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.testing import ztapi
from zope.app.container.contained import contained
from zope.app.dtmlpage.dtmlpage import DTMLPage


class Data(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __getitem__(self, name):
        return getattr(self, name)


class DTMLPageTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(DTMLPageTests, self).setUp()
        ztapi.provideAdapter(None, ITraverser, Traverser)
        ztapi.provideAdapter(None, ITraversable, DefaultTraversable)
        defineChecker(Data, NamesChecker(['URL', 'name', '__getitem__']))

    def test(self):
        page = DTMLPage()
        page.setSource(
            u'<html>'
            u'<head><title><dtml-var title></title></head>'
            u'<body>'
            u'<a href="<dtml-var "REQUEST.URL[\'1\']">">'
            u'<dtml-var name>'
            u'</a></body></html>'
            )

        page = contained(page, Data(name=u'zope'))

        out = page.render(Data(URL={u'1': u'http://foo.com/'}),
                          title=u"Zope rules")
        out = ' '.join(out.split())


        self.assertEqual(
            out,
            u'<html><head><title>Zope rules</title></head><body>'
            u'<a href="http://foo.com/">'
            u'zope'
            u'</a></body></html>'
            )

def test_suite():
    return unittest.makeSuite(DTMLPageTests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())

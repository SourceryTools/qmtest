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
"""Tests creator annotation.

$Id: test_creatorannotator.py 66902 2006-04-12 20:16:30Z philikon $
"""
from unittest import TestCase, TestSuite, main, makeSuite
from zope.app.component.testing import PlacefulSetup
from zope.testing.cleanup import CleanUp

from zope.interface import Interface, implements
import zope.component

from zope.dublincore.creatorannotator import CreatorAnnotator
from zope.dublincore.interfaces import IZopeDublinCore
from zope.security.interfaces import IPrincipal
from zope.security.management import newInteraction, endInteraction

class IDummyContent(Interface):
    pass

class DummyEvent(object):
    pass

class DummyDCAdapter(object):

    __used_for__ = IDummyContent
    implements(IZopeDublinCore)

    def _getcreator(self):
        return self.context.creators

    def _setcreator(self, value):
        self.context.creators = value
    creators = property(_getcreator, _setcreator, None, "Adapted Creators")

    def __init__(self, context):
        self.context = context
        self.creators = context.creators


class DummyDublinCore(object):

    implements(IDummyContent)

    creators = ()


class DummyPrincipal(object):
    implements(IPrincipal)

    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description


class DummyRequest(object):

    def __init__(self, principal):
        self.principal = principal
        self.interaction = None


class Test(PlacefulSetup, TestCase, CleanUp):

    def setUp(self):
        PlacefulSetup.setUp(self)
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerAdapter(DummyDCAdapter, (IDummyContent, ), IZopeDublinCore)

    def tearDown(self):
        PlacefulSetup.tearDown(self)

    def test_creatorannotation(self):
        # Create stub event and DC object
        event = DummyEvent()
        data = DummyDublinCore()
        event.object = data

        good_author = DummyPrincipal('goodauthor', 'the good author',
                                     'this is a very good author')

        bad_author = DummyPrincipal('badauthor', 'the bad author',
                                    'this is a very bad author')

        # Check what happens if no user is there
        CreatorAnnotator(event)
        self.assertEqual(data.creators,())
        endInteraction()

        # Let the bad edit it first
        newInteraction(DummyRequest(bad_author))
        CreatorAnnotator(event)

        self.failIf(len(data.creators) != 1)
        self.failUnless(bad_author.id in data.creators)
        endInteraction()

        # Now let the good edit it
        newInteraction(DummyRequest(good_author))
        CreatorAnnotator(event)

        self.failIf(len(data.creators) != 2)
        self.failUnless(good_author.id in data.creators)
        self.failUnless(bad_author.id in data.creators)
        endInteraction()

        # Let the bad edit it again
        newInteraction(DummyRequest(bad_author))
        CreatorAnnotator(event)

        # Check that the bad author hasn't been added twice.
        self.failIf(len(data.creators) != 2)
        self.failUnless(good_author.id in data.creators)
        self.failUnless(bad_author.id in data.creators)
        endInteraction()

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

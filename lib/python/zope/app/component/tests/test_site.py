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
"""Registration Tests

$Id$
"""
__docformat__ = "reStructuredText"
import unittest

import zope.interface
import zope.interface.verify
from zope.testing import doctest

from zope.app.testing import setup
from zope.app.component import interfaces, site
from zope.app.folder import folder
import zope.app.publication.interfaces

class SiteManagerStub(object):
    zope.interface.implements(interfaces.ILocalSiteManager)

class CustomFolder(folder.Folder):

    def __init__(self, name):
        self.__name__ = name
        super(CustomFolder, self).__init__()

    def __repr__(self):
        return '<%s %s>' %(self.__class__.__name__, self.__name__)


def test_SiteManagerAdapter():
    """
    The site manager adapter is used to find the nearest site for any given
    location. If the provided context is a site,

      >>> site = folder.Folder()
      >>> sm = SiteManagerStub()
      >>> site.setSiteManager(sm)

    then the adapter simply return's the site's site manager:
    
      >>> from zope.app.component.site import SiteManagerAdapter
      >>> SiteManagerAdapter(site) is sm
      True

    If the context is a location (i.e. has a `__parent__` attribute),

      >>> ob = folder.Folder()
      >>> ob.__parent__ = site
      >>> ob2 = folder.Folder()
      >>> ob2.__parent__ = ob

    we 'acquire' the closest site and return its site manager: 

      >>> SiteManagerAdapter(ob) is sm
      True
      >>> SiteManagerAdapter(ob2) is sm
      True

    If we are unable to find a local site manager, then the global site
    manager is returned.
    
      >>> import zope.component
      >>> orphan = CustomFolder('orphan')
      >>> SiteManagerAdapter(orphan) is zope.component.getGlobalSiteManager()
      True
    """


def test_setThreadSite_clearThreadSite():
    """
    This test ensures that the site is corectly set and cleared in a thread
    during traversal using event subscribers. Before we start, no site is set:

      >>> from zope.app.component import hooks
      >>> hooks.getSite() is None
      True


      >>> request = object()

      >>> from zope.app import publication
      >>> from zope.app.component import site

      
    On the other hand, if a site is traversed, 

      >>> sm = SiteManagerStub()
      >>> mysite = CustomFolder('mysite')
      >>> mysite.setSiteManager(sm)

      >>> ev = publication.interfaces.BeforeTraverseEvent(mysite, request)
      >>> site.threadSiteSubscriber(mysite, ev)

      >>> hooks.getSite()
      <CustomFolder mysite>

    Once the request is completed,

      >>> ev = publication.interfaces.EndRequestEvent(mysite, request)
      >>> site.clearThreadSiteSubscriber(ev)

    the site assignment is cleared again:

      >>> hooks.getSite() is None
      True
    """

class BaseTestSiteManagerContainer(unittest.TestCase):
    """This test is for objects that don't have site managers by
    default and that always give back the site manager they were
    given.

    Subclasses need to define a method, 'makeTestObject', that takes no
    arguments and that returns a new site manager
    container that has no site manager."""

    def test_IPossibleSite_verify(self):
        zope.interface.verify.verifyObject(interfaces.IPossibleSite,
                                           self.makeTestObject())

    def test_get_and_set(self):
        smc = self.makeTestObject()
        self.failIf(interfaces.ISite.providedBy(smc))
        sm = site.LocalSiteManager(smc)
        smc.setSiteManager(sm)
        self.failUnless(interfaces.ISite.providedBy(smc))
        self.failUnless(smc.getSiteManager() is sm)
        zope.interface.verify.verifyObject(interfaces.ISite, smc)

    def test_set_w_bogus_value(self):
        smc=self.makeTestObject()
        self.assertRaises(Exception, smc.setSiteManager, self)



class SiteManagerContainerTest(BaseTestSiteManagerContainer):
    def makeTestObject(self):
        from zope.app.component.site import SiteManagerContainer
        return SiteManagerContainer()


def setUp(test):
    setup.placefulSetUp()

def tearDown(test):
    setup.placefulTearDown()

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(),
        unittest.makeSuite(SiteManagerContainerTest),
        doctest.DocFileSuite('../site.txt',
                             setUp=setUp, tearDown=tearDown),
        ))

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
    

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
"""Base Mix-in class for Placeful Setups 

$Id: testing.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.interface
from zope.component.interfaces import IComponentLookup
from zope.app.component.interfaces import ILocalSiteManager
from zope.app import zapi
from zope.app.testing import setup
from zope.app.testing.placelesssetup import PlacelessSetup
from zope.app.folder import rootFolder

class Place(object):

    def __init__(self, path):
        self.path = path

    def __get__(self, inst, cls=None):
        if inst is None:
            return self

        try:
            # Use __dict__ directly to avoid infinite recursion
            root = inst.__dict__['rootFolder']
        except KeyError:
            root = inst.rootFolder = setup.buildSampleFolderTree()

        return zapi.traverse(root, self.path)


class PlacefulSetup(PlacelessSetup):

    # Places :)
    rootFolder  = Place(u'')

    folder1     = Place(u'folder1')
    folder1_1   = Place(u'folder1/folder1_1')
    folder1_1_1 = Place(u'folder1/folder1_1/folder1_1_1')
    folder1_1_2 = Place(u'folder1/folder1_2/folder1_1_2')
    folder1_2   = Place(u'folder1/folder1_2')
    folder1_2_1 = Place(u'folder1/folder1_2/folder1_2_1')

    folder2     = Place(u'folder2')
    folder2_1   = Place(u'folder2/folder2_1')
    folder2_1_1 = Place(u'folder2/folder2_1/folder2_1_1')

    folder3     = Place(u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER A}"
                        u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER KA}"
                        u"\N{CYRILLIC SMALL LETTER A}3")
    folder3_1   = Place(u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER A}"
                        u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER KA}"
                        u"\N{CYRILLIC SMALL LETTER A}3/"
                        u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER A}"
                        u"\N{CYRILLIC SMALL LETTER PE}"
                        u"\N{CYRILLIC SMALL LETTER KA}"
                        u"\N{CYRILLIC SMALL LETTER A}3_1")

    def setUp(self, folders=False, site=False):
        setup.placefulSetUp()
        if folders or site:
            return self.buildFolders(site)

    def tearDown(self):
        setup.placefulTearDown()
        # clean up folders and placeful site managers and services too?

    def buildFolders(self, site=False):
        self.rootFolder = setup.buildSampleFolderTree()
        if site:
            return self.makeSite()

    def makeSite(self, path='/'):
        folder = zapi.traverse(self.rootFolder, path)
        return setup.createSiteManager(folder, True)

    def createRootFolder(self):
        self.rootFolder = rootFolder()


class SiteManagerStub(object):
    zope.interface.implements(ILocalSiteManager)
    
    __bases__ = ()

    def __init__(self):
        self._utils = {}

    def setNext(self, next):
        self.__bases__ = (next, )

    def provideUtility(self, iface, util, name=''):
        self._utils[(iface, name)] = util

    def queryUtility(self, iface, name='', default=None):
        return self._utils.get((iface, name), default)
    

def testingNextUtility(utility, nextutility, interface, name='',
                       sitemanager=None, nextsitemanager=None):
    """Provide a next utility for testing.

    Since utilities must be registered in sites, we really provide a next
    site manager in which we place the next utility. If you do not pass in
    any site managers, they will be created for you.

    For a simple usage of this function, see the doc test of
    `queryNextUtility()`. Here is a demonstration that passes in the services
    directly and ensures that the `__parent__` attributes are set correctly.

    First, we need to create a utility interface and implementation:

      >>> from zope.interface import Interface, implements
      >>> class IAnyUtility(Interface):
      ...     pass
      
      >>> class AnyUtility(object):
      ...     implements(IAnyUtility)
      ...     def __init__(self, id):
      ...         self.id = id
      
      >>> any1 = AnyUtility(1)
      >>> any1next = AnyUtility(2)

    Now we create a special site manager that can have a location:

      >>> SiteManager = type('SiteManager', (GlobalSiteManager,),
      ...                       {'__parent__': None})

    Let's now create one site manager

      >>> sm = SiteManager()

    and pass it in as the original site manager to the function:

      >>> testingNextUtility(any1, any1next, IAnyUtility, sitemanager=sm)
      >>> any1.__parent__ is utils
      True
      >>> smnext = any1next.__parent__
      >>> sm.__parent__.next.data['Utilities'] is smnext
      True

    or if we pass the current and the next site manager:

      >>> sm = SiteManager()
      >>> smnext = SiteManager()
      >>> testingNextUtility(any1, any1next, IAnyUtility,
      ...                    sitemanager=sm, nextsitemanager=smnext)
      >>> any1.__parent__ is sm
      True
      >>> any1next.__parent__ is smnext
      True
    
    """
    if sitemanager is None:
        sitemanager = SiteManagerStub()
    if nextsitemanager is None:
        nextsitemanager = SiteManagerStub()
    sitemanager.setNext(nextsitemanager)

    sitemanager.provideUtility(interface, utility, name)
    utility.__conform__ = (
        lambda iface:
        iface.isOrExtends(IComponentLookup) and sitemanager or None
        )
    nextsitemanager.provideUtility(interface, nextutility, name)
    nextutility.__conform__ = (
        lambda iface:
        iface.isOrExtends(IComponentLookup) and nextsitemanager or None
        )

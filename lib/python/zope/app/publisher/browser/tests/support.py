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
"""Support for tests that need a simple site to be provided.

$Id: support.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.component
from zope.interface import implements
from zope.traversing.interfaces import IContainmentRoot

from zope.app.component.hooks import setSite
from zope.app.component.interfaces import ISite

class Site:
    implements(ISite, IContainmentRoot)

    def getSiteManager(self):
        return zope.component.getGlobalSiteManager()

site = Site()


class SiteHandler(object):

    def setUp(self):
        super(SiteHandler, self).setUp()
        setSite(site)

    def tearDown(self):
        setSite()
        super(SiteHandler, self).tearDown()

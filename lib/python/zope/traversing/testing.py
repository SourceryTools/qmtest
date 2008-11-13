##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Traversing test fixtures

$Id: testing.py 66550 2006-04-05 15:34:54Z philikon $
"""
__docformat__ = "reStructuredText"

import zope.component
import zope.interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.location.traversing import LocationPhysicallyLocatable
from zope.traversing.interfaces import ITraverser, ITraversable
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.traversing.interfaces import IContainmentRoot
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.adapters import Traverser, RootPhysicallyLocatable
from zope.traversing.browser import SiteAbsoluteURL, AbsoluteURL
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.traversing.namespace import etc

def setUp():
    zope.component.provideAdapter(Traverser, (None,), ITraverser)
    zope.component.provideAdapter(DefaultTraversable, (None,), ITraversable)
    zope.component.provideAdapter(LocationPhysicallyLocatable,
                                  (None,), IPhysicallyLocatable)
    zope.component.provideAdapter(RootPhysicallyLocatable,
                                  (IContainmentRoot,), IPhysicallyLocatable)

    # set up the 'etc' namespace
    zope.component.provideAdapter(etc, (None,), ITraversable, name="etc")
    zope.component.provideAdapter(etc, (None, None), ITraversable, name="etc")

    browserView(None, "absolute_url", AbsoluteURL)
    browserView(IContainmentRoot, "absolute_url", SiteAbsoluteURL)

    browserView(None, '', AbsoluteURL, providing=IAbsoluteURL)
    browserView(IContainmentRoot, '', SiteAbsoluteURL,
                providing=IAbsoluteURL)

def browserView(for_, name, factory, providing=zope.interface.Interface):
    zope.component.provideAdapter(factory, (for_, IDefaultBrowserLayer),
                                  providing, name=name)

def browserResource(name, factory, providing=zope.interface.Interface):
    zope.component.provideAdapter(factory, (IDefaultBrowserLayer,),
                                  providing, name=name)

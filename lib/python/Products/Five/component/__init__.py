##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Five local component look-up support

$Id: __init__.py 65813 2006-03-05 00:31:08Z philikon $
"""
import zope.interface
import zope.component
import zope.event
from zope.component.interfaces import IComponentLookup
from zope.app.component.interfaces import ISite, IPossibleSite
from zope.app.publication.zopepublication import BeforeTraverseEvent

import ExtensionClass
from Acquisition import aq_base, aq_inner, aq_parent
from Products.SiteAccess.AccessRule import AccessRule
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse

# Hook up custom component architecture calls
import zope.app.component.hooks
zope.app.component.hooks.setHooks()

def findSite(obj, iface=ISite):
    """Find a site by walking up the object hierarchy, supporting both
    the ``ILocation`` API and Zope 2 Acquisition."""
    while obj is not None and not iface.providedBy(obj):
        obj = getattr(obj, '__parent__', aq_parent(aq_inner(obj)))
    return obj

@zope.component.adapter(zope.interface.Interface)
@zope.interface.implementer(IComponentLookup)
def siteManagerAdapter(ob):
    """Look-up a site manager/component registry for local component
    lookup.  This is registered in place of the one in Zope 3 so that
    we lookup using acquisition in addition to the ``ILocation`` API.
    """
    site = findSite(ob)
    if site is None:
        return zope.component.getGlobalSiteManager()
    return site.getSiteManager()

class LocalSiteHook(ExtensionClass.Base):

    def __call__(self, container, request):
        zope.event.notify(BeforeTraverseEvent(container, request))

HOOK_NAME = '__local_site_hook__'

def enableSite(obj, iface=ISite):
    """Install __before_traverse__ hook for Local Site
    """
    # We want the original object, not stuff in between, and no acquisition
    obj = aq_base(obj)
    if not IPossibleSite.providedBy(obj):
        raise TypeError, 'Must provide IPossibleSite'
    hook = AccessRule(HOOK_NAME)
    registerBeforeTraverse(obj, hook, HOOK_NAME, 1)

    if not hasattr(obj, HOOK_NAME):
        setattr(obj, HOOK_NAME, LocalSiteHook())

    zope.interface.alsoProvides(obj, iface)

def disableSite(obj, iface=ISite):
    """Remove __before_traverse__ hook for Local Site
    """
    # We want the original object, not stuff in between, and no acquisition
    obj = aq_base(obj)
    if not iface.providedBy(obj):
        raise TypeError('Object must be a site.')

    unregisterBeforeTraverse(obj, HOOK_NAME)
    if hasattr(obj, HOOK_NAME):
        delattr(obj, HOOK_NAME)

    zope.interface.noLongerProvides(obj, iface)

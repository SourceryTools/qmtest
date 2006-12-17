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
"""Hooks for getting and setting a site in the thread global namespace.

$Id: hooks.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.component
import zope.deprecation
import zope.thread
import zope.security

class read_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, inst, cls):
        if inst is None:
            return self

        return self.func(inst)

class SiteInfo(zope.thread.local):
    site = None
    sm = zope.component.getGlobalSiteManager()

    def adapter_hook(self):
        adapter_hook = self.sm.adapters.adapter_hook
        self.adapter_hook = adapter_hook
        return adapter_hook

    adapter_hook = read_property(adapter_hook)

siteinfo = SiteInfo()

def setSite(site=None):
    if site is None:
        sm = zope.component.getGlobalSiteManager()
    else:

        # We remove the security proxy because there's no way for
        # untrusted code to get at it without it being proxied again.

        # We should really look look at this again though, especially
        # once site managers do less.  There's probably no good reason why
        # they can't be proxied.  Well, except maybe for performance.

        site = zope.security.proxy.removeSecurityProxy(site)
        sm = site.getSiteManager()

    siteinfo.site = site
    siteinfo.sm = sm
    try:
        del siteinfo.adapter_hook
    except AttributeError:
        pass

def getSite():
    return siteinfo.site


def getSiteManager(context=None):
    """A special hook for getting the site manager.

    Here we take the currently set site into account to find the appropriate
    site manager.
    """
    if context is None:
        return siteinfo.sm

    # We remove the security proxy because there's no way for
    # untrusted code to get at it without it being proxied again.

    # We should really look look at this again though, especially
    # once site managers do less.  There's probably no good reason why
    # they can't be proxied.  Well, except maybe for performance.
    sm = zope.component.interfaces.IComponentLookup(
        context, zope.component.getGlobalSiteManager())
    return zope.security.proxy.removeSecurityProxy(sm)


def adapter_hook(interface, object, name='', default=None):
    try:
        return siteinfo.adapter_hook(interface, object, name, default)
    except zope.component.interfaces.ComponentLookupError:
        return default


def setHooks():
    zope.component.adapter_hook.sethook(adapter_hook)
    zope.component.getSiteManager.sethook(getSiteManager)

def resetHooks():
    # Reset hookable functions to original implementation.
    zope.component.adapter_hook.reset()
    zope.component.getSiteManager.reset()

# Clear the site thread global
clearSite = setSite
from zope.testing.cleanup import addCleanUp
addCleanUp(resetHooks)

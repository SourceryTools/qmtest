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
"""Introspector View class

$Id: browser.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.component.interfaces import ComponentLookupError
from zope.interface import directlyProvides, directlyProvidedBy
from zope.proxy import removeAllProxies
from zope.publisher.browser import BrowserView
from zope.component.interface import getInterface

from zope.app import zapi
from zope.app.introspector.interfaces import IIntrospector

class IntrospectorView(BrowserView):

    def getIntrospector(self):
        introspector = IIntrospector(self.context)
        introspector.setRequest(self.request)
        return introspector

    def getInterfaceURL(self, name):
        sm = zapi.getSiteManager(self.context)
        try:
            getInterface(self.context, name)
            url = zapi.absoluteURL(sm, self.request)
        except ComponentLookupError:
            return ""
        return "%s/interfacedetail.html?id=%s" % (url, name)

    def update(self):
        if 'ADD' in self.request:
            for interface in self.getIntrospector().getMarkerInterfaceNames():
                if "add_%s" % interface in self.request:
                    ob = self.context
                    interface = getInterface(ob, interface)
                    directlyProvides(removeAllProxies(ob), directlyProvidedBy(ob), interface)

        if 'REMOVE' in self.request:
            for interface in self.getIntrospector().getDirectlyProvidedNames():
                if "rem_%s" % interface in self.request:
                    ob = self.context
                    interface = getInterface(ob, interface)
                    directlyProvides(removeAllProxies(ob), directlyProvidedBy(ob)-interface)


# BBB: Deprecated module; Will be gone in 3.3.
from zope.deprecation import deprecated
deprecated('IntrospectorView',
           'Use the public apidoc utilities. Will be gone in 3.3.')

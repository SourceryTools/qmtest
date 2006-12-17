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
"""Module Views

$Id: browser.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.component import getMultiAdapter
from zope.interface.interface import InterfaceClass
from zope.proxy import removeAllProxies
from zope.publisher.browser import BrowserView
from zope.security.proxy import isinstance, removeSecurityProxy
from zope.traversing.api import getName, getParent
from zope.traversing.browser import absoluteURL

from zope.app.i18n import ZopeMessageFactory as _

from zope.app.apidoc.apidoc import APIDocumentation
from zope.app.apidoc.utilities import getPythonPath, renderText, columnize
from zope.app.apidoc.codemodule.module import Module
from zope.app.apidoc.codemodule.class_ import Class
from zope.app.apidoc.codemodule.function import Function
from zope.app.apidoc.codemodule.text import TextFile
from zope.app.apidoc.codemodule.zcml import ZCMLFile

def findAPIDocumentationRoot(obj, request):
    if isinstance(obj, APIDocumentation):
        return absoluteURL(obj, request)
    return findAPIDocumentationRoot(getParent(obj), request)


class ModuleDetails(BrowserView):
    """Represents the details of the module."""

    def __init__(self, context, request):
        super(ModuleDetails, self).__init__(context, request)
        try:
            self.apidocRoot = findAPIDocumentationRoot(context, request)
        except TypeError:
            # Probably context without location; it's a test
            self.apidocRoot = ''

    def getDoc(self):
        """Get the doc string of the module STX formatted."""
        text = self.context.getDocString()
        if text is None:
            return None
        lines = text.strip().split('\n')
        # Get rid of possible CVS id.
        lines = [line for line in lines if not line.startswith('$Id')]
        return renderText('\n'.join(lines), self.context.getPath())

    def getEntries(self, columns=True):
        """Return info objects for all modules and classes in this module."""
        entries = [{'name': name,
                    # only for interfaces; should be done differently somewhen
                    'path': getPythonPath(removeAllProxies(obj)),
                    'url': absoluteURL(obj, self.request),
                    'ismodule': isinstance(obj, Module),
                    'isinterface': isinstance(
                         removeAllProxies(obj), InterfaceClass),
                    'isclass': isinstance(obj, Class),
                    'isfunction': isinstance(obj, Function),
                    'istextfile': isinstance(obj, TextFile),
                    'iszcmlfile': isinstance(obj, ZCMLFile)}
                   for name, obj in self.context.items()]
        entries.sort(lambda x, y: cmp(x['name'], y['name']))
        if columns:
            entries = columnize(entries)
        return entries

    def getBreadCrumbs(self):
        """Create breadcrumbs for the module path.

        We cannot reuse the the system's bread crumbs, since they go all the
        way up to the root, but we just want to go to the root module."""
        names = self.context.getPath().split('.')
        crumbs = []
        module = self.context
        # I really need the class here, so remove the proxy.
        while removeSecurityProxy(module).__class__ is Module:
            crumbs.append(
                {'name': getName(module),
                 'url': absoluteURL(module, self.request)}
                )
            module = getParent(module)

        crumbs.append(
            {'name': _('[top]'),
             'url': getMultiAdapter(
                      (module, self.request), name='absolute_url')()} )

        crumbs.reverse()
        return crumbs

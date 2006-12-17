##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Support classes for XML-based tree

$Id: xmlobject.py 67630 2006-04-27 00:54:03Z jim $
"""
from rfc822 import formatdate, time
from xml.sax.saxutils import quoteattr

from zope.interface import Interface
from zope.proxy import sameProxiedObjects
from zope.security.interfaces import Unauthorized, Forbidden
from zope.i18n import translate
from zope.traversing.api import getParents, getParent, traverse
from zope.publisher.browser import BrowserView

from zope.app import zapi
from zope.app.container.interfaces import IReadContainer
from zope.app.i18n import ZopeMessageFactory as _

titleTemplate = _('Contains $${num} item(s)')
loadingMsg = _('Loading...')

def setNoCacheHeaders(response):
    """Ensure that the tree isn't cached"""
    response.setHeader('Pragma', 'no-cache')
    response.setHeader('Cache-Control', 'no-cache')
    response.setHeader('Expires',
                       formatdate(time.time() - 7 * 86400)) # 7 days ago

def xmlEscape(format, *args):
    quotedArgs = [quoteattr(unicode(arg)) for arg in args]
    return format % tuple(quotedArgs)

def xmlEscapeWithCData(format, *args):
    cData = args[-1]
    quotedArgs = [quoteattr(unicode(arg)) for arg in args[:-1]]
    quotedArgsWithCData = quotedArgs + [cData]
    return format % tuple(quotedArgsWithCData)

def getParentsFromContextToObject(context, obj):
    """Returns a list starting with the given context's parent followed by
    each of its parents till we reach the object.

    """
    if sameProxiedObjects(context, obj):
        return []

    parents = []
    w = context

    while 1:
        w = w.__parent__
        if sameProxiedObjects(w, obj):
            parents.append(w)
            break
        if w is None:
            break

        parents.append(w)

    return parents


class ReadContainerXmlObjectView(BrowserView):
    """Provide a xml interface for dynamic navigation tree in UI"""

    __used_for__ = IReadContainer


    def getIconUrl(self, item):
        result = ''
        icon = zapi.queryMultiAdapter((item, self.request), name='zmi_icon')
        if icon:
            result = icon.url()
        return result

    def getLengthOf(self, item):
        res = -1
        if IReadContainer.providedBy(item):
            try:
                res = len(item)
            except (Unauthorized, Forbidden):
                pass
        return res

    def children_utility(self, container):
        """Return an XML document that contains the children of an object."""
        result = []

        keys = list(container.keys())

        # include the site manager
        keys.append(u'++etc++site')

        for name in keys:

            # Only include items we can traverse to
            item = traverse(container, name, None)
            if item is None:
                continue

            iconUrl = self.getIconUrl(item)
            item_len = self.getLengthOf(item)
            if item_len >= 0:
                result.append(xmlEscape(
                    u'<collection name=%s length=%s icon_url=%s/>',
                    name, item_len, iconUrl))
            else:
                result.append(xmlEscape(
                    u'<item name=%s icon_url=%s/>',
                    name, iconUrl))

        return u' '.join(result)


    def children(self):
        """ """
        container = self.context
        self.request.response.setHeader('Content-Type', 'text/xml')
        setNoCacheHeaders(self.request.response)
        res = (u'<?xml version="1.0" ?><children> %s </children>'
                % self.children_utility(container))
        return res

    def singleBranchTree(self, root=''):
        """Return an XML document with the siblings and parents of an object.

        There is only one branch expanded, in other words, the tree is
        filled with the object, its siblings and its parents with
        their respective siblings.

        """
        result = ''
        oldItem = self.context

        vh = self.request.getVirtualHostRoot()
        if vh:
            vhrootView = zapi.getMultiAdapter(
                    (vh, self.request), name='absolute_url')
            baseURL = vhrootView() + '/'
            try:
                rootName = '[' + vh.__name__ + ']'
            except:
                # we got the containment root itself as the virtual host
                # and there is no name.
                rootName = _('[top]')
            parents = getParentsFromContextToObject(self.context, vh)
        else:
            rootName = _('[top]')
            baseURL = self.request.getApplicationURL() + '/'
            parents = getParents(self.context)

        rootName = translate(rootName, context=self.request, default=rootName)

        for item in parents:
            # skip skin if present
            #if item == oldItem:
            #        continue
            subItems = []
            if IReadContainer.providedBy(item):
                keys = list(item.keys())
            else:
                keys = []

            # include the site manager
            keys.append(u'++etc++site')

            for name in keys:
                # Only include items we can traverse to
                subItem = traverse(item, name, None)
                iconUrl = self.getIconUrl(subItem)
                subitem_len = self.getLengthOf(subItem)
                if subitem_len >= 0:
                    # the test below seems to be broken
                    # with the ++etc++site case
                    if subItem == oldItem:
                        subItems.append(xmlEscapeWithCData(
                            u'<collection name=%s length=%s '
                            u'icon_url=%s>%s</collection>', 
                            name, subitem_len, iconUrl, result))
                    else:
                        subItems.append(xmlEscape(
                            u'<collection name=%s length=%s '
                            u'icon_url=%s/>',
                            name, subitem_len, iconUrl))
                else:
                    subItems.append(xmlEscape(
                        u'<item name=%s icon_url=%s />', name, iconUrl))

            result = u' '.join(subItems)
            oldItem = item

        # do not forget root folder
        iconUrl = self.getIconUrl(oldItem)
        result = xmlEscapeWithCData(
                  u'<collection name=%s baseURL=%s length=%s '
                  u'icon_url=%s isroot="">%s</collection>',
                  rootName, baseURL, len(oldItem), iconUrl, result)

        self.request.response.setHeader('Content-Type', 'text/xml')
        setNoCacheHeaders(self.request.response)
        title = translate(titleTemplate,
                          context=self.request, default=titleTemplate)
        loading = translate(loadingMsg,
                          context=self.request, default=loadingMsg)
        return xmlEscapeWithCData(
                u'<?xml version="1.0" ?>'
                u'<children title_tpl=%s loading_msg=%s>%s</children>',
                title, loading, result)

class XmlObjectView(BrowserView):
    """Provide a xml interface for dynamic navigation tree in UI"""

    __used_for__ = Interface

    def singleBranchTree(self, root=''):
        parent = getParent(self.context)
        while parent is not None:
                if IReadContainer.providedBy(parent):
                    view = zapi.queryMultiAdapter(
                        (parent, self.request), name='singleBranchTree.xml')
                    return view()
                else:
                    parent = getParent(parent)

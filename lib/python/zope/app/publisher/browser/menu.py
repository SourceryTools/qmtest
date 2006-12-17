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
"""Menu Registration code.

$Id: menu.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = "reStructuredText"
import sys

import zope.component
from zope.interface import Interface, implements, providedBy
from zope.security import checkPermission, canAccess
from zope.security.interfaces import Unauthorized, Forbidden
from zope.security.proxy import removeSecurityProxy
from zope.publisher.browser import BrowserView

from zope.app.pagetemplate.engine import Engine
from zope.app.publication.browser import PublicationTraverser
from zope.app.publisher.interfaces.browser import IMenuAccessView
from zope.app.publisher.interfaces.browser import IBrowserMenu
from zope.app.publisher.interfaces.browser import IBrowserMenuItem
from zope.app.publisher.interfaces.browser import IBrowserSubMenuItem
from zope.app.publisher.interfaces.browser import IMenuItemType

class BrowserMenu(object):
    """Browser Menu"""
    implements(IBrowserMenu)

    def __init__(self, id, title=u'', description=u''):
        self.id = id
        self.title = title
        self.description = description

    def getMenuItemType(self):
        return zope.component.getUtility(IMenuItemType, self.id)

    def getMenuItems(self, object, request):
        """Return menu item entries in a TAL-friendly form."""
        result = []
        for name, item in zope.component.getAdapters((object, request),
                                                     self.getMenuItemType()):
            if item.available():
                result.append(item)

        # Now order the result. This is not as easy as it seems.
        #
        # (1) Look at the interfaces and put the more specific menu entries
        #     to the front.
        # (2) Sort unabigious entries by order and then by title.
        ifaces = list(providedBy(removeSecurityProxy(object)).__iro__)
        result = [(ifaces.index(item._for or Interface),
            item.order, item.title, item) for item in result]
        result.sort()

        result = [
            {'title': item.title,
             'description': item.description,
             'action': item.action,
             'selected': (item.selected() and u'selected') or u'',
             'icon': item.icon,
             'extra': item.extra,
             'submenu': (IBrowserSubMenuItem.providedBy(item) and
                         getMenu(item.submenuId, object, request)) or None}
            for index, order, title, item in result]

        return result


class BrowserMenuItem(BrowserView):
    """Browser Menu Item Class"""
    implements(IBrowserMenuItem)

    # See zope.app.publisher.interfaces.browser.IBrowserMenuItem
    title = u''
    description = u''
    action = u''
    extra = None
    order = 0
    permission = None
    filter = None
    icon = None
    _for = Interface

    def available(self):
        """See zope.app.publisher.interfaces.browser.IBrowserMenuItem"""
        # Make sure we have the permission needed to access the menu's action
        if self.permission is not None:
            # If we have an explicit permission, check that we
            # can access it.
            if not checkPermission(self.permission, self.context):
                return False

        elif self.action != u'':
            # Otherwise, test access by attempting access
            path = self.action
            l = self.action.find('?')
            if l >= 0:
                path = self.action[:l]

            traverser = PublicationTraverser()
            try:
                view = traverser.traverseRelativeURL(
                    self.request, self.context, path)
            except (Unauthorized, Forbidden, LookupError):
                return False
            else:
                # we're assuming that view pages are callable
                # this is a pretty sound assumption
                if not canAccess(view, '__call__'):
                    return False

        # Make sure that we really want to see this menu item
        if self.filter is not None:

            try:
                include = self.filter(Engine.getContext(
                    context = self.context,
                    nothing = None,
                    request = self.request,
                    modules = sys.modules,
                    ))
            except Unauthorized:
                return False
            else:
                if not include:
                    return False

        return True

    def selected(self):
        """See zope.app.publisher.interfaces.browser.IBrowserMenuItem"""
        request_url = self.request.getURL()

        normalized_action = self.action
        if self.action.startswith('@@'):
            normalized_action = self.action[2:]

        if request_url.endswith('/'+normalized_action):
            return True
        if request_url.endswith('/++view++'+normalized_action):
            return True
        if request_url.endswith('/@@'+normalized_action):
            return True

        return False


class BrowserSubMenuItem(BrowserMenuItem):
    """Browser Menu Item Base Class"""
    implements(IBrowserSubMenuItem)

    # See zope.app.publisher.interfaces.browser.IBrowserSubMenuItem
    submenuId = None

    def selected(self):
        """See zope.app.publisher.interfaces.browser.IBrowserMenuItem"""
        if self.action is u'':
            return False
        return super(BrowserSubMenuItem, self).selected()


def getMenu(id, object, request):
    """Return menu item entries in a TAL-friendly form."""
    menu = zope.component.getUtility(IBrowserMenu, id)
    return menu.getMenuItems(object, request)


def getFirstMenuItem(id, object, request):
    """Get the first item of a menu."""
    items = getMenu(id, object, request)
    if items:
        return items[0]
    return None


class MenuAccessView(BrowserView):
    """A view allowing easy access to menus."""
    implements(IMenuAccessView)

    def __getitem__(self, menuId):
        return getMenu(menuId, self.context, self.request)

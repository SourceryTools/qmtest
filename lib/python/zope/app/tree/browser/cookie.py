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
"""Stateful cookie tree

$Id: cookie.py 68951 2006-07-02 13:02:27Z philikon $
"""
import zope.traversing.api
from zope.traversing.interfaces import IContainmentRoot
from zope.component.interfaces import IComponentLookup

from zope.app.container.interfaces import IContainer
from zope.app.folder.interfaces import IFolder
from zope.app.component.interfaces import ISite

from zope.app.tree.filters import OnlyInterfacesFilter
from zope.app.tree.browser import StatefulTreeView

class CookieTreeView(StatefulTreeView):
    """A stateful tree view using cookies to remember the tree state"""

    request_variable = 'tree-state'
    
    def cookieTree(self, root=None, filter=None):
        """Build a tree with tree state information from a request.
        """
        request = self.request
        tree_state = request.get(self.request_variable, "")
        tree_state = str(tree_state)
        tree_state = tree_state or None
        if tree_state is not None:
            # set a cookie right away
            request.response.setCookie(self.request_variable,
                                       tree_state)
        return self.statefulTree(root, filter, tree_state)

    def folderTree(self, root=None):
        """Cookie tree with only folders (and site managers).
        """
        filter = OnlyInterfacesFilter(IContainer)
        return self.cookieTree(root, filter)

    def siteTree(self):
        """Cookie tree with only folders and the nearest site as root
        node.
        """
        parent = self.context
        for parent in zope.traversing.api.getParents(self.context):
            if ISite.providedBy(parent):
                break
        return self.folderTree(parent)

    def rootTree(self):
        """Cookie tree with only folders and the root container as
        root node.
        """
        root = zope.traversing.api.getRoot(self.context)
        return self.folderTree(root)

    def virtualHostTree(self):
        """Cookie tree with only folders and the root container as
        root node.
        """
        vh = self.request.getVirtualHostRoot()
        if vh:
            return self.folderTree(vh)
        else:
            root = zope.traversing.api.getRoot(self.context)
            return self.folderTree(root)

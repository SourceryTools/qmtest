##############################################################################
#
# Copyright (c) 2002, 2003 Zope Corporation and Contributors.
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
"""`OnlineHelp` tree view

$Id: tree.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.i18n import translate
from zope.publisher.browser import BrowserView

from zope.app import zapi
from zope.app.onlinehelp.interfaces import IOnlineHelp

class OnlineHelpTopicTreeView(BrowserView):
    """Online help topic tree view."""

    def __init__(self, context, request):
        super(OnlineHelpTopicTreeView, self).__init__(context, request)
        self.onlinehelp = zapi.getUtility(IOnlineHelp, "OnlineHelp")

    def getTopicTree(self):
        """Return the tree of help topics.

        We build a flat list of tpoics info dict.
        Iterate this dict oan build from the level info
        a navigation tree in the page tmeplate.
        Each time you get a level 0 means this is a subitem of the
        Onlinehelp itself::

          >>> info = [('id',{infoDict}),(),()]

          <ul class="tree" id="tree">
            <li><a href="#">items</a>
              <ul>
                <li><a href="#">item</a></li>
              </ul>
            </li>
            <li><a href="#">items</a>
              <ul>
                <li><a href="#">items</a>
                  <ul>
                    <li><a href="#">item</a></li>
                    <li><a href="#">item</a></li>
                    <li><a href="#">item</a></li>
                  </ul>
                </li>
                <li><a href="#">items</a>
                  <ul>
                    <li><a href="#">item</a></li>
                    <li id="activeTreeNode"><a href="#">active item</a></li>
                    <li><a href="#">item</a></li>
                  </ul>
                </li>
              </ul>
            </li>
          <ul>
        """
        return self.renderTree(self.onlinehelp)

    def renderTree(self, root):
        """Reder a unordered list 'ul' tree with a class name 'tree'."""
        res = []
        intend = "  "
        res.append('<ul class="tree" id="tree">')
        for topic in root.getSubTopics():
            item = self.renderLink(topic)

            # expand if context is in tree
            if self.isExpanded(topic):
                res.append('  <li class="expand">%s' % item)
            else:
                res.append('  <li>%s' % item)

            if len(topic.getSubTopics()) > 0:
                res.append(self.renderItemList(topic, intend))
            res.append('  </li>')

        res.append('<ul>')

        return '\n'.join(res)

    def renderItemList(self, topic, intend):
        """Render a 'ul' elements as childs of the 'ul' tree."""
        res = []
        intend = intend + "  "
        res.append('%s<ul>' % intend)

        for item in topic.getSubTopics():

            # expand if context is in tree
            if self.isExpanded(topic):
                res.append('  %s<li class="expand">' % intend)
            else:
                res.append('  %s<li>' % intend)

            res.append(self.renderLink(item))
            if len(item.getSubTopics()) > 0:
                res.append('    %s%s' % (
                    self.renderItemList(item, intend), intend))
            res.append('  %s</li>' % intend)
        res.append('%s</ul>' % intend)

        return '\n'.join(res)

    def renderLink(self, topic):
        """Render a href element."""
        title = translate(topic.title, context=self.request,
                default=topic.title)
        if topic.parentPath:
            url = zapi.joinPath(topic.parentPath, topic.id)
        else:
            url = topic.id
        return '<a href="/++help++/%s">%s</a>\n' % (url, title)

    def isExpanded(self, topic):
        if topic.parentPath:
            path = zapi.joinPath(topic.parentPath, topic.id)
        else:
            path = topic.id
        try:
            if zapi.getPath(self.context).startswith('/' + path):
                return True
        except:
            # TODO: fix it, functional test doesn't like zapi.getPath? ri
            pass
        return False

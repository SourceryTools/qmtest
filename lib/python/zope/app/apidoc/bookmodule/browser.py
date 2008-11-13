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
"""Browser Views for Book

$Id: browser.py 70826 2006-10-20 03:41:16Z baijum $
"""
__docformat__ = 'restructuredtext'
from metaconfigure import EMPTYPATH

class Menu(object):
    """Menu View Helper Class

    >>> class Chapter(object):
    ...     title = 'Read Me'
    ...     path = 'README.txt'
    ...
    ...     def getTopicPath(self):
    ...         return self.path[:-4]
    
    >>> class Node(object):
    ...     def __init__(self, context):
    ...         self.context = context

    >>> menu = Menu()

    >>> chapter = Chapter()
    >>> node = Node(chapter)
    >>> menu.getMenuTitle(node)
    'Read Me'

    >>> menu.getMenuLink(node)
    'README/show.html'
    >>> chapter.path = EMPTYPATH
    >>> menu.getMenuLink(node)
    """

    def getMenuTitle(self, node):
        """Return the title of the node that is displayed in the menu."""
        return node.context.title

    def getMenuLink(self, node):
        """Return the HTML link of the node that is displayed in the menu."""
        if node.context.path == EMPTYPATH:
            return None
        return node.context.getTopicPath() + '/show.html'

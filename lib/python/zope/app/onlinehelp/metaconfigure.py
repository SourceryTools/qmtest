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
"""Meta-Configuration Handlers for "help" namespace.

These handlers process the `registerTopic()` directive of
the "help" ZCML namespace.

$Id: metaconfigure.py 41025 2005-12-24 16:47:19Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.app.onlinehelp import globalhelp


class OnlineHelpTopicDirective(object):

    def __init__(self, _context, id, title, parent="", doc_path=None, 
        for_=None, view=None, class_=None, resources=None):
        self._context = _context
        self.id = id
        self.title = title
        self.parent = parent
        self.doc_path = doc_path
        self.for_ = for_
        self.view = view
        self.class_ = class_
        self.resources = resources
        
    def _args(self):
        return (self.parent, self.id, self.title, self.doc_path, self.for_,
                self.view, self.class_, self.resources)

    def _discriminator(self):
        return ('registerHelpTopic', self.parent, self.id)

    def __call__(self):
        self._context.action(
            discriminator=self._discriminator(),
            callable=globalhelp.registerHelpTopic,
            args=self._args(),
            order=666666,
        )

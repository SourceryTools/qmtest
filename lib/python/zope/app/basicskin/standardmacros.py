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
"""Standard macros for page templates in the ZMI

The macros are drawn from various different page templates.

$Id: standardmacros.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'
import zope.interface

from zope.component import getMultiAdapter
from zope.publisher.browser import BrowserView

class Macros(object):
    zope.interface.implements(zope.interface.common.mapping.IItemMapping)

    macro_pages = ()    
    aliases = {
        'view': 'page',
        'dialog': 'page',
        'addingdialog': 'page'
        }

    def __getitem__(self, key):
        key = self.aliases.get(key, key)
        context = self.context
        request = self.request
        for name in self.macro_pages:
            page = getMultiAdapter((context, request), name=name)
            try:
                v = page[key]
            except KeyError:
                pass
            else:
                return v
        raise KeyError(key)

class StandardMacros(BrowserView, Macros):
    macro_pages = ('view_macros', 'dialog_macros')

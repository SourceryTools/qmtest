
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
"""Adapters that give the size of an object.

$Id: size.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.app.i18n import ZopeMessageFactory as _
from zope.size.interfaces import ISized
from zope.interface import implements

class ContainerSized(object):

    implements(ISized)

    def __init__(self, container):
        self._container = container

    def sizeForSorting(self):
        """See `ISized`"""
        return ('item', len(self._container))

    def sizeForDisplay(self):
        """See `ISized`"""
        num_items = len(self._container)
        if num_items == 1:
            return _('1 item')
        return _('${items} items', mapping={'items': str(num_items)})

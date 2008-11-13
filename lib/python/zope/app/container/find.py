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
"""Find Support

$Id: find.py 68442 2006-06-01 12:54:41Z mj $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from interfaces import IFind, IIdFindFilter, IObjectFindFilter
from interfaces import IReadContainer

class FindAdapter(object):

    implements(IFind)

    __used_for__ = IReadContainer

    def __init__(self, context):
        self._context = context

    def find(self, id_filters=None, object_filters=None):
        'See IFind'
        id_filters = id_filters or []
        object_filters = object_filters or []
        result = []
        container = self._context
        for id, object in container.items():
            _find_helper(id, object, container,
                         id_filters, object_filters,
                         result)
        return result


def _find_helper(id, object, container, id_filters, object_filters, result):
    for id_filter in id_filters:
        if not id_filter.matches(id):
            break
    else:
        # if we didn't break out of the loop, all name filters matched
        # now check all object filters
        for object_filter in object_filters:
            if not object_filter.matches(object):
                break
        else:
            # if we didn't break out of the loop, all filters matched
            result.append(object)

    if not IReadContainer.providedBy(object):
        return

    container = object
    for id, object in container.items():
        _find_helper(id, object, container, id_filters, object_filters, result)

class SimpleIdFindFilter(object):

    implements(IIdFindFilter)

    def __init__(self, ids):
        self._ids = ids

    def matches(self, id):
        'See INameFindFilter'
        return id in self._ids
    
class SimpleInterfacesFindFilter(object):
    """Filter objects on the provided interfaces"""
    implements(IObjectFindFilter)
    
    def __init__(self, *interfaces):
        self.interfaces = interfaces
    
    def matches(self, object):
        for iface in self.interfaces:
            if iface.providedBy(object):
                return True
        return False

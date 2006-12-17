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
"""Filters

Child objects can be filtered out by certain criteria which are
defined by a filter. Writing your own filter should be very easy. All
you have to implement is the IObjectFindFilter interface from the
zope.app.interfaces.find package. Already existing filters for the
find machinery may be used with statictree just as well.

Since commonly needed, this module provides two filters that filter by
interface.

$Id: filters.py 26551 2004-07-15 07:06:37Z srichter $
"""
from zope.interface import implements
from zope.app.container.interfaces import IObjectFindFilter

class OnlyInterfacesFilter(object):
    """Only match objects that implement one of the given interfaces.
    """
    implements(IObjectFindFilter)
    only_interfaces = True

    def __init__(self, *filterby):
        self.ifaces = filterby

    def matches(self, obj):
        ifaces = self.ifaces
        for iface in ifaces:
            if iface.providedBy(obj):
                return self.only_interfaces
        return not self.only_interfaces

class AllButInterfacesFilter(OnlyInterfacesFilter):
    """Match only objects that do not implement one of the given
    interfaces.
    """
    only_interfaces = False

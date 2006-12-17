##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Default Preferences Provider

$Id$
"""
__docformat__ = "reStructuredText"
import persistent
from BTrees.OOBTree import OOBTree

import zope.interface
import zope.component
from zope.security.checker import defineChecker
from zope.traversing.interfaces import IContainmentRoot
from zope.location import locate

import zope.app.component
from zope.app.container.contained import Contained
from zope.app.preference import preference, interfaces

class DefaultPreferenceProvider(persistent.Persistent, Contained):
    zope.interface.implements(interfaces.IDefaultPreferenceProvider)

    def __init__(self):
        self.data = OOBTree()

    def getDefaultPreferenceGroup(self, id=''):
        group = zope.component.getUtility(interfaces.IPreferenceGroup, name=id)
        group = group.__bind__(self)
        default = DefaultPreferenceGroup(group, self)
        zope.interface.alsoProvides(default, IContainmentRoot)
        locate(default, self, 'preferences')
        return default

    preferences = property(getDefaultPreferenceGroup)


def DefaultPreferences(context, request):
    return context.preferences


class DefaultPreferenceGroup(preference.PreferenceGroup):
    """A preference group representing the site-wide default values."""

    def __init__(self, group, provider):
        self.provider = provider
        super(DefaultPreferenceGroup, self).__init__(
            group.__id__, group.__schema__,
            group.__title__, group.__description__)

        # Make sure that we also mark the default group as category if the
        # actual group is one; this is important for the UI.
        if interfaces.IPreferenceCategory.providedBy(group):
            zope.interface.alsoProvides(self, interfaces.IPreferenceCategory)

    def get(self, key, default=None):
        group = super(DefaultPreferenceGroup, self).get(key, default)
        if group is default:
            return default
        return DefaultPreferenceGroup(group, self.provider).__bind__(self)
    
    def items(self):
        return [
            (id, DefaultPreferenceGroup(group, self.provider).__bind__(self))
            for id, group in super(DefaultPreferenceGroup, self).items()]

    def __getattr__(self, key):
        # Try to find a sub-group of the given id
        group = self.get(key)
        if group is not None:
            return group

        # Try to find a preference of the given name
        if self.__schema__ and key in self.__schema__:
            marker = object()
            value = self.data.get(key, marker)
            if value is not marker:
                return value

            # There is currently no local entry, so let's go to the next
            # provider and lookup the group and value there.
            nextProvider = zope.app.component.queryNextUtility(
                self.provider, interfaces.IDefaultPreferenceProvider)

            # No more providers found, so return the schema's default
            if nextProvider is None: 
                return self.__schema__[key].default

            nextGroup = nextProvider.getDefaultPreferenceGroup(self.__id__)
            return getattr(nextGroup, key, self.__schema__[key].default)

        # Nothing found, raise an attribute error
        raise AttributeError("'%s' is not a preference or sub-group." % key)

    def data(self):
        if self.__id__ not in self.provider.data:
            self.provider.data[self.__id__] = OOBTree()

        return self.provider.data[self.__id__]
    data = property(data)


defineChecker(DefaultPreferenceGroup, preference.PreferenceGroupChecker)

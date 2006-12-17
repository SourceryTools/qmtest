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
"""Filesystem representation support.

$Id$
"""
__docformat__ = 'restructuredtext'

from zope.app.component.interfaces import ISite


class RootDirectoryFactory(object):

    def __init__(self, context):
        pass

    def __call__(self, name):
        return Folder()


class ReadDirectory(object):
    """Adapter to provide a file-system rendition of folders
    """

    def __init__(self, context):
        self.context = context

    def keys(self):
        keys = self.context.keys()
        if ISite.providedBy(self.context):
            return list(keys) + ['++etc++site']
        return keys

    def get(self, key, default=None):
        if key == '++etc++site' and ISite.providedBy(self.context):
            return self.context.getSiteManager()

        return self.context.get(key, default)

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, key):
        v = self.get(key, self)
        if v is self:
            raise KeyError(key)
        return v

    def values(self):
        return map(self.get, self.keys())

    def __len__(self):
        l = len(self.context)
        if ISite.providedBy(self.context):
            l += 1
        return l

    def items(self):
        get = self.get
        return [(key, get(key)) for key in self.keys()]

    def __contains__(self, key):
        return self.get(key) is not None

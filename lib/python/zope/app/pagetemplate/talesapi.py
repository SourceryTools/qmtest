##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Implementation of the Zope TALES API

$Id: talesapi.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.size.interfaces import ISized
from zope.security.interfaces import Unauthorized
from zope.tales.interfaces import ITALESFunctionNamespace
from zope.dublincore.interfaces import IDCDescriptiveProperties
from zope.dublincore.interfaces import IDCTimes
from zope.dublincore.interfaces import IZopeDublinCore
from zope.traversing.api import getName

class ZopeTalesAPI(object):

    implements(IDCTimes, IDCDescriptiveProperties, ITALESFunctionNamespace)

    def __init__(self, context):
        self.context = context

    def setEngine(self, engine):
        self._engine = engine

    def title(self):
        a = IZopeDublinCore(self.context, None)
        if a is None:
            raise AttributeError('title')
        return a.title
    title = property(title)

    def description(self):
        a = IZopeDublinCore(self.context, None)
        if a is None:
            raise AttributeError('description')
        return a.description
    description = property(description)

    def created(self):
        a = IZopeDublinCore(self.context, None)
        if a is None:
            raise AttributeError('created')
        return a.created
    created = property(created)

    def modified(self):
        a = IZopeDublinCore(self.context, None)
        if a is None:
            raise AttributeError('modified')
        return a.modified
    modified = property(modified)

    def name(self):
        return getName(self.context)

    def title_or_name(self):
        try:
            return getattr(self, 'title', '') or getName(self.context)
        except Unauthorized:
            return getName(self.context)

    def size(self):
        a = ISized(self.context, None)
        if a is None:
            raise AttributeError('size')
        return a.sizeForDisplay()

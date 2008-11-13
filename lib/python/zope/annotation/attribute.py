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
"""Attribute Annotations implementation

$Id: attribute.py 72995 2007-03-05 21:36:39Z jacobholm $
"""
__docformat__ = 'restructuredtext'

from UserDict import DictMixin
from BTrees.OOBTree import OOBTree

from zope import component, interface
from zope.annotation import interfaces

class AttributeAnnotations(DictMixin):
    """Store annotations on an object

    Store annotations in the `__annotations__` attribute on a
    `IAttributeAnnotatable` object.
    """
    interface.implements(interfaces.IAnnotations)
    component.adapts(interfaces.IAttributeAnnotatable)

    def __init__(self, obj, context=None):
        self.obj = obj

    def __nonzero__(self):
        return bool(getattr(self.obj, '__annotations__', 0))

    def get(self, key, default=None):
        """See zope.annotation.interfaces.IAnnotations"""
        annotations = getattr(self.obj, '__annotations__', None)
        if not annotations:
            return default

        return annotations.get(key, default)

    def __getitem__(self, key):
        annotations = getattr(self.obj, '__annotations__', None)
        if annotations is None:
            raise KeyError(key)

        return annotations[key]

    def keys(self):
        annotations = getattr(self.obj, '__annotations__', None)
        if annotations is None:
            return []

        return annotations.keys()

    def __setitem__(self, key, value):
        """See zope.annotation.interfaces.IAnnotations"""
        try:
            annotations = self.obj.__annotations__
        except AttributeError:
            annotations = self.obj.__annotations__ = OOBTree()

        annotations[key] = value

    def __delitem__(self, key):
        """See zope.app.interfaces.annotation.IAnnotations"""
        try:
            annotation = self.obj.__annotations__
        except AttributeError:
            raise KeyError(key)

        del annotation[key]

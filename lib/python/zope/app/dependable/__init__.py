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
"""Dependable Framework.

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.traversing.api import getParent, canonicalPath, getPath
from zope.annotation.interfaces import IAnnotations

from zope.app.dependable.interfaces import IDependable

class PathSetAnnotation(object):
    """Abstract base class for annotations that are sets of paths.

    To make this into a concrete class, a subclass must set the class
    attribute `key` to a unique annotation key.  A subclass may also
    choose to rename the methods.
    """

    def __init__(self, context):
        self.context = context
        try:
            parent = getParent(self.context)
        except TypeError:
            parent = None
        if parent is not None:
            try:
                pp = getPath(parent)
            except TypeError:
                pp = ""
            if not pp.endswith("/"):
                pp += "/"
            self.pp = pp # parentpath
        else:
            self.pp = ""
        self.pplen = len(self.pp)

    def addPath(self, path):
        path = self._make_relative(path)
        annotations = IAnnotations(self.context)
        old = annotations.get(self.key, ())
        fixed = map(self._make_relative, old)
        if path not in fixed:
            fixed.append(path)
        new = tuple(fixed)
        if new != old:
            annotations[self.key] = new

    def removePath(self, path):
        path = self._make_relative(path)
        annotations = IAnnotations(self.context)
        old = annotations.get(self.key, ())
        if old:
            fixed = map(self._make_relative, old)
            fixed = [loc for loc in fixed if loc != path]
            new = tuple(fixed)
            if new != old:
                if new:
                    annotations[self.key] = new
                else:
                    del annotations[self.key]

    def getPaths(self):
        annotations = IAnnotations(self.context)
        locs = annotations.get(self.key, ())
        return tuple(map(self._make_absolute, locs))

    def _make_relative(self, path):
        if path.startswith("/") and self.pp:
            path = canonicalPath(path)
            if path.startswith(self.pp):
                path = path[self.pplen:]
                while path.startswith("/"):
                    path = path[1:]
        return path

    def _make_absolute(self, path):
        if not path.startswith("/") and self.pp:
            path = self.pp + path
        return path


class Dependable(PathSetAnnotation):
    """See `IDependable`."""

    implements(IDependable)

    key = "zope.app.dependable.Dependents"

    addDependent = PathSetAnnotation.addPath
    removeDependent = PathSetAnnotation.removePath
    dependents = PathSetAnnotation.getPaths

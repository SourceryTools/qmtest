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
"""Convenience functions for traversing the object tree.

$Id: api.py 66514 2006-04-05 11:55:24Z philikon $
"""
from zope.interface import moduleProvides
from zope.traversing.interfaces import IContainmentRoot, ITraversalAPI
from zope.traversing.interfaces import ITraverser, IPhysicallyLocatable
from zope.traversing.interfaces import TraversalError

moduleProvides(ITraversalAPI)
__all__ = tuple(ITraversalAPI)

_marker = object()

def joinPath(path, *args):
    """Join the given relative paths to the given path.

    Returns a unicode path.

    The path should be well-formed, and not end in a '/' unless it is
    the root path. It can be either a string (ascii only) or unicode.
    The positional arguments are relative paths to be added to the
    path as new path segments.  The path may be absolute or relative.

    A segment may not start with a '/' because that would be confused
    with an absolute path. A segment may not end with a '/' because we
    do not allow '/' at the end of relative paths.  A segment may
    consist of . or .. to mean "the same place", or "the parent path"
    respectively. A '.' should be removed and a '..' should cause the
    segment to the left to be removed.  joinPath('/', '..') should
    raise an exception.
    """

    if not args:
        # Concatenating u'' is much quicker than unicode(path)
        return u'' + path
    if path != '/' and path.endswith('/'):
        raise ValueError('path must not end with a "/": %s' % path)
    if path != '/':
        path += u'/'
    for arg in args:
        if arg.startswith('/') or arg.endswith('/'):
            raise ValueError("Leading or trailing slashes in path elements")
    return _normalizePath(path + u'/'.join(args))

def getPath(obj):
    """Returns a string representing the physical path to the object.
    """
    return IPhysicallyLocatable(obj).getPath()

def getRoot(obj):
    """Returns the root of the traversal for the given object.
    """
    return IPhysicallyLocatable(obj).getRoot()

def traverse(object, path, default=_marker, request=None):
    """Traverse 'path' relative to the given object.

    'path' is a string with path segments separated by '/'.

    'request' is passed in when traversing from presentation code. This
    allows paths like @@foo to work.

    Raises TraversalError if path cannot be found

    Note: calling traverse with a path argument taken from an untrusted
          source, such as an HTTP request form variable, is a bad idea.
          It could allow a maliciously constructed request to call
          code unexpectedly.
          Consider using traverseName instead.
    """
    traverser = ITraverser(object)
    if default is _marker:
        return traverser.traverse(path, request=request)
    else:
        return traverser.traverse(path, default=default, request=request)

def traverseName(obj, name, default=_marker, traversable=None, request=None):
    """Traverse a single step 'name' relative to the given object.

    'name' must be a string. '.' and '..' are treated specially, as well as
    names starting with '@' or '+'. Otherwise 'name' will be treated as a
    single path segment.

    You can explicitly pass in an ITraversable as the 'traversable'
    argument. If you do not, the given object will be adapted to ITraversable.

    'request' is passed in when traversing from presentation code. This
    allows paths like @@foo to work.

    Raises TraversalError if path cannot be found and 'default' was
    not provided.

    """
    further_path = []
    if default is _marker:
        obj = traversePathElement(obj, name, further_path,
                                  traversable=traversable, request=request)
    else:
        obj = traversePathElement(obj, name, further_path, default=default,
                                  traversable=traversable, request=request)
    if further_path:
        raise NotImplementedError('further_path returned from traverse')
    else:
        return obj

def getName(obj):
    """Get the name an object was traversed via
    """
    return IPhysicallyLocatable(obj).getName()

def getParent(obj):
    """Returns the container the object was traversed via.

    Returns None if the object is a containment root.
    Raises TypeError if the object doesn't have enough context to get the
    parent.
    """
    
    if IContainmentRoot.providedBy(obj):
        return None
    
    parent = getattr(obj, '__parent__', None)
    if parent is not None:
        return parent

    raise TypeError("Not enough context information to get parent", obj)



def getParents(obj):
    """Returns a list starting with the given object's parent followed by
    each of its parents.

    Raises a TypeError if the context doesn't go all the way down to
    a containment root.
    """
    if IContainmentRoot.providedBy(obj):
        return []

    
    parents = []
    w = obj
    while 1:
        w = w.__parent__
        if w is None:
            break
        parents.append(w)

    if parents and IContainmentRoot.providedBy(parents[-1]):
        return parents

    raise TypeError("Not enough context information to get all parents")


def _normalizePath(path):
    """Normalize a path by resolving '.' and '..' path elements."""

    # Special case for the root path.
    if path == u'/':
        return path

    new_segments = []
    prefix = u''
    if path.startswith('/'):
        prefix = u'/'
        path = path[1:]

    for segment in path.split(u'/'):
        if segment == u'.':
            continue
        if segment == u'..':
            new_segments.pop()  # raises IndexError if there is nothing to pop
            continue
        if not segment:
            raise ValueError('path must not contain empty segments: %s'
                             % path)
        new_segments.append(segment)

    return prefix + u'/'.join(new_segments)

def canonicalPath(path_or_object):
    """Returns a canonical absolute unicode path for the given path or object.

    Resolves segments that are '.' or '..'.

    Raises ValueError if a badly formed path is given.
    """
    if isinstance(path_or_object, (str, unicode)):
        path = path_or_object
        if not path:
            raise ValueError("path must be non-empty: %s" % path)
    else:
        path = getPath(path_or_object)

    path = u'' + path

    # Special case for the root path.
    if path == u'/':
        return path

    if path[0] != u'/':
        raise ValueError('canonical path must start with a "/": %s' % path)
    if path[-1] == u'/':
        raise ValueError('path must not end with a "/": %s' % path)

    # Break path into segments. Process '.' and '..' segments.
    return _normalizePath(path)

# import this down here to avoid circular imports
from zope.traversing.adapters import traversePathElement

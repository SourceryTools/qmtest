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
"""Utility functions for evolving database generations.

$Id$
"""
__docformat__ = "reStructuredText"

from zope.app import zapi

def findObjectsMatching(root, condition):
    """Find all objects in the root that match the condition.

    The condition is a callable Python object that takes an object as an
    argument and must return `True` or `False`.

    All sub-objects of the root will also be searched recursively. All mapping
    objects providing `values()` are supported.

    Example:

    >>> class A(dict):
    ...     def __init__(self, name):
    ...         self.name = name

    >>> class B(dict):
    ...     def __init__(self, name):
    ...         self.name = name

    >>> class C(dict):
    ...     def __init__(self, name):
    ...         self.name = name

    >>> tree = A('a1')
    >>> tree['b1'] = B('b1')
    >>> tree['c1'] = C('c1')
    >>> tree['b1']['a2'] = A('a2')
    >>> tree['b1']['b2'] = B('b2')
    >>> tree['b1']['b2']['c2'] = C('c2')
    >>> tree['b1']['b2']['a3'] = A('a3')

    # Find all instances of class A
    >>> matches = findObjectsMatching(tree, lambda x: isinstance(x, A))
    >>> names = [x.name for x in matches]
    >>> names.sort()
    >>> names
    ['a1', 'a2', 'a3']

    # Find all objects having a '2' in the name
    >>> matches = findObjectsMatching(tree, lambda x: '2' in x.name)
    >>> names = [x.name for x in matches]
    >>> names.sort()
    >>> names
    ['a2', 'b2', 'c2']
    """
    if condition(root):
        yield root

    if hasattr(root, 'values'):
        for subobj in root.values():
            for match in findObjectsMatching(subobj, condition):
                yield match

def findObjectsProviding(root, interface):
    """Find all objects in the root that provide the specified interface.

    All sub-objects of the root will also be searched recursively.

    Example:

    >>> from zope.interface import Interface, implements
    >>> class IA(Interface):
    ...     pass
    >>> class IB(Interface):
    ...     pass
    >>> class IC(IA):
    ...     pass

    >>> class A(dict):
    ...     implements(IA)
    ...     def __init__(self, name):
    ...         self.name = name

    >>> class B(dict):
    ...     implements(IB)
    ...     def __init__(self, name):
    ...         self.name = name

    >>> class C(dict):
    ...     implements(IC)
    ...     def __init__(self, name):
    ...         self.name = name

    >>> tree = A('a1')
    >>> tree['b1'] = B('b1')
    >>> tree['c1'] = C('c1')
    >>> tree['b1']['a2'] = A('a2')
    >>> tree['b1']['b2'] = B('b2')
    >>> tree['b1']['b2']['c2'] = C('c2')
    >>> tree['b1']['b2']['a3'] = A('a3')

    # Find all objects that provide IB
    >>> matches = findObjectsProviding(tree, IB)
    >>> names = [x.name for x in matches]
    >>> names.sort()
    >>> names
    ['b1', 'b2']

    # Find all objects that provide IA
    >>> matches = findObjectsProviding(tree, IA)
    >>> names = [x.name for x in matches]
    >>> names.sort()
    >>> names
    ['a1', 'a2', 'a3', 'c1', 'c2']
    """
    for match in findObjectsMatching(root, interface.providedBy):
        yield match

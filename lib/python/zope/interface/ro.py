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
"""Compute a resolution order for an object and it's bases

$Id: ro.py 25177 2004-06-02 13:17:31Z jim $
"""

def ro(object):
    """Compute a "resolution order" for an object
    """
    return mergeOrderings([_flatten(object, [])])

def mergeOrderings(orderings, seen=None):
    """Merge multiple orderings so that within-ordering order is preserved

    Orderings are constrained in such a way that if an object appears
    in two or more orderings, then the suffix that begins with the
    object must be in both orderings.

    For example:

    >>> _mergeOrderings([
    ... ['x', 'y', 'z'],
    ... ['q', 'z'],
    ... [1, 3, 5],
    ... ['z']
    ... ])
    ['x', 'y', 'q', 1, 3, 5, 'z']

    """

    if seen is None:
        seen = {}
    result = []
    orderings.reverse()
    for ordering in orderings:
        ordering = list(ordering)
        ordering.reverse()
        for o in ordering:
            if o not in seen:
                seen[o] = 1
                result.append(o)

    result.reverse()
    return result

def _flatten(ob, result):
    result.append(ob)
    for base in ob.__bases__:
        _flatten(base, result)

    return result

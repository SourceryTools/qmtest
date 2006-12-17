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
"""This module provides a sample container implementation.

This is primarily for testing purposes.

It might be useful as a mix-in for some classes, but many classes will
need a very different implementation.

$Id: btree.py 26619 2004-07-19 04:19:07Z pruggera $
"""
__docformat__ = 'restructuredtext'

from persistent import Persistent
from BTrees.OOBTree import OOBTree
from zope.app.container.sample import SampleContainer

class BTreeContainer(SampleContainer, Persistent):

    # implements(what my base classes implement)

    # TODO: It appears that BTreeContainer uses SampleContainer only to
    # get the implementation of __setitem__().  All the other methods
    # provided by that base class are just slower replacements for
    # operations on the BTree itself.  It would probably be clearer to
    # just delegate those methods directly to the btree.

    def _newContainerData(self):
        """Construct an item-data container

        Subclasses should override this if they want different data.

        The value returned is a mapping object that also has get,
        has_key, keys, items, and values methods.
        """
        return OOBTree()

    def __contains__(self, key):
        '''See interface IReadContainer

        Reimplement this method, since has_key() returns the key if available,
        while we expect True or False.

        >>> c = BTreeContainer()
        >>> "a" in c
        False
        >>> c["a"] = 1
        >>> "a" in c
        True
        >>> "A" in c
        False
        '''
        return key in self._SampleContainer__data

    has_key = __contains__
        

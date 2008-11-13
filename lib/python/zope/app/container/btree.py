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

$Id: btree.py 77225 2007-06-29 09:20:13Z dobe $
"""
__docformat__ = 'restructuredtext'

from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.Length import Length

from zope.app.container.sample import SampleContainer
from zope.cachedescriptors.property import Lazy

class BTreeContainer(SampleContainer, Persistent):

    # implements(what my base classes implement)

    # TODO: It appears that BTreeContainer uses SampleContainer only to
    # get the implementation of __setitem__().  All the other methods
    # provided by that base class are just slower replacements for
    # operations on the BTree itself.  It would probably be clearer to
    # just delegate those methods directly to the btree.

    def __init__(self):
        super(BTreeContainer, self).__init__()
        self.__len = Length()

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

    @Lazy
    def _BTreeContainer__len(self):
        import logging
        log = logging.getLogger('zope.app.container.btree')
        l=Length()
        ol = super(BTreeContainer, self).__len__()
        if ol>0:
            l.change(ol)
        self._p_changed=True
        log.info("Storing length of %r" % self)
        return l

    def __len__(self):
        #import pdb;pdb.set_trace()
        return self.__len()

    def __setitem__(self, key, value):
        # make sure our lazy property gets set
        l = self.__len
        super(BTreeContainer, self).__setitem__(key, value)
        l.change(1)

    def __delitem__(self, key):
        # make sure our lazy property gets set
        l = self.__len
        super(BTreeContainer, self).__delitem__(key)
        l.change(-1)

    has_key = __contains__

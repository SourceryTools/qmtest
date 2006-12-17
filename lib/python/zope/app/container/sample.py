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
"""Sample container implementation.

This is primarily for testing purposes.

It might be useful as a mix-in for some classes, but many classes will
need a very different implementation.

$Id: sample.py 29246 2005-02-22 11:28:03Z gintautasm $
"""
__docformat__ = 'restructuredtext'

from zope.app.container.interfaces import IContainer
from zope.interface import implements
from zope.app.container.contained import Contained, setitem, uncontained


class SampleContainer(Contained):
    """Sample container implementation suitable for testing.

    It is not suitable, directly as a base class unless the subclass
    overrides `_newContainerData` to return a persistent mapping object.
    """
    implements(IContainer)

    def __init__(self):
        self.__data = self._newContainerData()

    def _newContainerData(self):
        """Construct an item-data container

        Subclasses should override this if they want different data.

        The value returned is a mapping object that also has `get`,
        `has_key`, `keys`, `items`, and `values` methods.
        """
        return {}

    def keys(self):
        '''See interface `IReadContainer`'''
        return self.__data.keys()

    def __iter__(self):
        return iter(self.__data)

    def __getitem__(self, key):
        '''See interface `IReadContainer`'''
        return self.__data[key]

    def get(self, key, default=None):
        '''See interface `IReadContainer`'''
        return self.__data.get(key, default)

    def values(self):
        '''See interface `IReadContainer`'''
        return self.__data.values()

    def __len__(self):
        '''See interface `IReadContainer`'''
        return len(self.__data)

    def items(self):
        '''See interface `IReadContainer`'''
        return self.__data.items()

    def __contains__(self, key):
        '''See interface `IReadContainer`'''
        return self.__data.has_key(key)

    has_key = __contains__

    def __setitem__(self, key, object):
        '''See interface `IWriteContainer`'''
        setitem(self, self.__data.__setitem__, key, object)

    def __delitem__(self, key):
        '''See interface `IWriteContainer`'''
        uncontained(self.__data[key], self, key)
        del self.__data[key]

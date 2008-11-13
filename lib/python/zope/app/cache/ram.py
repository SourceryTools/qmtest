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
"""RAM cache implementation.

$Id: ram.py 77128 2007-06-27 13:32:02Z nouri $
"""
__docformat__ = 'restructuredtext'

from time import time
from threading import Lock
from cPickle import dumps
from persistent import Persistent

from zope.interface import implements
from zope.app.container.contained import Contained
from zope.app.cache.interfaces.ram import IRAMCache


# A global caches dictionary shared between threads
caches = {}

# A writelock for caches dictionary
writelock = Lock()

# A counter for cache ids and its lock
cache_id_counter = 0
cache_id_writelock = Lock()

class RAMCache(Persistent, Contained):
    """RAM Cache

    The design of this class is heavily based on RAMCacheManager in
    Zope2.

    The idea behind the `RAMCache` is that it should be shared between
    threads, so that the same objects are not cached in each thread.
    This is achieved by storing the cache data structure itself as a
    module level variable (`RAMCache.caches`).  This, of course,
    requires locking on modifications of that data structure.

    `RAMCache` is a persistent object.  The actual data storage is a
    volatile object, which can be acquired/created by calling
    ``_getStorage()``.  Storage objects are shared between threads and
    handle their blocking internally.
    """

    implements(IRAMCache)

    def __init__(self):

        # A timestamp and a counter are used here because using just a
        # timestamp and an id (address) produced unit test failures on
        # Windows (where ticks are 55ms long).  If we want to use just
        # the counter, we need to make it persistent, because the
        # RAMCaches are persistent.

        cache_id_writelock.acquire()
        try:
            global cache_id_counter
            cache_id_counter +=1
            self._cacheId = "%s_%f_%d" % (id(self), time(), cache_id_counter)
        finally:
            cache_id_writelock.release()

        self.requestVars = ()
        self.maxEntries = 1000
        self.maxAge = 3600
        self.cleanupInterval = 300

    def getStatistics(self):
        s = self._getStorage()
        return s.getStatistics()

    def update(self,  maxEntries=None, maxAge=None, cleanupInterval=None):
        if maxEntries is not None:
            self.maxEntries = maxEntries

        if maxAge is not None:
            self.maxAge = maxAge

        if cleanupInterval is not None:
            self.cleanupInterval = cleanupInterval

        self._getStorage().update(maxEntries, maxAge, cleanupInterval)

    def invalidate(self, ob, key=None):
        s = self._getStorage()
        if key:
            key =  self._buildKey(key)
            s.invalidate(ob, key)
        else:
            s.invalidate(ob)

    def invalidateAll(self):
        s = self._getStorage()
        s.invalidateAll()

    def query(self, ob, key=None, default=None):
        s = self._getStorage()
        key = self._buildKey(key)
        try:
            return s.getEntry(ob, key)
        except KeyError:
            return default

    def set(self, data, ob, key=None):
        s = self._getStorage()
        key = self._buildKey(key)
        s.setEntry(ob, key, data)

    def _getStorage(self):
        "Finds or creates a storage object."
        cacheId = self._cacheId
        writelock.acquire()
        try:
            if cacheId not in caches:
                caches[cacheId] = Storage(self.maxEntries, self.maxAge,
                                          self.cleanupInterval)
            return caches[cacheId]
        finally:
            writelock.release()

    def _buildKey(kw):
        "Build a tuple which can be used as an index for a cached value"
        if kw:
            items = kw.items()
            items.sort()
            return tuple(items)
        return ()

    _buildKey = staticmethod(_buildKey)


class Storage(object):
    """Storage.

    Storage keeps the count and does the aging and cleanup of cached
    entries.

    This object is shared between threads.  It corresponds to a single
    persistent `RAMCache` object.  Storage does the locking necessary
    for thread safety.

    """

    def __init__(self, maxEntries=1000, maxAge=3600, cleanupInterval=300):
        self._data = {}
        self._misses = {}
        self._invalidate_queue = []
        self.maxEntries = maxEntries
        self.maxAge = maxAge
        self.cleanupInterval = cleanupInterval
        self.writelock = Lock()
        self.lastCleanup = time()

    def update(self, maxEntries=None, maxAge=None, cleanupInterval=None):
        """Set the registration options.

        ``None`` values are ignored.
        """
        if maxEntries is not None:
            self.maxEntries = maxEntries

        if maxAge is not None:
            self.maxAge = maxAge

        if cleanupInterval is not None:
            self.cleanupInterval = cleanupInterval

    def getEntry(self, ob, key):

        if self.lastCleanup <= time() - self.cleanupInterval:
            self.cleanup()

        try:
            data = self._data[ob][key]
        except KeyError:
            if ob not in self._misses:
                self._misses[ob] = 0
            self._misses[ob] += 1
            raise
        else:
            data[2] += 1                    # increment access count
            return data[0]


    def setEntry(self, ob, key, value):
        """Stores a value for the object.  Creates the necessary
        dictionaries."""

        if self.lastCleanup <= time() - self.cleanupInterval:
            self.cleanup()

        self.writelock.acquire()
        try:
            if ob not in self._data:
                self._data[ob] = {}

            timestamp = time()
            # [data, ctime, access count]
            self._data[ob][key] = [value, timestamp, 0]
        finally:
            self.writelock.release()
            self._invalidate_queued()

    def _do_invalidate(self, ob, key=None):
        """This does the actual invalidation, but does not handle the locking.

        This method is supposed to be called from `invalidate`
        """
        try:
            if key is None:
                del self._data[ob]
                self._misses[ob] = 0
            else:
                del self._data[ob][key]
                if not self._data[ob]:
                    del self._data[ob]
        except KeyError:
            pass

    def _invalidate_queued(self):
        """This method should be called after each writelock release."""

        while self._invalidate_queue:
            obj, key = self._invalidate_queue.pop()
            self.invalidate(obj, key)

    def invalidate(self, ob, key=None):
        """Drop the cached values.

        Drop all the values for an object if no key is provided or
        just one entry if the key is provided.

        """
        if self.writelock.acquire(0):
            try:
                self._do_invalidate(ob, key)
            finally:
                self.writelock.release()
                # self._invalidate_queued() not called to avoid a recursion
        else:
            self._invalidate_queue.append((ob, key))

    def invalidateAll(self):
        """Drop all the cached values.
        """
        self.writelock.acquire()
        try:
            self._data = {}
            self._misses = {}
            self._invalidate_queue = []
        finally:
            self.writelock.release()

    def removeStaleEntries(self):
        "Remove the entries older than `maxAge`"

        if self.maxAge > 0:
            punchline = time() - self.maxAge
            self.writelock.acquire()
            try:
                data = self._data
                for object, dict in data.items():
                    for key in dict.keys():
                        if dict[key][1] < punchline:
                            del dict[key]
                            if not dict:
                                del data[object]
            finally:
                self.writelock.release()
                self._invalidate_queued()

    def cleanup(self):
        "Cleanup the data"
        self.removeStaleEntries()
        self.removeLeastAccessed()
        self.lastCleanup = time()

    def removeLeastAccessed(self):
        ""

        self.writelock.acquire()
        try:
            data = self._data
            keys = [(ob, k) for ob, v in data.iteritems() for k in v]

            if len(keys) > self.maxEntries:
                def getKey(item):
                    ob, key = item
                    return data[ob][key][2]
                keys.sort(key=getKey)

                ob, key = keys[self.maxEntries]
                maxDropCount = data[ob][key][2]

                keys.reverse()

                for ob, key in keys:
                    if data[ob][key][2] <= maxDropCount:
                        del data[ob][key]
                        if not data[ob]:
                            del data[ob]

                self._clearAccessCounters()
        finally:
            self.writelock.release()
            self._invalidate_queued()

    def _clearAccessCounters(self):
        for dict in self._data.itervalues():
            for val in dict.itervalues():
                val[2] = 0
        for k in self._misses:
            self._misses[k] = 0

    def getKeys(self, object):
        return self._data[object].keys()

    def getStatistics(self):
        "Basically see IRAMCache"
        objects = self._data.keys()
        objects.sort()
        result = []

        for ob in objects:
            size = len(dumps(self._data[ob]))
            hits = sum(entry[2] for entry in self._data[ob].itervalues())
            result.append({'path': ob,
                           'hits': hits,
                           'misses': self._misses.get(ob, 0),
                           'size': size,
                           'entries': len(self._data[ob])})
        return tuple(result)

__doc__ = RAMCache.__doc__ + __doc__

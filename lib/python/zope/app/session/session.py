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
"""Session implementation

$Id: session.py 70124 2006-09-12 14:17:57Z yusei $
"""
from cStringIO import StringIO
import sha, time, string, random, hmac, warnings, thread, zope.interface
from UserDict import IterableUserDict
from heapq import heapify, heappop

import ZODB
import ZODB.MappingStorage
from persistent import Persistent
from BTrees.OOBTree import OOBTree

from zope import schema
from zope.interface import implements
from zope.component import getUtility, adapts
from zope.component.interfaces import ComponentLookupError
from zope.publisher.interfaces import IRequest
from zope.annotation.interfaces import IAttributeAnnotatable

from interfaces import \
        IClientIdManager, IClientId, ISession, ISessionDataContainer, \
        ISessionPkgData, ISessionData

from http import ICookieClientIdManager

__docformat__ = 'restructuredtext'

cookieSafeTrans = string.maketrans("+/", "-.")

def digestEncode(s):
    """Encode SHA digest for cookie."""
    return s.encode("base64")[:-2].translate(cookieSafeTrans)


class ClientId(str):
    """See zope.app.interfaces.utilities.session.IClientId

        >>> import tests
        >>> request = tests.setUp()

        >>> id1 = ClientId(request)
        >>> id2 = ClientId(request)
        >>> id1 == id2
        True

        >>> tests.tearDown()

    """
    implements(IClientId)
    adapts(IRequest)

    def __new__(cls, request):
        return str.__new__(
                cls, getUtility(IClientIdManager).getClientId(request)
                )


class PersistentSessionDataContainer(Persistent, IterableUserDict):
    """A SessionDataContainer that stores data in the ZODB"""
    __parent__ = __name__ = None

    implements(ISessionDataContainer, IAttributeAnnotatable)

    _v_last_sweep = 0 # Epoch time sweep last run

    def __init__(self):
        self.data = OOBTree()
        self.timeout = 1 * 60 * 60
        self.resolution = 50*60

    def __getitem__(self, pkg_id):
        """Retrieve an ISessionData

            >>> sdc = PersistentSessionDataContainer()

            >>> sdc.timeout = 60
            >>> sdc.resolution = 3
            >>> sdc['clientid'] = sd = SessionData()

        To ensure stale data is removed, we can wind
        back the clock using undocumented means...

            >>> sd.lastAccessTime = sd.lastAccessTime - 64
            >>> sdc._v_last_sweep = sdc._v_last_sweep - 4

        Now the data should be garbage collected

            >>> sdc['clientid']
            Traceback (most recent call last):
                [...]
            KeyError: 'clientid'

        Ensure lastAccessTime on the ISessionData is being updated
        occasionally. The ISessionDataContainer maintains this whenever
        the ISessionData is set or retrieved.

        lastAccessTime on the ISessionData is set when it is added
        to the ISessionDataContainer

            >>> sdc['client_id'] = sd = SessionData()
            >>> sd.lastAccessTime > 0
            True

        lastAccessTime is also updated whenever the ISessionData
        is retrieved through the ISessionDataContainer, at most
        once every 'resolution' seconds.

            >>> then = sd.lastAccessTime = sd.lastAccessTime - 4
            >>> now = sdc['client_id'].lastAccessTime
            >>> now > then
            True
            >>> time.sleep(1)
            >>> now == sdc['client_id'].lastAccessTime
            True

        Ensure lastAccessTime is not modified and no garbage collection
        occurs when timeout == 0. We test this by faking a stale
        ISessionData object.

            >>> sdc.timeout = 0
            >>> sd.lastAccessTime = sd.lastAccessTime - 5000
            >>> lastAccessTime = sd.lastAccessTime
            >>> sdc['client_id'].lastAccessTime == lastAccessTime
            True

        Next, we test session expiration functionality beyond transactions.

            >>> import transaction
            >>> from ZODB.DB import DB
            >>> from ZODB.DemoStorage import DemoStorage
            >>> sdc = PersistentSessionDataContainer()
            >>> sdc.timeout = 60
            >>> sdc.resolution = 3
            >>> db = DB(DemoStorage('test_storage'))
            >>> c = db.open()
            >>> c.root()['sdc'] = sdc
            >>> sdc['pkg_id'] = sd = SessionData()
            >>> sd['name'] = 'bob'
            >>> transaction.commit()

        Access immediately. the data should be accessible.

            >>> c.root()['sdc']['pkg_id']['name']
            'bob'

        Change the clock time and stale the session data.

            >>> sdc = c.root()['sdc']
            >>> sd = sdc['pkg_id']
            >>> sd.lastAccessTime = sd.lastAccessTime - 64
            >>> sdc._v_last_sweep = sdc._v_last_sweep - 4
            >>> transaction.commit()

        The data should be garbage collected.

            >>> c.root()['sdc']['pkg_id']['name']
            Traceback (most recent call last):
                [...]
            KeyError: 'pkg_id'

        Then abort transaction and access the same data again.
        The previous GC was cancelled, but deadline is over.
        The data should be garbage collected again.

            >>> transaction.abort()
            >>> c.root()['sdc']['pkg_id']['name']
            Traceback (most recent call last):
                [...]
            KeyError: 'pkg_id'

        """
        if self.timeout == 0:
            return IterableUserDict.__getitem__(self, pkg_id)

        now = time.time()

        # TODO: When scheduler exists, sweeping should be done by
        # a scheduled job since we are currently busy handling a
        # request and may end up doing simultaneous sweeps

        # If transaction is aborted after sweep. _v_last_sweep keep
        # incorrect sweep time. So when self.data is ghost, revert the time
        # to the previous _v_last_sweep time(_v_old_sweep).
        if self.data._p_state < 0:
            try:
                self._v_last_sweep = self._v_old_sweep
                del self._v_old_sweep
            except AttributeError:
                pass

        if self._v_last_sweep + self.resolution < now:
            self.sweep()
            if getattr(self, '_v_old_sweep', None) is None:
                self._v_old_sweep = self._v_last_sweep
            self._v_last_sweep = now

        rv = IterableUserDict.__getitem__(self, pkg_id)
        # Only update lastAccessTime once every few minutes, rather than
        # every hit, to avoid ZODB bloat and conflicts
        if rv.lastAccessTime + self.resolution < now:
            rv.lastAccessTime = int(now)
        return rv

    def __setitem__(self, pkg_id, session_data):
        """Set an ISessionPkgData

            >>> sdc = PersistentSessionDataContainer()
            >>> sad = SessionData()

        __setitem__ sets the ISessionData's lastAccessTime

            >>> sad.lastAccessTime
            0
            >>> sdc['1'] = sad
            >>> 0 < sad.lastAccessTime <= time.time()
            True

        We can retrieve the same object we put in

            >>> sdc['1'] is sad
            True

        """
        session_data.lastAccessTime = int(time.time())
        return IterableUserDict.__setitem__(self, pkg_id, session_data)

    def sweep(self):
        """Clean out stale data

            >>> sdc = PersistentSessionDataContainer()
            >>> sdc['1'] = SessionData()
            >>> sdc['2'] = SessionData()

        Wind back the clock on one of the ISessionData's
        so it gets garbage collected

            >>> sdc['2'].lastAccessTime -= sdc.timeout * 2

        Sweep should leave '1' and remove '2'

            >>> sdc.sweep()
            >>> sd1 = sdc['1']
            >>> sd2 = sdc['2']
            Traceback (most recent call last):
                [...]
            KeyError: '2'

        """
        # We only update the lastAccessTime every 'resolution' seconds.
        # To compensate for this, we factor in the resolution when
        # calculating the expiry time to ensure that we never remove
        # data that has been accessed within timeout seconds.
        expire_time = time.time() - self.timeout - self.resolution
        heap = [(v.lastAccessTime, k) for k,v in self.data.items()]
        heapify(heap)
        while heap:
            lastAccessTime, key = heappop(heap)
            if lastAccessTime < expire_time:
                del self.data[key]
            else:
                return


class RAMSessionDataContainer(PersistentSessionDataContainer):
    """A SessionDataContainer that stores data in RAM.

    Currently session data is not shared between Zope clients, so
    server affinity will need to be maintained to use this in a ZEO cluster.

        >>> sdc = RAMSessionDataContainer()
        >>> sdc['1'] = SessionData()
        >>> sdc['1'] is sdc['1']
        True
        >>> ISessionData.providedBy(sdc['1'])
        True

    """
    def __init__(self):
        self.resolution = 5*60
        self.timeout = 1 * 60 * 60
        # Something unique
        self.key = '%s.%s.%s' % (time.time(), random.random(), id(self))

    _ram_storage = ZODB.MappingStorage.MappingStorage()
    _ram_db = ZODB.DB(_ram_storage)
    _conns = {}

    def _getData(self):

        # Open a connection to _ram_storage per thread
        tid = thread.get_ident()
        if not self._conns.has_key(tid):
            self._conns[tid] = self._ram_db.open()

        root = self._conns[tid].root()
        if not root.has_key(self.key):
            root[self.key] = OOBTree()
        return root[self.key]

    data = property(_getData, None)

    def sweep(self):
        super(RAMSessionDataContainer, self).sweep()
        self._ram_db.pack(time.time())


class Session(object):
    """See zope.app.session.interfaces.ISession"""
    implements(ISession)
    adapts(IRequest)

    def __init__(self, request):
        self.client_id = str(IClientId(request))

    def __getitem__(self, pkg_id):
        """See zope.app.session.interfaces.ISession

            >>> import tests
            >>> request = tests.setUp(PersistentSessionDataContainer)
            >>> request2 = tests.HTTPRequest(StringIO(''), {}, None)

            >>> ISession.providedBy(Session(request))
            True

        Setup some sessions, each with a distinct namespace

            >>> session1 = Session(request)['products.foo']
            >>> session2 = Session(request)['products.bar']
            >>> session3 = Session(request2)['products.bar']

        If we use the same parameters, we should retrieve the
        same object

            >>> session1 is Session(request)['products.foo']
            True

        Make sure it returned sane values

            >>> ISessionPkgData.providedBy(session1)
            True

        Make sure that pkg_ids don't share a namespace.

            >>> session1['color'] = 'red'
            >>> session2['color'] = 'blue'
            >>> session3['color'] = 'vomit'
            >>> session1['color']
            'red'
            >>> session2['color']
            'blue'
            >>> session3['color']
            'vomit'

            >>> tests.tearDown()

        """

        # First locate the ISessionDataContainer by looking up
        # the named Utility, and falling back to the unnamed one.
        try:
            sdc = getUtility(ISessionDataContainer, pkg_id)
        except ComponentLookupError:
            sdc = getUtility(ISessionDataContainer)

        # The ISessionDataContainer contains two levels:
        # ISessionDataContainer[client_id] == ISessionData
        # ISessionDataContainer[client_id][pkg_id] == ISessionPkgData
        try:
            sd = sdc[self.client_id]
        except KeyError:
            sd = sdc[self.client_id] = SessionData()

        try:
            return sd[pkg_id]
        except KeyError:
            spd = sd[pkg_id] = SessionPkgData()
            return spd


class SessionData(Persistent, IterableUserDict):
    """See zope.app.session.interfaces.ISessionData

        >>> session = SessionData()
        >>> ISessionData.providedBy(session)
        True
        >>> session.lastAccessTime
        0

    """
    implements(ISessionData)
    lastAccessTime = 0
    def __init__(self):
        self.data = OOBTree()


class SessionPkgData(Persistent, IterableUserDict):
    """See zope.app.session.interfaces.ISessionData

        >>> session = SessionPkgData()
        >>> ISessionPkgData.providedBy(session)
        True
    """
    implements(ISessionPkgData)
    def __init__(self):
        self.data = OOBTree()


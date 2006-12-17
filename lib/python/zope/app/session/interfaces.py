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
"""Interfaces for session utility.

$Id: interfaces.py 40311 2005-11-22 09:24:25Z Zen $
"""
from zope.interface import Interface
from zope.interface.common.mapping import IMapping, IReadMapping, IWriteMapping
from zope import schema
from zope.app.container.interfaces import IContainer
from zope.app.i18n import ZopeMessageFactory as _

__docformat__ = 'restructuredtext'

class IClientIdManager(Interface):
    """Manages sessions - fake state over multiple client requests."""

    def getClientId(request):
        """Return the client id for the given request as a string.
        
        If the request doesn't have an attached sessionId a new one will be
        generated.

        This will do whatever is possible to do the HTTP request to ensure the
        session id will be preserved. Depending on the specific method,
        further action might be necessary on the part of the user.  See the
        documentation for the specific implementation and its interfaces.

        """


class IClientId(Interface):
    """A unique id representing a session"""

    def __str__():
        """As a unique ASCII string"""


class ISessionDataContainer(IReadMapping, IWriteMapping):
    """Stores data objects for sessions.

    The object implementing this interface is responsible for expiring data as
    it feels appropriate.

    Usage::

      session_data_container[client_id][product_id][key] = value

    Note that this interface does not support the full mapping interface -
    the keys need to remain secret so we can't give access to keys(), 
    values() etc.

    """
    timeout = schema.Int(
            title=_(u"Timeout"),
            description=_(
                "Number of seconds before data becomes stale and may "
                "be removed. A value of '0' means no expiration."),
            default=3600,
            required=True,
            min=0,
            )
    resolution = schema.Int(
            title=_("Timeout resolution (in seconds)"),
            description=_(
                "Defines what the 'resolution' of item timeout is. "
                "Setting this higher allows the transience machinery to "
                "do fewer 'writes' at the expense of  causing items to time "
                "out later than the 'Data object timeout value' by  a factor "
                "of (at most) this many seconds."
                ),
            default=5*60,
            required=True,
            min=0,
            )

    def __getitem__(self, product_id):
        """Return an ISessionPkgData"""

    def __setitem__(self, product_id, value):
        """Store an ISessionPkgData"""


class ISession(Interface):
    """This object allows retrieval of the correct ISessionData
    for a particular product id
    
        >>> session = ISession(request)[product_id]
        >>> session['color'] = 'red'
        True

        >>> ISessionData.providedBy(session)
        True

    """

    def __getitem__(product_id):
        """Return the relevant ISessionPkgData
        
        This involves locating the correct ISessionDataContainer for the 
        given product id, determining the client id, and returning the
        relevant ISessionPkgData.
        
        """


class ISessionData(IReadMapping, IMapping):
    """Storage for a particular product id's session data
    
    Contains 0 or more ISessionPkgData instances
    
    """

    lastAccessTime = schema.Int(
            title=_("Last Access Time"),
            description=_(
                "Approximate epoch time this ISessionData was last retrieved "
                "from its ISessionDataContainer"
                ),
            default=0,
            required=True,
            )

    # Note that only IReadMapping and IWriteMaping are implemented.
    # We cannot give access to the keys, as they need to remain secret.

    def __getitem__(self, client_id):
        """Return an ISessionPkgData"""

    def __setitem__(self, client_id, session_pkg_data):
        """Store an ISessionPkgData"""


class ISessionPkgData(IMapping):
    """Storage for a particular product id and browser id's session data

    Data is stored persistently and transactionally. Data stored must
    be persistent or picklable.

    """

# BBB, generation 0, 2004-07-12

IBrowserIdManager = IClientIdManager

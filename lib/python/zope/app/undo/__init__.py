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
"""Undo Support

$Id: __init__.py 68942 2006-07-02 10:18:06Z philikon $
"""
from datetime import datetime

import transaction
import zope.component
from zope.interface import implements
from zope.traversing.interfaces import IPhysicallyLocatable

from zope.app.undo.interfaces import IUndoManager, UndoError
from zope.app.security.interfaces import IAuthentication, IPrincipal
from zope.app.security.interfaces import PrincipalLookupError

def undoSetup(event):
    # setup undo functionality
    sm = zope.component.getGlobalSiteManager()
    sm.registerUtility(ZODBUndoManager(event.database), IUndoManager)

class Prefix(unicode):
    """A prefix is equal to any string it is a prefix of.

    This class can be compared to a string (or arbitrary sequence).
    The comparison will return True if the prefix value is a prefix of
    the string being compared.

    Two prefixes cannot safely be compared.

    It does not matter from which side you compare with a prefix:

    >>> p = Prefix('str')
    >>> p == 'string'
    True
    >>> 'string' == p
    True

    You can also test for inequality:

    >>> p != 'string'
    False
    >>> 'string' != p
    False

    Unicode works, too:

    >>> p == u'string'
    True
    >>> u'string' == p
    True
    >>> p != u'string'
    False
    >>> u'string' != p
    False

    >>> p = Prefix('foo')
    >>> p == 'bar'
    False
    >>> 'bar' == p
    False

    >>> p != 'bar'
    True
    >>> 'bar' != p
    True

    >>> p == None
    False
    """
    def __eq__(self, other):
        if other and unicode(other[:len(self)]).__cmp__(self) == 0:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class ZODBUndoManager(object):
    """Implement the basic undo management API for a single ZODB database."""
    implements(IUndoManager)

    def __init__(self, db):
        self.__db = db

    def getTransactions(self, context=None, first=0, last=-20):
        """See zope.app.undo.interfaces.IUndo"""
        return self._getUndoInfo(context, None, first, last)

    def getPrincipalTransactions(self, principal, context=None,
                                 first=0, last=-20):
        """See zope.app.undo.interfaces.IPrincipal"""
        if not IPrincipal.providedBy(principal):
            raise TypeError("Invalid principal: %s" % principal)
        return self._getUndoInfo(context, principal, first, last)

    def _getUndoInfo(self, context, principal, first, last):
        specification = {}

        if context is not None:
            locatable = IPhysicallyLocatable(context, None)
            if locatable is not None:
                location = Prefix(locatable.getPath())
                specification.update({'location': location})

        if principal is not None:
            # TODO: The 'user' in the transactions is a concatenation
            # of 'path' and 'user' (id).  'path' used to be the path
            # of the user folder in Zope 2.  ZopePublication currently
            # does not set a path, so ZODB lets the path default to
            # '/'.  We should change ZODB3 to set no default path at
            # some point
            path = '/' # default for now
            specification.update({'user_name': path + ' ' + principal.id})

        entries = self.__db.undoInfo(first, last, specification)

        # We walk through the entries, augmenting the dictionaries 
        # with some additional items we have promised in the interface
        for entry in entries:
            entry['datetime'] = datetime.fromtimestamp(entry['time'])
            entry['principal'] = None

            user_name = entry['user_name']
            if user_name:
                # TODO: This is because of ZODB3/Zope2 cruft regarding
                # the user path (see comment above).  This 'if' block
                # should go away.
                split = user_name.split()
                if len(split) == 2:
                    user_name = split[1]
            if user_name:
                try:
                    principal = zope.component.getUtility(
                        IAuthentication).getPrincipal(user_name)
                    entry['principal'] = principal
                except PrincipalLookupError:
                    # principals might have passed away
                    pass
        return entries

    def undoTransactions(self, ids):
        """See zope.app.undo.interfaces.IUndo"""
        self._undo(ids)

    def undoPrincipalTransactions(self, principal, ids):
        """See zope.app.undo.interfaces.IPrincipal"""
        if not IPrincipal.providedBy(principal):
            raise TypeError("Invalid principal: %s" % principal)

        # Make sure we only undo the transactions initiated by our
        # principal
        left_overs = list(ids)
        first = 0
        batch_size = 20
        txns = self._getUndoInfo(None, principal, first, -batch_size)
        while txns and left_overs:
            for info in txns:
                if (info['id'] in left_overs and
                    info['principal'].id == principal.id):
                    left_overs.remove(info['id'])
            first += batch_size
            txns = self._getUndoInfo(None, principal, first, -batch_size)
        if left_overs:
            raise UndoError("You are trying to undo a transaction that "
                            "either does not exist or was not initiated "
                            "by the principal.")
        self._undo(ids)

    def _undo(self, ids):
        for id in ids:
            self.__db.undo(id)
        transaction.get().setExtendedInfo('undo', True)

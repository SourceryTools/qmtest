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
"""Undo Interfaces

$Id: interfaces.py 26567 2004-07-16 06:58:27Z srichter $
"""

from zope.interface import Interface

class UndoError(Exception):
    pass

class IUndo(Interface):
    """Undo functionality"""

    def getTransactions(context=None, first=0, last=-20):
        """Return a sequence of mapping objects describing
        transactions, ordered by date, descending:

        Keys of mapping objects:

          id           -> internal id for zodb
          principal    -> principal that invoked the transaction
          datetime     -> datetime object of time
          description  -> description/note (string)

          Extended information (not necessarily available):
          request_type -> type of request that caused transaction
          request_info -> request information, e.g. URL, method
          location     -> location of the object that was modified
          undo         -> boolean value, indicated an undo transaction

        If 'context' is None, all transactions will be listed,
        otherwise only transactions for that location.

        It skips the 'first' most recent transactions; i.e. if first
        is N, then the first transaction returned will be the Nth
        transaction.

        If last is less than zero, then its absolute value is the
        maximum number of transactions to return.  Otherwise if last
        is N, then only the N most recent transactions following start
        are considered.
        """

    def undoTransactions(ids):
        """Undo the transactions specified in the sequence 'ids'.
        """

class IPrincipalUndo(Interface):
    """Undo functionality for one specific principal"""

    def getPrincipalTransactions(principal, context=None, first=0, last=-20):
        """Returns transactions invoked by the given principal.

        See IUndo.getTransactions() for more information
        """

    def undoPrincipalTransactions(principal, ids):
        """Undo the transactions invoked by 'principal' with the given
        'ids'. Raise UndoError if a transaction is listed among 'ids'
        that does not belong to 'principal'.
        """

class IUndoManager(IUndo, IPrincipalUndo):
    """Utility to provide both global and principal-specific undo
    functionality
    """

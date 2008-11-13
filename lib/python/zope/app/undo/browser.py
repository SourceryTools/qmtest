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
"""Undo view

$Id: browser.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.component
from zope.security.interfaces import ForbiddenAttribute
from zope.publisher.browser import BrowserView
from zope.app.undo.interfaces import IUndoManager

class UndoView(BrowserView):
    """Undo view"""

    def principalLastTransactionIsUndo(self):
        """Return True if the authenticated principal's last
        transaction is an undo transaction.
        """
        request = self.request
        undo = zope.component.getUtility(IUndoManager)
        txn_info = undo.getPrincipalTransactions(request.principal, first=0,
                                                 last=1)
        if txn_info:
            return txn_info[0].get('undo', False)
        return False

    def undoPrincipalLastTransaction(self):
        """Undo the authenticated principal's last transaction and
        return where he/she came from"""
        request = self.request
        undo = zope.component.getUtility(IUndoManager)
        txn_info = undo.getPrincipalTransactions(request.principal, first=0,
                                                 last=1)
        if txn_info:
            id = txn_info[0]['id']
            undo.undoPrincipalTransactions(request.principal, [id])
        target = request.get('HTTP_REFERER', '@@SelectedManagementView.html')
        request.response.redirect(target)

    def undoAllTransactions(self, ids):
        """Undo transactions specified in 'ids'."""
        undo = zope.component.getUtility(IUndoManager)
        undo.undoTransactions(ids)
        self._redirect()

    def undoPrincipalTransactions(self, ids):
        """Undo transactions that were issued by the authenticated
        user specified in 'ids'."""
        undo = zope.component.getUtility(IUndoManager)
        undo.undoPrincipalTransactions(self.request.principal, ids)
        self._redirect()

    def _redirect(self):
        target = "@@SelectedManagementView.html"
        self.request.response.redirect(target)

    def getAllTransactions(self, first=0, last=-20, showall=False):
        context = None
        if not showall:
            context = self.context
        undo = zope.component.getUtility(IUndoManager)
        return undo.getTransactions(context, first, last)

    def getPrincipalTransactions(self, first=0, last=-20, showall=False):
        context = None
        if not showall:
            context = self.context
        undo = zope.component.getUtility(IUndoManager)
        return undo.getPrincipalTransactions(self.request.principal, context,
                                             first, last)

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
"""A simple implementation of a Message Catalog.

$Id: messagecatalog.py 27237 2004-08-23 23:42:11Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import classProvides, providedBy, implements
import time

from BTrees.OOBTree import OOBTree
from persistent import Persistent
from zope.component.interfaces import IFactory
from zope.app.i18n.interfaces import ILocalMessageCatalog


class MessageCatalog(Persistent):

    implements(ILocalMessageCatalog)
    classProvides(IFactory)

    def __init__(self, language, domain="default"):
        """Initialize the message catalog"""
        self.id  = ''
        self.title = ''
        self.description = ''
        self.language = language
        self.domain = domain
        self._messages = OOBTree()

    def getMessage(self, id):
        'See `IReadMessageCatalog`'
        return self._messages[id][0]

    def queryMessage(self, id, default=None):
        'See `IReadMessageCatalog`'
        result = self._messages.get(id)
        if result is not None:
            result = result[0]
        else:
            result = default
        return result

    def getIdentifier(self):
        'See `IReadMessageCatalog`'
        return (self.language, self.domain)

    def getFullMessage(self, msgid):
        'See `IWriteMessageCatalog`'
        message = self._messages[msgid]
        return {'domain'   : self.domain,
                'language' : self.language,
                'msgid'    : msgid,
                'msgstr'   : message[0],
                'mod_time' : message[1]}

    def setMessage(self, msgid, message, mod_time=None):
        'See `IWriteMessageCatalog`'
        if mod_time is None:
            mod_time = int(time.time())
        self._messages[msgid] = (message, mod_time)

    def deleteMessage(self, msgid):
        'See `IWriteMessageCatalog`'
        del self._messages[msgid]

    def getMessageIds(self):
        'See IWriteMessageCatalog'
        return list(self._messages.keys())

    def getMessages(self):
        'See `IWriteMessageCatalog`'
        messages = []
        for message in self._messages.items():
            messages.append({'domain'   : self.domain,
                             'language' : self.language,
                             'msgid'    : message[0],
                             'msgstr'   : message[1][0],
                             'mod_time' : message[1][1]})
        return messages

    def getInterfaces(self):
        'See `IFactory`'
        return tuple(providedBy(self))

    getInterfaces = classmethod(getInterfaces)

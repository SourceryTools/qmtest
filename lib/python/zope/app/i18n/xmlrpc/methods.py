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
"""Translation Domain XML-RPC Methods 

$Id: methods.py 27322 2004-08-28 00:59:04Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.app.publisher.xmlrpc import XMLRPCView

class Methods(XMLRPCView):

    def getAllLanguages(self):
        return self.context.getAllLanguages()

    def getMessagesFor(self, languages):
        messages = []
        for msg in self.context.getMessages():
            if msg['language'] in languages:
                messages.append(msg)

        return messages

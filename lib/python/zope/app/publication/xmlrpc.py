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
"""XML-RPC Publication Handler.

This module specifically implements a custom `nameTraverse()` method.

$Id: xmlrpc.py 27311 2004-08-27 21:22:43Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.app.publication.http import BaseHTTPPublication

# Don't need any special handling for xml-rpc
XMLRPCPublication = BaseHTTPPublication

class XMLRPCPublicationFactory(object):

    def __init__(self, db):
        self.__pub = XMLRPCPublication(db)

    def __call__(self):
        return self.__pub

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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Test FTP Publication.

$Id: ftp.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.publisher.interfaces import NotFound
from zope.publisher.publish import mapply

from zope.app import zapi
from zope.app.publication.zopepublication import ZopePublication



class FTPPublication(ZopePublication):
    """The Publication will do all the work for the FTP"""

    def callObject(self, request, ob):
        method = request['command']
        view = zapi.queryMultiAdapter((ob, request), name=method, default=self)
        if view is self:
            raise NotFound(ob, method, request)

        return mapply(getattr(view, method), (), request)

    def annotateTransaction(self, txn, request, ob):
        txn = super(FTPPublication, self).annotateTransaction(txn, request, ob)
        request_info = [request['command']]
        path = request.get('path', '')
        if path:
            request_info.append(path)
        name = request.get('name', '')
        if name:
            request_info.append(name)
        request_info = ' '.join(request_info)
        txn.setExtendedInfo('request_info', request_info)
        return txn

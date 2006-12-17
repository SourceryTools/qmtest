##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Not found Exception

$Id: notfound.py 26816 2004-07-28 19:09:51Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.app.http.interfaces import IHTTPException
from zope.interface import implements

class NotFound(object):

    implements(IHTTPException)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        if self.request.method in ['MKCOL'] and \
               self.request.getTraversalStack():
            # MKCOL with non-existing parent.
            self.request.response.setStatus(409)
        else:
            self.request.response.setStatus(404)
        return ''

    __str__ = __call__

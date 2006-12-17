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
"""FTP Publisher

$Id: ftp.py 41619 2006-02-14 14:04:04Z niemeyer $
"""
from zope.interface import implements
from zope.publisher.interfaces.ftp import IFTPCredentials, IFTPRequest
from zope.publisher.base import BaseResponse, BaseRequest

class FTPResponse(BaseResponse):
    __slots__ = '_exc', # Saved exception

    def outputBody(self):
        # Nothing to do
        pass

    def getResult(self):
        if getattr(self, '_exc', None) is not None:
            raise self._exc[0], self._exc[1], self._exc[2]
        return self._result

    def handleException(self, exc_info):
        self._exc = exc_info

class FTPRequest(BaseRequest):
    implements(IFTPCredentials, IFTPRequest)

    __slots__ = '_auth'

    def __init__(self, body_instream, environ, response=None, bbb=None):
        # BBB: This is backward-compatibility support for the deprecated
        # output stream.
        try:
            self._auth = environ.get('credentials')
        except AttributeError:
            import warnings
            warnings.warn("Can't pass output streams to requests anymore. "
                          "This will go away in Zope 3.4.",
                          DeprecationWarning,
                          2)
            environ, response = response, bbb
            self._auth = environ.get('credentials')

        del environ['credentials']

        super(FTPRequest, self).__init__(body_instream, environ, response)

        path = environ['path']
        if path.startswith('/'):
            path = path[1:]
        if path:
            path = path.split('/')
            path.reverse()
            self.setTraversalStack(path)


    def _createResponse(self):
        """Create a specific FTP response object."""
        return FTPResponse()

    def _authUserPW(self):
        'See IFTPCredentials'
        return self._auth

    def unauthorized(self, challenge):
        'See IFTPCredentials'


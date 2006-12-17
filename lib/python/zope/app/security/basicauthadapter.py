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
"""HTTP Basic Authentication adapter

$Id: basicauthadapter.py 69465 2006-08-14 12:49:46Z ctheune $
"""
from zope.publisher.interfaces.http import IHTTPCredentials
from loginpassword import LoginPassword


class BasicAuthAdapter(LoginPassword):
    """Adapter for handling HTTP Basic Auth."""

    __used_for__ = IHTTPCredentials

    __request = None

    def __init__(self, request):
        self.__request = request
        # TODO base64 decoding should be done here, not in request
        lpw = request._authUserPW()
        if lpw is None:
            login, password = None, None
        else:
            login, password = lpw
        LoginPassword.__init__(self, login, password)

    def needLogin(self, realm):
        self.__request.unauthorized('basic realm="%s"'% realm)

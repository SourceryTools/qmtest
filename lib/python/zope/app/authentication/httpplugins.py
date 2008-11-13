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
"""PAS plugins related to HTTP

$Id: httpplugins.py 69466 2006-08-14 13:09:26Z ctheune $
"""
__docformat__ = "reStructuredText"
import base64
from persistent import Persistent
from zope.interface import implements, Interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope.schema import TextLine

from zope.app.container.contained import Contained
from zope.app.authentication import interfaces


class IHTTPBasicAuthRealm(Interface):
    """HTTP Basic Auth Realm

    Represents the realm string that is used during basic HTTP authentication
    """

    realm = TextLine(title=u'Realm',
                     description=u'HTTP Basic Authentication Realm',
                     required=True,
                     default=u'Zope')


class HTTPBasicAuthCredentialsPlugin(Persistent, Contained):

    implements(interfaces.ICredentialsPlugin, IHTTPBasicAuthRealm)

    realm = 'Zope'

    protocol = 'http auth'

    def extractCredentials(self, request):
        """Extracts HTTP basic auth credentials from a request.

        First we need to create a request that contains some credentials.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest(
          ...     environ={'HTTP_AUTHORIZATION': u'Basic bWdyOm1ncnB3'})

        Now create the plugin and get the credentials.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> plugin.extractCredentials(request)
          {'login': u'mgr', 'password': u'mgrpw'}

        Make sure we return `None`, if no authentication header has been
        specified.

          >>> print plugin.extractCredentials(TestRequest())
          None

        Also, this plugin can *only* handle basic authentication.

          >>> request = TestRequest(environ={'HTTP_AUTHORIZATION': 'foo bar'})
          >>> print plugin.extractCredentials(TestRequest())
          None

        This plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> print plugin.extractCredentials(TestRequest('/'))
          None

        """
        if not IHTTPRequest.providedBy(request):
            return None

        if request._auth:
            if request._auth.lower().startswith(u'basic '):
                credentials = request._auth.split()[-1]
                login, password = base64.decodestring(credentials).split(':')
                return {'login': login.decode('utf-8'),
                        'password': password.decode('utf-8')}
        return None

    def challenge(self, request):
        """Issues an HTTP basic auth challenge for credentials.

        The challenge is issued by setting the appropriate response headers.
        To illustrate, we'll create a plugin:

          >>> plugin = HTTPBasicAuthCredentialsPlugin()

        The plugin adds its challenge to the HTTP response.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()
          >>> response = request.response
          >>> plugin.challenge(request)
          True
          >>> response._status
          401
          >>> response.getHeader('WWW-Authenticate', literal=True)
          'basic realm="Zope"'

        Notice that the realm is quoted, as per RFC 2617.

        The plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> request = TestRequest('/')
          >>> response = request.response
          >>> print plugin.challenge(request)
          False

        """
        if not IHTTPRequest.providedBy(request):
            return False
        request.response.setHeader("WWW-Authenticate",
                                   'basic realm="%s"' % self.realm,
                                   literal=True)
        request.response.setStatus(401)
        return True

    def logout(self, request):
        """Always returns False as logout is not supported by basic auth.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> from zope.publisher.browser import TestRequest
          >>> plugin.logout(TestRequest())
          False

        """
        return False

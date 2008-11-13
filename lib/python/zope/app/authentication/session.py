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
""" Implementations of the session-based and cookie-based extractor and
    challenge plugins.

$Id: session.py 80262 2007-09-27 23:47:04Z srichter $
"""
__docformat__ = 'restructuredtext'

import transaction
from persistent import Persistent
from urllib import urlencode

from zope.interface import implements, Interface
from zope.schema import TextLine
from zope.publisher.interfaces.http import IHTTPRequest
from zope.session.interfaces import ISession
from zope.traversing.browser.absoluteurl import absoluteURL

from zope.app.component import hooks
from zope.app.container.contained import Contained
from zope.app.authentication.interfaces import ICredentialsPlugin

class ISessionCredentials(Interface):
    """ Interface for storing and accessing credentials in a session.

        We use a real class with interface here to prevent unauthorized
        access to the credentials.
    """

    def __init__(login, password):
        pass

    def getLogin():
        """Return login name."""

    def getPassword():
        """Return password."""


class SessionCredentials(object):
    """Credentials class for use with sessions.

    A session credential is created with a login and a password:

      >>> cred = SessionCredentials('scott', 'tiger')

    Logins are read using getLogin:
      >>> cred.getLogin()
      'scott'

    and passwords with getPassword:

      >>> cred.getPassword()
      'tiger'

    """
    implements(ISessionCredentials)

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def getLogin(self): return self.login

    def getPassword(self): return self.password

    def __str__(self): return self.getLogin() + ':' + self.getPassword()


class IBrowserFormChallenger(Interface):
    """A challenger that uses a browser form to collect user credentials."""

    loginpagename = TextLine(
        title=u'Loginpagename',
        description=u"""Name of the login form used by challenger.

        The form must provide 'login' and 'password' input fields.
        """,
        default=u'loginForm.html')

    loginfield = TextLine(
        title=u'Loginfield',
        description=u"Field of the login page in which is looked for the login user name.",
        default=u"login")

    passwordfield = TextLine(
        title=u'Passwordfield',
        description=u"Field of the login page in which is looked for the password.",
        default=u"password")


class SessionCredentialsPlugin(Persistent, Contained):
    """A credentials plugin that uses Zope sessions to get/store credentials.

    To illustrate how a session plugin works, we'll first setup some session
    machinery:

      >>> from zope.session.session import RAMSessionDataContainer
      >>> from tests import sessionSetUp
      >>> sessionSetUp(RAMSessionDataContainer)

    This lets us retrieve the same session info from any test request, which
    simulates what happens when a user submits a session ID as a cookie.

    We also need a session plugin:

      >>> plugin = SessionCredentialsPlugin()

    A session plugin uses an ISession component to store the last set of
    credentials it gets from a request. Credentials can be retrieved from
    subsequent requests using the session-stored credentials.

    Our test environment is initially configured without credentials:

      >>> from tests import sessionSetUp
      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> print plugin.extractCredentials(request)
      None

    We must explicitly provide credentials once so the plugin can store
    them in a session:

      >>> request = TestRequest(login='scott', password='tiger')
      >>> plugin.extractCredentials(request)
      {'login': 'scott', 'password': 'tiger'}

    Subsequent requests now have access to the credentials even if they're
    not explicitly in the request:

      >>> plugin.extractCredentials(TestRequest())
      {'login': 'scott', 'password': 'tiger'}

    We can always provide new credentials explicitly in the request:

      >>> plugin.extractCredentials(TestRequest(
      ...     login='harry', password='hirsch'))
      {'login': 'harry', 'password': 'hirsch'}

    and these will be used on subsequent requests:

      >>> plugin.extractCredentials(TestRequest())
      {'login': 'harry', 'password': 'hirsch'}

    We can also change the fields from which the credentials are extracted:

      >>> plugin.loginfield = "my_new_login_field"
      >>> plugin.passwordfield = "my_new_password_field"

    Now we build a request that uses the new fields:

      >>> request = TestRequest(my_new_login_field='luke', my_new_password_field='the_force')

    The plugin now extracts the credentials information from these new fields:

      >>> plugin.extractCredentials(request)
      {'login': 'luke', 'password': 'the_force'}

    Finally, we clear the session credentials using the logout method:

      >>> plugin.logout(TestRequest())
      True
      >>> print plugin.extractCredentials(TestRequest())
      None

    """
    implements(ICredentialsPlugin, IBrowserFormChallenger)

    loginpagename = 'loginForm.html'
    loginfield = 'login'
    passwordfield = 'password'

    def extractCredentials(self, request):
        """Extracts credentials from a session if they exist."""
        if not IHTTPRequest.providedBy(request):
            return None
        session = ISession(request)
        sessionData = session.get(
            'zope.app.authentication.browserplugins')
        login = request.get(self.loginfield, None)
        password = request.get(self.passwordfield, None)
        credentials = None

        if login and password:
            credentials = SessionCredentials(login, password)
        elif not sessionData:
            return None
        sessionData = session[
            'zope.app.authentication.browserplugins']
        if credentials:
            sessionData['credentials'] = credentials
        else:
            credentials = sessionData.get('credentials', None)
        if not credentials:
            return None
        return {'login': credentials.getLogin(),
                'password': credentials.getPassword()}

    def challenge(self, request):
        """Challenges by redirecting to a login form.

        To illustrate, we'll create a test request:

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()

        and confirm its response's initial status and 'location' header:

          >>> request.response.getStatus()
          599
          >>> request.response.getHeader('location')

        When we issue a challenge using a session plugin:

          >>> plugin = SessionCredentialsPlugin()
          >>> plugin.challenge(request)
          True

        we get a redirect:

          >>> request.response.getStatus()
          302
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@loginForm.html?camefrom=%2F'

        The plugin redirects to the page defined by the loginpagename
        attribute:

          >>> plugin.loginpagename = 'mylogin.html'
          >>> plugin.challenge(request)
          True
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@mylogin.html?camefrom=%2F'

        It also provides the request URL as a 'camefrom' GET style parameter.
        To illustrate, we'll pretend we've traversed a couple names:

          >>> env = {
          ...     'REQUEST_URI': '/foo/bar/folder/page%201.html?q=value',
          ...     'QUERY_STRING': 'q=value'
          ...     }
          >>> request = TestRequest(environ=env)
          >>> request._traversed_names = [u'foo', u'bar']
          >>> request._traversal_stack = [u'page 1.html', u'folder']
          >>> request['REQUEST_URI']
          '/foo/bar/folder/page%201.html?q=value'

        When we challenge:

          >>> plugin.challenge(request)
          True

        We see the 'camefrom' points to the requested URL:

          >>> request.response.getHeader('location') # doctest: +ELLIPSIS
          '.../@@mylogin.html?camefrom=%2Ffoo%2Fbar%2Ffolder%2Fpage+1.html%3Fq%3Dvalue'

        This can be used by the login form to redirect the user back to the
        originating URL upon successful authentication.
        """
        if not IHTTPRequest.providedBy(request):
            return False

        site = hooks.getSite()
        # We need the traversal stack to complete the 'camefrom' parameter
        stack = request.getTraversalStack()
        stack.reverse()
        # Better to add the query string, if present
        query = request.get('QUERY_STRING')

        camefrom = '/'.join([request.getURL(path_only=True)] + stack)
        if query:
            camefrom = camefrom + '?' + query
        url = '%s/@@%s?%s' % (absoluteURL(site, request),
                              self.loginpagename,
                              urlencode({'camefrom': camefrom}))
        request.response.redirect(url)
        return True

    def logout(self, request):
        """Performs logout by clearing session data credentials."""
        if not IHTTPRequest.providedBy(request):
            return False

        sessionData = ISession(request)[
            'zope.app.authentication.browserplugins']
        sessionData['credentials'] = None
        transaction.commit()
        return True

##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Session implementation using cookies

$Id: http.py 80044 2007-09-25 20:17:42Z rogerineichen $
"""
import hmac
import logging
import random
import re
import sha
import string
import time
from cStringIO import StringIO

import zope.location
from persistent import Persistent
from zope import schema, component
from zope.interface import implements
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.http import IHTTPApplicationRequest
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.i18nmessageid import ZopeMessageFactory as _
from zope.session.interfaces import IClientIdManager
from zope.schema.fieldproperty import FieldProperty

from zope.app.http.httpdate import build_http_date

__docformat__ = 'restructuredtext'

cookieSafeTrans = string.maketrans("+/", "-.")

logger = logging.getLogger()

def digestEncode(s):
    """Encode SHA digest for cookie."""
    return s.encode("base64")[:-2].translate(cookieSafeTrans)

class MissingClientIdException(Exception):
    """No ClientId found in Request"""

class ICookieClientIdManager(IClientIdManager):
    """Manages sessions using a cookie"""

    namespace = schema.TextLine(
            title=_('Cookie Name'),
            description=_(
                "Name of cookie used to maintain state. "
                "Must be unique to the site domain name, and only contain "
                "ASCII letters, digits and '_'"
                ),
            required=True,
            min_length=1,
            max_length=30,
            constraint=re.compile("^[\d\w_]+$").search,
            )

    cookieLifetime = schema.Int(
            title=_('Cookie Lifetime'),
            description=_(
                "Number of seconds until the browser expires the cookie. "
                "Leave blank expire the cookie when the browser is quit. "
                "Set to 0 to never expire. "
                ),
            min=0,
            required=False,
            default=None,
            missing_value=None,
            )

    thirdparty = schema.Bool(
            title=_('Third party cookie'),
            description=_(
                "Is a third party issuing the identification cookie? "
                "Servers like Apache or Nginx have capabilities to issue "
                "identification cookies too. If Third party cookies are "
                "beeing used, Zope will never send a cookie back, just check "
                "for them."
                ),
            required=False,
            default=False,
            )


class CookieClientIdManager(zope.location.Location, Persistent):
    """Session utility implemented using cookies."""

    implements(IClientIdManager, ICookieClientIdManager, IAttributeAnnotatable)

    thirdparty = FieldProperty(ICookieClientIdManager['thirdparty'])
    cookieLifetime = FieldProperty(ICookieClientIdManager['cookieLifetime'])

    def __init__(self):
        self.namespace = "zope3_cs_%x" % (int(time.time()) - 1000000000)
        self.secret = "%.20f" % random.random()

    def getClientId(self, request):
        """Get the client id

        This creates one if necessary:

          >>> from zope.publisher.http import HTTPRequest
          >>> request = HTTPRequest(StringIO(''), {}, None)
          >>> bim = CookieClientIdManager()
          >>> id = bim.getClientId(request)
          >>> id == bim.getClientId(request)
          True

        The id is retained accross requests:

          >>> request2 = HTTPRequest(StringIO(''), {}, None)
          >>> request2._cookies = dict(
          ...   [(name, cookie['value'])
          ...    for (name, cookie) in request.response._cookies.items()
          ...   ])
          >>> id == bim.getClientId(request2)
          True
          >>> bool(id)
          True

        Note that the return value of this function is a string, not
        an IClientId. This is because this method is used to implement
        the IClientId Adapter.

          >>> type(id) == type('')
          True

        It's also possible to use third-party cookies. E.g. Apache `mod_uid`
        or Nginx `ngx_http_userid_module` are able to issue user tracking
        cookies in front of Zope. In case thirdparty is activated Zope may
        not set a cookie.
        
          >>> bim.thirdparty = True
          >>> request3 = HTTPRequest(StringIO(''), {}, None)
          >>> bim.getClientId(request3)
          Traceback (most recent call last):
          ...
          MissingClientIdException          
          >>> cookie = request3.response.getCookie(bim.namespace)
          >>> cookie is None
          True
          
        """
        sid = self.getRequestId(request)
        if sid is None:
            if self.thirdparty:
                raise MissingClientIdException
            else:
                sid = self.generateUniqueId()
                
        if not self.thirdparty:
            self.setRequestId(request, sid)

        return sid

    def generateUniqueId(self):
        """Generate a new, random, unique id.

          >>> bim = CookieClientIdManager()
          >>> id1 = bim.generateUniqueId()
          >>> id2 = bim.generateUniqueId()
          >>> id1 != id2
          True

        """
        data = "%.20f%.20f%.20f" % (random.random(), time.time(), time.clock())
        digest = sha.sha(data).digest()
        s = digestEncode(digest)
        # we store a HMAC of the random value together with it, which makes
        # our session ids unforgeable.
        mac = hmac.new(s, self.secret, digestmod=sha).digest()
        return s + digestEncode(mac)

    def getRequestId(self, request):
        """Return the browser id encoded in request as a string

        Return None if an id is not set.

        For example:

          >>> from zope.publisher.http import HTTPRequest
          >>> request = HTTPRequest(StringIO(''), {}, None)
          >>> bim = CookieClientIdManager()

        Because no cookie has been set, we get no id:

          >>> bim.getRequestId(request) is None
          True

        We can set an id:

          >>> id1 = bim.generateUniqueId()
          >>> bim.setRequestId(request, id1)

        And get it back:

          >>> bim.getRequestId(request) == id1
          True

        When we set the request id, we also set a response cookie.  We
        can simulate getting this cookie back in a subsequent request:

          >>> request2 = HTTPRequest(StringIO(''), {}, None)
          >>> request2._cookies = dict(
          ...   [(name, cookie['value'])
          ...    for (name, cookie) in request.response._cookies.items()
          ...   ])

        And we get the same id back from the new request:

          >>> bim.getRequestId(request) == bim.getRequestId(request2)
          True

        If another server is managing the ClientId cookies (Apache, Nginx)
        we're returning their value without checking:
        
          >>> bim.namespace = 'uid'
          >>> bim.thirdparty = True
          >>> request3 = HTTPRequest(StringIO(''), {}, None)
          >>> request3._cookies = {'uid': 'AQAAf0Y4gjgAAAQ3AwMEAg=='}
          >>> bim.getRequestId(request3)
          'AQAAf0Y4gjgAAAQ3AwMEAg=='
          
        """
        response_cookie = request.response.getCookie(self.namespace)
        if response_cookie:
            sid = response_cookie['value']
        else:
            request = IHTTPApplicationRequest(request)
            sid = request.getCookies().get(self.namespace, None)
        if self.thirdparty:
            return sid
        else:
            # If there is an id set on the response, use that but don't trust it.
            # We need to check the response in case there has already been a new
            # session created during the course of this request.
            if sid is None or len(sid) != 54:
                return None
            s, mac = sid[:27], sid[27:]
            if (digestEncode(hmac.new(s, self.secret, digestmod=sha).digest())
                != mac):
                return None
            else:
                return sid

    def setRequestId(self, request, id):
        """Set cookie with id on request.

        This sets the response cookie:

        See the examples in getRequestId.

        Note that the id is checkec for validity. Setting an
        invalid value is silently ignored:

            >>> from zope.publisher.http import HTTPRequest
            >>> request = HTTPRequest(StringIO(''), {}, None)
            >>> bim = CookieClientIdManager()
            >>> bim.getRequestId(request)
            >>> bim.setRequestId(request, 'invalid id')
            >>> bim.getRequestId(request)

        For now, the cookie path is the application URL:

            >>> cookie = request.response.getCookie(bim.namespace)
            >>> cookie['path'] == request.getApplicationURL(path_only=True)
            True

        In the future, it should be the site containing the
        CookieClientIdManager

        By default, session cookies don't expire:

            >>> cookie.has_key('expires')
            False

        Expiry time of 0 means never (well - close enough)

            >>> bim.cookieLifetime = 0
            >>> request = HTTPRequest(StringIO(''), {}, None)
            >>> bid = bim.getClientId(request)
            >>> cookie = request.response.getCookie(bim.namespace)
            >>> cookie['expires']
            'Tue, 19 Jan 2038 00:00:00 GMT'

        A non-zero value means to expire after than number of seconds:

            >>> bim.cookieLifetime = 3600
            >>> request = HTTPRequest(StringIO(''), {}, None)
            >>> bid = bim.getClientId(request)
            >>> cookie = request.response.getCookie(bim.namespace)
            >>> import rfc822
            >>> expires = time.mktime(rfc822.parsedate(cookie['expires']))
            >>> expires > time.mktime(time.gmtime()) + 55*60
            True
                        
        If another server in front of Zope (Apache, Nginx) is managing the
        cookies we won't set any ClientId cookies:
        
          >>> request = HTTPRequest(StringIO(''), {}, None)
          >>> bim.thirdparty = True
          >>> bim.setRequestId(request, '1234')
          >>> cookie = request.response.getCookie(bim.namespace)
          >>> cookie
        """
        # TODO: Currently, the path is the ApplicationURL. This is reasonable,
        #     and will be adequate for most purposes.
        #     A better path to use would be that of the folder that contains
        #     the site manager this service is registered within. However,
        #     that would be expensive to look up on each request, and would
        #     have to be altered to take virtual hosting into account.
        #     Seeing as this utility instance has a unique namespace for its
        #     cookie, using ApplicationURL shouldn't be a problem.

        if self.thirdparty:
            logger.warning('ClientIdManager is using thirdparty cookies, '
                'ignoring setIdRequest call')            
        else:
            if self.cookieLifetime is not None:
                if self.cookieLifetime:
                    expires = build_http_date(time.time() + self.cookieLifetime)
                else:
                    expires = 'Tue, 19 Jan 2038 00:00:00 GMT'
                request.response.setCookie(
                        self.namespace, id, expires=expires,
                        path=request.getApplicationURL(path_only=True)
                        )
            else:
                request.response.setCookie(
                        self.namespace, id,
                        path=request.getApplicationURL(path_only=True)
                        )

def notifyVirtualHostChanged(event):
    """Adjust cookie paths when IVirtualHostRequest information changes.
    
    Given a event, this method should call a CookieClientIdManager's 
    setRequestId if a cookie is present in the response for that manager. To
    demonstrate we create a dummy manager object and event:
    
        >>> class DummyManager(object):
        ...     implements(ICookieClientIdManager)
        ...     namespace = 'foo'
        ...     thirdparty = False
        ...     request_id = None
        ...     def setRequestId(self, request, id):
        ...         self.request_id = id
        ...
        >>> manager = DummyManager()
        >>> component.provideUtility(manager, IClientIdManager)
        >>> from zope.publisher.http import HTTPRequest
        >>> class DummyEvent (object):
        ...     request = HTTPRequest(StringIO(''), {}, None)
        >>> event = DummyEvent()
        
    With no cookies present, the manager should not be called:
    
        >>> notifyVirtualHostChanged(event)
        >>> manager.request_id is None
        True
        
    However, when a cookie *has* been set, the manager is called so it can
    update the cookie if need be:
    
        >>> event.request.response.setCookie('foo', 'bar')
        >>> notifyVirtualHostChanged(event)
        >>> manager.request_id
        'bar'
    
    If a server in front of Zope manages the ClientIds (Apache, Nginx), we
    don't need to take care about the cookies

        >>> manager2 = DummyManager()
        >>> manager2.thirdparty = True
        >>> event2 = DummyEvent()
        
    However, when a cookie *has* been set, the manager is called so it can
    update the cookie if need be:
    
        >>> event2.request.response.setCookie('foo2', 'bar2')
        >>> notifyVirtualHostChanged(event2)
        >>> id = manager2.request_id
        >>> id is None
        True

    Cleanup of the utility registration:
    
        >>> import zope.component.testing
        >>> zope.component.testing.tearDown()
        
    """
    # the event sends us a IHTTPApplicationRequest, but we need a
    # IHTTPRequest for the response attribute, and so does the cookie-
    # manager.
    request = IHTTPRequest(event.request, None)
    if event.request is None:
        return 
    for name, manager in component.getUtilitiesFor(IClientIdManager):
        if manager and ICookieClientIdManager.providedBy(manager):
            # Third party ClientId Managers need no modification at all 
            if not manager.thirdparty:
                cookie = request.response.getCookie(manager.namespace)
                if cookie:
                    manager.setRequestId(request, cookie['value'])
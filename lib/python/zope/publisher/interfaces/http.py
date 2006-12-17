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
"""HTTP-related publisher interfaces.

$Id: http.py 69340 2006-08-02 14:16:04Z mj $
"""

__docformat__ = "reStructuredText"

from zope.interface import Interface
from zope.interface import Attribute

from zope.publisher.interfaces import IApplicationRequest
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import IRequest
from zope.publisher.interfaces import IResponse


class IVirtualHostRequest(Interface):
    """The support for virtual hosts in Zope is very important.

    In order to make virtual hosts working, we need to support several
    methods in our Request object. This interface defines the required
    methods.
    """

    def setVirtualHostRoot(names):
        """Marks the currently traversed object as the root of a virtual host.

        Any path elements traversed up to that

        Set the names which compose the application path.
        These are the path elements that appear in the beginning of
        the generated URLs.

        Should be called during traversal.
        """

    def getVirtualHostRoot():
        """Returns the object which is the virtual host root for this request

        Return None if setVirtualHostRoot hasn't been called.
        """

    def setApplicationServer(host, proto='http', port=None):
        """Override the host, protocol and port parts of generated URLs.

        This affects automatically inserted <base> tags and URL getters
        in the request, but not things like @@absolute_url views.
        """

    def shiftNameToApplication():
        """Add the name being traversed to the application name

        This is only allowed in the case where the name is the first name.

        A Value error is raised if the shift can't be performed.
        """


class IHTTPApplicationRequest(IApplicationRequest, IVirtualHostRequest):
    """HTTP request data.

    This object provides access to request data.  This includes, the
    input headers, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into four categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
        in the <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
        specification</a>

      - Cookies

        These are the cookie data, if present.

      - Other

        Data that may be set by an application object.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, cookies, and special.
    """

    def __getitem__(key):
        """Return HTTP request data

        Request data sre retrieved from one of:

        - Environment variables

          These variables include input headers, server data, and other
          request-related data.  The variable names are as <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
          in the <a
          href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
          specification</a>

        - Cookies

          These are the cookie data, if present.

        Cookies are searched before environmental data.
        """

    def getCookies():
        """Return the cookie data

        Data are returned as a mapping object, mapping cookie name to value.
        """
        return IMapping(str, str)

    cookies = Attribute(
        """Request cookie data

        This is a read-only mapping from variable name to value.
        """)

    def getHeader(name, default=None, literal=False):
        """Get a header value

        Return the named HTTP header, or an optional default
        argument or None if the header is not found. Note that
        both original and CGI-ified header names are recognized,
        e.g. 'Content-Type', 'CONTENT_TYPE' and 'HTTP_CONTENT_TYPE'
        should all return the Content-Type header, if available.

        If the literal argument is passed, the header is searched
        'as is', eg: only if the case matches.
        """

    headers = Attribute(
        """Request header data

        This is a read-only mapping from variable name to value.
        It does *not* support iteration.
        """)

    URL = Attribute(
        """Request URL data

        When converted to a string, this gives the effective published URL.

        This object can also be used as a mapping object. The key must
        be an integer or a string that can be converted to an
        integer. A non-negative integer returns a URL n steps from the
        URL of the top-level application objects. A negative integer
        gives a URL that is -n steps back from the effective URL.

        For example, 'request.URL[-2]' is equivalent to the Zope 2
        'request["URL2"]'. The notion is that this would be used in
        path expressions, like 'request/URL/-2'.
        """)


    def getURL(level=0, path_only=False):
        """Return the published URL with level names removed from the end.

        If path_only is true, then only a path will be returned.
        """

    def getApplicationURL(depth=0, path_only=False):
        """Return the application URL plus depth steps

        If path_only is true, then only a path will be returned.
        """


class IHTTPPublisher(IPublishTraverse):
    """HTTP Publisher"""


class IHTTPRequest(IRequest):

    method = Attribute("Request method, normalized to upper case")

    def setPathSuffix(steps):
        """Add additional traversal steps to be taken after all other traversal

        This is used to handle HTTP request methods (except for GET
        and POST in the case of browser requests) and XML-RPC methods.
        """

    locale = Attribute(
        "Return the locale object associated with this request.")

    def setupLocale():
        """Setup the locale object based on languages returned by
        IUserPreferredLanguages adapter.
        """


class IHTTPCredentials(Interface):

    # TODO: Eventially this will be a different method
    def _authUserPW():
        """Return (login, password) if there are basic credentials;
        return None if there aren't."""

    def unauthorized(challenge):
        """Issue a 401 Unauthorized error (asking for login/password).
        The challenge is the value of the WWW-Authenticate header."""


class IHTTPApplicationResponse(Interface):
    """HTTP Response
    """

    def redirect(location, status=302):
        """Causes a redirection without raising an error.
        """

class IHeaderOutput(Interface):
    """Interface for setting HTTP response headers.

    This allows the HTTP server and the application to both set response
    headers.

    zope.publisher.http.HTTPResponse is optionally passed an
    object which implements this interface in order to intermingle
    its headers with the HTTP server's response headers,
    and for the purpose of better logging.
    """

    def setResponseStatus(status, reason):
        """Sets the status code and the accompanying message.
        """

    def setResponseHeaders(mapping):
        """Sets headers.  The headers must be Correctly-Cased.
        """

    def appendResponseHeaders(lst):
        """Sets headers that can potentially repeat.

        Takes a list of strings.
        """

    def wroteResponseHeader():
        """Returns a flag indicating whether the response

        header has already been sent.
        """

    def setAuthUserName(name):
        """Sets the name of the authenticated user so the name can be logged.
        """


class IHTTPResponse(IResponse):
    """An object representation of an HTTP response.

    The Response type encapsulates all possible responses to HTTP
    requests.  Responses are normally created by the object publisher.
    A published object may recieve the response object as an argument
    named 'RESPONSE'.  A published object may also create its own
    response object.  Normally, published objects use response objects
    to:

    - Provide specific control over output headers,

    - Set cookies, or

    - Provide stream-oriented output.

    If stream oriented output is used, then the response object
    passed into the object must be used.
    """

    authUser = Attribute('The authenticated user message.')

    def getStatus():
        """Returns the current HTTP status code as an integer.
        """

    def setStatus(status, reason=None):
        """Sets the HTTP status code of the response

        The argument may either be an integer or a string from { OK,
        Created, Accepted, NoContent, MovedPermanently,
        MovedTemporarily, NotModified, BadRequest, Unauthorized,
        Forbidden, NotFound, InternalError, NotImplemented,
        BadGateway, ServiceUnavailable } that will be converted to the
        correct integer value.
        """

    def getStatusString():
        """Return the status followed by the reason."""

    def setHeader(name, value, literal=False):
        """Sets an HTTP return header "name" with value "value"

        The previous value is cleared. If the literal flag is true,
        the case of the header name is preserved, otherwise
        word-capitalization will be performed on the header name on
        output.
        """

    def addHeader(name, value):
        """Add an HTTP Header

        Sets a new HTTP return header with the given value, while retaining
        any previously set headers with the same name.
        """

    def getHeader(name, default=None):
        """Gets a header value

        Returns the value associated with a HTTP return header, or
        'default' if no such header has been set in the response
        yet.
        """

    def getHeaders():
        """Returns a list of header name, value tuples.
        """

    def appendToCookie(name, value):
        """Append text to a cookie value

        If a value for the cookie has previously been set, the new
        value is appended to the old one separated by a colon.
        """

    def expireCookie(name, **kw):
        """Causes an HTTP cookie to be removed from the browser

        The response will include an HTTP header that will remove the cookie
        corresponding to "name" on the client, if one exists. This is
        accomplished by sending a new cookie with an expiration date
        that has already passed. Note that some clients require a path
        to be specified - this path must exactly match the path given
        when creating the cookie. The path can be specified as a keyword
        argument.
        If the value of a keyword argument is None, it will be ignored.
        """

    def setCookie(name, value, **kw):
        """Sets an HTTP cookie on the browser

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.
        If the value of a keyword argument is None, it will be ignored.
        """

    def getCookie(name, default=None):
        """Gets HTTP cookie data as a dict

        Returns the dict of values associated with an HTTP cookie set in the
        response, or 'default' if no such cookie has been set in the response
        yet.
        """

    def setResult(result):
        """Sets the response result value to a string or a file.
        """

    def consumeBody():
        """Returns the response body as a string.

        Note that this function can be only requested once, since it is
        constructed from the result.
        """

    def consumeBodyIter():
        """Returns the response body as an iterable.

        Note that this function can be only requested once, since it is
        constructed from the result.
        """
        
class IHTTPVirtualHostChangedEvent(Interface):
    """The host, port and/or the application path have changed.
    
    The request referred to in this event implements at least the 
    IHTTPAppliationRequest interface.
    """
    request = Attribute(u'The application request whose virtual host info has '
                        u'been altered')

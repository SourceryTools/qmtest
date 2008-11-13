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
"""HTTP Publisher

$Id: http.py 89074 2008-07-31 07:29:29Z andreasjung $
"""
import re, time, random
from cStringIO import StringIO
from urllib import quote, unquote, splitport
from types import StringTypes, ClassType
from cgi import escape
from Cookie import SimpleCookie
from Cookie import CookieError
import logging
from tempfile import TemporaryFile

from zope import component, interface, event
from zope.deprecation import deprecation

from zope.publisher import contenttype
from zope.publisher.interfaces.http import IHTTPCredentials
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.http import IHTTPApplicationRequest
from zope.publisher.interfaces.http import IHTTPPublisher
from zope.publisher.interfaces.http import IHTTPVirtualHostChangedEvent
from zope.publisher.interfaces.http import IResult

from zope.publisher.interfaces import Redirect
from zope.publisher.interfaces.http import IHTTPResponse
from zope.publisher.interfaces.http import IHTTPApplicationResponse
from zope.publisher.interfaces.logginginfo import ILoggingInfo
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError

from zope.publisher import contenttype
from zope.publisher.base import BaseRequest, BaseResponse
from zope.publisher.base import RequestDataProperty, RequestDataMapper
from zope.publisher.base import RequestDataGetter


# Default Encoding
ENCODING = 'UTF-8'

eventlog = logging.getLogger('eventlog')

class CookieMapper(RequestDataMapper):
    _mapname = '_cookies'

class HeaderGetter(RequestDataGetter):
    _gettrname = 'getHeader'

def sane_environment(env):
    # return an environment mapping which has been cleaned of
    # funny business such as REDIRECT_ prefixes added by Apache
    # or HTTP_CGI_AUTHORIZATION hacks.
    # It also makes sure PATH_INFO is a unicode string.
    dict = {}
    for key, val in env.items():
        while key.startswith('REDIRECT_'):
            key = key[9:]
        dict[key] = val
    if 'HTTP_CGI_AUTHORIZATION' in dict:
        dict['HTTP_AUTHORIZATION'] = dict.pop('HTTP_CGI_AUTHORIZATION')
    if 'PATH_INFO' in dict:
        dict['PATH_INFO'] = dict['PATH_INFO'].decode('utf-8')
    return dict

class HTTPVirtualHostChangedEvent(object):
    interface.implements(IHTTPVirtualHostChangedEvent)

    request = None

    def __init__(self, request):
        self.request = request

# Possible HTTP status responses
status_reasons = {
100: 'Continue',
101: 'Switching Protocols',
102: 'Processing',
200: 'Ok',
201: 'Created',
202: 'Accepted',
203: 'Non-Authoritative Information',
204: 'No Content',
205: 'Reset Content',
206: 'Partial Content',
207: 'Multi-Status',
300: 'Multiple Choices',
301: 'Moved Permanently',
302: 'Moved Temporarily',
303: 'See Other',
304: 'Not Modified',
305: 'Use Proxy',
307: 'Temporary Redirect',
400: 'Bad Request',
401: 'Unauthorized',
402: 'Payment Required',
403: 'Forbidden',
404: 'Not Found',
405: 'Method Not Allowed',
406: 'Not Acceptable',
407: 'Proxy Authentication Required',
408: 'Request Time-out',
409: 'Conflict',
410: 'Gone',
411: 'Length Required',
412: 'Precondition Failed',
413: 'Request Entity Too Large',
414: 'Request-URI Too Large',
415: 'Unsupported Media Type',
416: 'Requested range not satisfiable',
417: 'Expectation Failed',
422: 'Unprocessable Entity',
423: 'Locked',
424: 'Failed Dependency',
500: 'Internal Server Error',
501: 'Not Implemented',
502: 'Bad Gateway',
503: 'Service Unavailable',
504: 'Gateway Time-out',
505: 'HTTP Version not supported',
507: 'Insufficient Storage',
}

status_codes={}

def init_status_codes():
    # Add mappings for builtin exceptions and
    # provide text -> error code lookups.
    for key, val in status_reasons.items():
        status_codes[val.replace(' ', '').lower()] = key
        status_codes[val.lower()] = key
        status_codes[key] = key
        status_codes[str(key)] = key

    en = [n.lower() for n in dir(__builtins__) if n.endswith('Error')]

    for name in en:
        status_codes[name] = 500

init_status_codes()


class URLGetter(object):

    __slots__ = "__request"

    def __init__(self, request):
        self.__request = request

    def __str__(self):
        return self.__request.getURL()

    def __getitem__(self, name):
        url = self.get(name, None)
        if url is None:
            raise KeyError(name)
        return url

    def get(self, name, default=None):
        i = int(name)
        try:
            if i < 0:
                i = -i
                return self.__request.getURL(i)
            else:
                return self.__request.getApplicationURL(i)
        except IndexError, v:
            if v[0] == i:
                return default
            raise

class HTTPInputStream(object):
    """Special stream that supports caching the read data.

    This is important, so that we can retry requests.
    """

    def __init__(self, stream, environment):
        self.stream = stream
        size = environment.get('CONTENT_LENGTH')
        # There can be no size in the environment (None) or the size
        # can be an empty string, in which case we treat it as absent.
        if not size:
            size = environment.get('HTTP_CONTENT_LENGTH')
        if not size or int(size) < 65536:
            self.cacheStream = StringIO()
        else:
            self.cacheStream = TemporaryFile()

    def getCacheStream(self):
        self.read()
        self.cacheStream.seek(0)
        return self.cacheStream

    def read(self, size=-1):
        data = self.stream.read(size)
        self.cacheStream.write(data)
        return data

    def readline(self, size=None):
        # XXX We should pass the ``size`` argument to self.stream.readline
        # but twisted.web2.wsgi.InputStream.readline() doesn't accept it.
        # See http://www.zope.org/Collectors/Zope3-dev/535 and
        #     http://twistedmatrix.com/trac/ticket/1451
        data = self.stream.readline()
        self.cacheStream.write(data)
        return data

    def readlines(self, hint=0):
        data = self.stream.readlines(hint)
        self.cacheStream.write(''.join(data))
        return data
        

DEFAULT_PORTS = {'http': '80', 'https': '443'}
STAGGER_RETRIES = True

class HTTPRequest(BaseRequest):
    """Model HTTP request data.

    This object provides access to request data.  This includes, the
    input headers, form data, server data, and cookies.

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

      - Form data

        These are data extracted from either a URL-encoded query
        string or body, if present.

      - Cookies

        These are the cookie data, if present.

      - Other

        Data that may be set by an application object.

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.
    """
    interface.implements(IHTTPCredentials,
                         IHTTPRequest,
                         IHTTPApplicationRequest)

    __slots__ = (
        '__provides__',   # Allow request to directly provide interfaces
        '_auth',          # The value of the HTTP_AUTHORIZATION header.
        '_cookies',       # The request cookies
        '_path_suffix',   # Extra traversal steps after normal traversal
        '_retry_count',   # How many times the request has been retried
        '_app_names',     # The application path as a sequence
        '_app_server',    # The server path of the application url
        '_orig_env',      # The original environment
        '_endswithslash', # Does the given path end with /
        'method',         # The upper-cased request method (REQUEST_METHOD)
        '_locale',        # The locale for the request
        '_vh_root',       # Object at the root of the virtual host
        )

    retry_max_count = 3    # How many times we're willing to retry

    def __init__(self, body_instream, environ, response=None):

        super(HTTPRequest, self).__init__(
            HTTPInputStream(body_instream, environ), environ, response)

        self._orig_env = environ
        environ = sane_environment(environ)

        if 'HTTP_AUTHORIZATION' in environ:
            self._auth = environ['HTTP_AUTHORIZATION']
            del environ['HTTP_AUTHORIZATION']
        else:
            self._auth = None

        self.method = environ.get("REQUEST_METHOD", 'GET').upper()

        self._environ = environ

        self.__setupCookies()
        self.__setupPath()
        self.__setupURLBase()
        self._vh_root = None
        self.setupLocale()

    def setupLocale(self):
        envadapter = IUserPreferredLanguages(self, None)
        if envadapter is None:
            self._locale = None
            return

        langs = envadapter.getPreferredLanguages()
        for httplang in langs:
            parts = (httplang.split('-') + [None, None])[:3]
            try:
                self._locale = locales.getLocale(*parts)
                return
            except LoadLocaleError:
                # Just try the next combination
                pass
        else:
            # No combination gave us an existing locale, so use the default,
            # which is guaranteed to exist
            self._locale = locales.getLocale(None, None, None)

    def _getLocale(self):
        return self._locale
    locale = property(_getLocale)

    def __setupURLBase(self):
        get_env = self._environ.get
        # Get base info first. This isn't likely to cause
        # errors and might be useful to error handlers.
        script = get_env('SCRIPT_NAME', '').strip()

        # _script and the other _names are meant for URL construction
        self._app_names = filter(None, script.split('/'))

        # get server URL and store it too, since we are already looking it up
        server_url = get_env('SERVER_URL', None)
        if server_url is not None:
            self._app_server = server_url = server_url.strip()
        else:
            server_url = self.__deduceServerURL()

        if server_url.endswith('/'):
            server_url = server_url[:-1]

        # strip off leading /'s of script
        while script.startswith('/'):
            script = script[1:]

        self._app_server = server_url

    def __deduceServerURL(self):
        environ = self._environ

        if (environ.get('HTTPS', '').lower() == "on" or
            environ.get('SERVER_PORT_SECURE') == "1"):
            protocol = 'https'
        else:
            protocol = 'http'

        if environ.has_key('HTTP_HOST'):
            host = environ['HTTP_HOST'].strip()
            hostname, port = splitport(host)
        else:
            hostname = environ.get('SERVER_NAME', '').strip()
            port = environ.get('SERVER_PORT', '')

        if port and port != DEFAULT_PORTS.get(protocol):
            host = hostname + ':' + port
        else:
            host = hostname

        return '%s://%s' % (protocol, host)

    def _parseCookies(self, text, result=None):
        """Parse 'text' and return found cookies as 'result' dictionary."""

        if result is None:
            result = {}

        # ignore cookies on a CookieError
        try:
            c = SimpleCookie(text)
        except CookieError, e:
            eventlog.warn(e)
            return result

        for k,v in c.items():
            result[unicode(k, ENCODING)] = unicode(v.value, ENCODING)

        return result

    def __setupCookies(self):
        # Cookie values should *not* be appended to existing form
        # vars with the same name - they are more like default values
        # for names not otherwise specified in the form.
        self._cookies = {}
        cookie_header = self._environ.get('HTTP_COOKIE', None)
        if cookie_header is not None:
            self._parseCookies(cookie_header, self._cookies)

    def __setupPath(self):
        # PATH_INFO is unicode here, so setupPath_helper sets up the
        # traversal stack correctly.
        self._setupPath_helper("PATH_INFO")

    def supportsRetry(self):
        'See IPublisherRequest'
        count = getattr(self, '_retry_count', 0)
        if count < self.retry_max_count:
            if STAGGER_RETRIES:
                time.sleep(random.uniform(0, 2**(count)))
            return True

    def retry(self):
        'See IPublisherRequest'
        count = getattr(self, '_retry_count', 0)
        self._retry_count = count + 1

        new_response = self.response.retry()
        request = self.__class__(
            # Use the cache stream as the new input stream.
            body_instream=self._body_instream.getCacheStream(),
            environ=self._orig_env,
            response=new_response,
            )
        request.setPublication(self.publication)
        request._retry_count = self._retry_count
        return request

    def traverse(self, obj):
        'See IPublisherRequest'

        ob = super(HTTPRequest, self).traverse(obj)
        if self._path_suffix:
            self._traversal_stack = self._path_suffix
            ob = super(HTTPRequest, self).traverse(ob)

        return ob

    def getHeader(self, name, default=None, literal=False):
        'See IHTTPRequest'
        environ = self._environ
        if not literal:
            name = name.replace('-', '_').upper()
        val = environ.get(name, None)
        if val is not None:
            return val
        if not name.startswith('HTTP_'):
            name='HTTP_%s' % name
        return environ.get(name, default)

    headers = RequestDataProperty(HeaderGetter)

    def getCookies(self):
        'See IHTTPApplicationRequest'
        return self._cookies

    cookies = RequestDataProperty(CookieMapper)

    def setPathSuffix(self, steps):
        'See IHTTPRequest'
        steps = list(steps)
        steps.reverse()
        self._path_suffix = steps

    def _authUserPW(self):
        'See IHTTPCredentials'
        if self._auth and self._auth.lower().startswith('basic '):
            encoded = self._auth.split(None, 1)[-1]
            name, password = encoded.decode("base64").split(':', 1)
            return name, password

    def unauthorized(self, challenge):
        'See IHTTPCredentials'
        self._response.setHeader("WWW-Authenticate", challenge, True)
        self._response.setStatus(401)

    def setPrincipal(self, principal):
        'See IPublicationRequest'
        super(HTTPRequest, self).setPrincipal(principal)
        logging_info = ILoggingInfo(principal, None)
        if logging_info is None:
            message = '-'
        else:
            message = logging_info.getLogMessage()
        self.response.authUser = message

    def _createResponse(self):
        # Should be overridden by subclasses
        return HTTPResponse()


    def getURL(self, level=0, path_only=False):
        names = self._app_names + self._traversed_names
        if level:
            if level > len(names):
                raise IndexError(level)
            names = names[:-level]
        # See: http://www.ietf.org/rfc/rfc2718.txt, Section 2.2.5
        names = [quote(name.encode("utf-8"), safe='/+@') for name in names]

        if path_only:
            if not names:
                return '/'
            return '/' + '/'.join(names)
        else:
            if not names:
                return self._app_server
            return "%s/%s" % (self._app_server, '/'.join(names))

    def getApplicationURL(self, depth=0, path_only=False):
        """See IHTTPApplicationRequest"""
        if depth:
            names = self._traversed_names
            if depth > len(names):
                raise IndexError(depth)
            names = self._app_names + names[:depth]
        else:
            names = self._app_names

        # See: http://www.ietf.org/rfc/rfc2718.txt, Section 2.2.5
        names = [quote(name.encode("utf-8"), safe='/+@') for name in names]

        if path_only:
            return names and ('/' + '/'.join(names)) or '/'
        else:
            return (names and ("%s/%s" % (self._app_server, '/'.join(names)))
                    or self._app_server)

    def setApplicationServer(self, host, proto='http', port=None):
        if port and str(port) != DEFAULT_PORTS.get(proto):
            host = '%s:%s' % (host, port)
        self._app_server = '%s://%s' % (proto, host)
        event.notify(HTTPVirtualHostChangedEvent(self))

    def shiftNameToApplication(self):
        """Add the name being traversed to the application name

        This is only allowed in the case where the name is the first name.

        A Value error is raise if the shift can't be performed.
        """
        if len(self._traversed_names) == 1:
            self._app_names.append(self._traversed_names.pop())
            event.notify(HTTPVirtualHostChangedEvent(self))
            return

        raise ValueError("Can only shift leading traversal "
                         "names to application names")

    def setVirtualHostRoot(self, names=()):
        del self._traversed_names[:]
        self._vh_root = self._last_obj_traversed
        self._app_names = list(names)
        event.notify(HTTPVirtualHostChangedEvent(self))

    def getVirtualHostRoot(self):
        return self._vh_root

    URL = RequestDataProperty(URLGetter)

    def __repr__(self):
        # Returns a *short* string.
        return '<%s.%s instance URL=%s>' % (
            self.__class__.__module__, self.__class__.__name__, str(self.URL))

    def get(self, key, default=None):
        'See Interface.Common.Mapping.IReadMapping'
        marker = object()
        result = self._cookies.get(key, marker)
        if result is not marker:
            return result

        return super(HTTPRequest, self).get(key, default)

    def keys(self):
        'See Interface.Common.Mapping.IEnumerableMapping'
        d = {}
        d.update(self._environ)
        d.update(self._cookies)
        return d.keys()



class HTTPResponse(BaseResponse):
    interface.implements(IHTTPResponse, IHTTPApplicationResponse)

    __slots__ = (
        'authUser',             # Authenticated user string
        # BBB: Remove for Zope 3.4.
        '_header_output',       # Hook object to collaborate with a server
                                # for header generation.
        '_headers',
        '_cookies',
        '_status',              # The response status (usually an integer)
        '_reason',              # The reason that goes with the status
        '_status_set',          # Boolean: status explicitly set
        '_charset',             # String: character set for the output
        )


    def __init__(self):
        super(HTTPResponse, self).__init__()
        self.reset()


    def reset(self):
        'See IResponse'
        super(HTTPResponse, self).reset()
        self._headers = {}
        self._cookies = {}
        self._status = 599
        self._reason = 'No status set'
        self._status_set = False
        self._charset = None
        self.authUser = '-'

    def setStatus(self, status, reason=None):
        'See IHTTPResponse'
        if status is None:
            status = 200
        else:
            if type(status) in StringTypes:
                status = status.lower()
            status = status_codes.get(status, 500)
        self._status = status

        if reason is None:
            reason = status_reasons.get(status, "Unknown")

        self._reason = reason
        self._status_set = True


    def getStatus(self):
        'See IHTTPResponse'
        return self._status

    def getStatusString(self):
        'See IHTTPResponse'
        return '%i %s' % (self._status, self._reason)

    def setHeader(self, name, value, literal=False):
        'See IHTTPResponse'
        name = str(name)
        value = str(value)

        if not literal:
            name = name.lower()

        self._headers[name] = [value]


    def addHeader(self, name, value):
        'See IHTTPResponse'
        values = self._headers.setdefault(name, [])
        values.append(value)


    def getHeader(self, name, default=None, literal=False):
        'See IHTTPResponse'
        key = name.lower()
        name = literal and name or key
        result = self._headers.get(name)
        if result:
            return result[0]
        return default


    def getHeaders(self):
        'See IHTTPResponse'
        result = []
        headers = self._headers

        result.append(
            ("X-Powered-By", "Zope (www.zope.org), Python (www.python.org)"))

        for key, values in headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = '-'.join([k.capitalize() for k in key.split('-')])
            result.extend([(key, val) for val in values])

        result.extend([tuple(cookie.split(': ', 1))
                       for cookie in self._cookie_list()])

        return result


    def appendToCookie(self, name, value):
        'See IHTTPResponse'
        cookies = self._cookies
        if name in cookies:
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        if 'value' in cookie:
            cookie['value'] = '%s:%s' % (cookie['value'], value)
        else:
            cookie['value'] = value


    def expireCookie(self, name, **kw):
        'See IHTTPResponse'
        dict = {'max_age':0, 'expires':'Wed, 31-Dec-97 23:59:59 GMT'}
        for k, v in kw.items():
            if v is not None:
                dict[k] = v
        cookies = self._cookies
        if name in cookies:
            # Cancel previous setCookie().
            del cookies[name]
        self.setCookie(name, 'deleted', **dict)


    def setCookie(self, name, value, **kw):
        'See IHTTPResponse'
        cookies = self._cookies
        cookie = cookies.setdefault(name, {})

        for k, v in kw.items():
            if v is not None:
                cookie[k.lower()] = v

        cookie['value'] = value


    def getCookie(self, name, default=None):
        'See IHTTPResponse'
        return self._cookies.get(name, default)


    def setResult(self, result):
        'See IHTTPResponse'
        if IResult.providedBy(result):
            r = result
        else:
            r = component.queryMultiAdapter((result, self._request), IResult)
            if r is None:
                if isinstance(result, basestring):
                    r = result
                elif result is None:
                    r = ''
                else:
                    raise TypeError(
                        'The result should be None, a string, or adaptable to '
                        'IResult.')
            if isinstance(r, basestring):
                r, headers = self._implicitResult(r)
                self._headers.update(dict((k, [v]) for (k, v) in headers))
                r = (r,) # chunking should be much larger than per character

        self._result = r
        if not self._status_set:
            self.setStatus(200)


    def consumeBody(self):
        'See IHTTPResponse'
        return ''.join(self._result)


    def consumeBodyIter(self):
        'See IHTTPResponse'
        return self._result


    def _implicitResult(self, body):
        encoding = getCharsetUsingRequest(self._request) or 'utf-8'
        content_type = self.getHeader('content-type')

        if isinstance(body, unicode):
            try:
                if not content_type.startswith('text/'):
                    raise ValueError(
                        'Unicode results must have a text content type.')
            except AttributeError:
                    raise ValueError(
                        'Unicode results must have a text content type.')


            major, minor, params = contenttype.parse(content_type)

            if 'charset' in params:
                encoding = params['charset']
            else:
                content_type += ';charset=%s' %encoding

            body = body.encode(encoding)

        if content_type:
            headers = [('content-type', content_type),
                       ('content-length', str(len(body)))]
        else:
            headers = [('content-length', str(len(body)))]

        return body, headers


    def handleException(self, exc_info):
        """
        Calls self.setBody() with an error response.
        """
        t, v = exc_info[:2]
        if isinstance(t, (ClassType, type)):    
            if issubclass(t, Redirect):
                self.redirect(v.getLocation())
                return
            title = tname = t.__name__
        else:
            title = tname = unicode(t)

        # Throwing non-protocol-specific exceptions is a good way
        # for apps to control the status code.
        self.setStatus(tname)

        body = self._html(title, "A server error occurred." )
        self.setHeader("Content-Type", "text/html")
        self.setResult(body)

    def internalError(self):
        'See IPublisherResponse'
        self.setStatus(500, u"The engines can't take any more, Jim!")

    def _html(self, title, content):
        t = escape(title)
        return (
            u"<html><head><title>%s</title></head>\n"
            u"<body><h2>%s</h2>\n"
            u"%s\n"
            u"</body></html>\n" %
            (t, t, content)
            )

    def retry(self):
        """
        Returns a response object to be used in a retry attempt
        """
        return self.__class__()

    def redirect(self, location, status=None):
        """Causes a redirection without raising an error"""
        if status is None:
            # parse the HTTP version and set default accordingly
            if (self._request.get("SERVER_PROTOCOL","HTTP/1.0") <
                "HTTP/1.1"):
                status=302
            else:
                status=303

        self.setStatus(status)
        self.setHeader('Location', location)
        self.setResult(DirectResult(()))
        return location

    def _cookie_list(self):
        try:
            c = SimpleCookie()
        except CookieError, e:
            eventlog.warn(e)
            return []
        for name, attrs in self._cookies.items():
            name = str(name)
            c[name] = attrs['value'].encode(ENCODING)
            for k,v in attrs.items():
                if k == 'value':
                    continue
                if k == 'secure':
                    if v:
                        c[name]['secure'] = True
                    continue
                if k == 'max_age':
                    k = 'max-age'
                elif k == 'comment':
                    # Encode rather than throw an exception
                    v = quote(v.encode('utf-8'), safe="/?:@&+")
                c[name][k] = str(v)
        return str(c).splitlines()

    def write(*_):
        raise TypeError(
            "The HTTP response write method is no longer supported. "
            "See the file httpresults.txt in the zope.publisher package "
            "for more information."
            )

def sort_charsets(x, y):
    if y[1] == 'utf-8':
        return 1
    if x[1] == 'utf-8':
        return -1
    return cmp(y, x)


class HTTPCharsets(object):
    component.adapts(IHTTPRequest)
    interface.implements(IUserPreferredCharsets)

    def __init__(self, request):
        self.request = request

    def getPreferredCharsets(self):
        '''See interface IUserPreferredCharsets'''
        charsets = []
        sawstar = sawiso88591 = 0
        header_present = bool(self.request.get('HTTP_ACCEPT_CHARSET'))
        for charset in self.request.get('HTTP_ACCEPT_CHARSET', '').split(','):
            charset = charset.strip().lower()
            if charset:
                if ';' in charset:
                    try:
                        charset, quality = charset.split(';')
                    except ValueError:
                        continue
                    if not quality.startswith('q='):
                        # not a quality parameter
                        quality = 1.0
                    else:
                        try:
                            quality = float(quality[2:])
                        except ValueError:
                            continue
                else:
                    quality = 1.0
                if quality == 0.0:
                    continue
                if charset == '*':
                    sawstar = 1
                if charset == 'iso-8859-1':
                    sawiso88591 = 1
                charsets.append((quality, charset))
        # Quoting RFC 2616, $14.2: If no "*" is present in an Accept-Charset
        # field, then all character sets not explicitly mentioned get a
        # quality value of 0, except for ISO-8859-1, which gets a quality
        # value of 1 if not explicitly mentioned.
        # And quoting RFC 2616, $14.2: "If no Accept-Charset header is
        # present, the default is that any character set is acceptable."
        if not sawstar and not sawiso88591 and header_present:
            charsets.append((1.0, 'iso-8859-1'))
        # UTF-8 is **always** preferred over anything else.
        # Reason: UTF-8 is not specific and can encode the entire unicode
        # range , unlike many other encodings. Since Zope can easily use very
        # different ranges, like providing a French-Chinese dictionary, it is
        # always good to use UTF-8.
        charsets.sort(sort_charsets)
        charsets = [charset for quality, charset in charsets]
        if sawstar and 'utf-8' not in charsets:
            charsets.insert(0, 'utf-8')
        return charsets


def getCharsetUsingRequest(request):
    'See IHTTPResponse'
    envadapter = IUserPreferredCharsets(request, None)
    if envadapter is None:
        return

    try:
        charset = envadapter.getPreferredCharsets()[0]
    except IndexError:
        # Exception caused by empty list! This is okay though, since the
        # browser just could have sent a '*', which means we can choose
        # the encoding, which we do here now.
        charset = 'utf-8'
    return charset


class DirectResult(object):
    """A generic result object.

    The result's body can be any iterable. It is the responsibility of the
    application to specify all headers related to the content, such as the
    content type and length.
    """
    interface.implements(IResult)

    def __init__(self, body):
        self.body = body

    def __iter__(self):
        return iter(self.body)

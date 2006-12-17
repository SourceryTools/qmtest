"""Integration with Python standard library module urllib2.

Also includes a redirection bugfix, support for parsing HTML HEAD blocks for
the META HTTP-EQUIV tag contents, and following Refresh header redirects.

Copyright 2002-2006 John J Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file
COPYING.txt included with the distribution).

"""

import copy, time, tempfile, htmlentitydefs, re, logging, types, \
       string, socket, urlparse, urllib2, urllib, httplib, sgmllib
from urllib2 import URLError, HTTPError, BaseHandler
from cStringIO import StringIO
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import _opener
from _request import Request
from _util import isstringlike, startswith, \
     getheaders, closeable_response, response_seek_wrapper
from _html import unescape, unescape_charref
from _headersutil import is_html
from _clientcookie import CookieJar, request_host

debug = logging.getLogger("mechanize.cookies").debug


CHUNK = 1024  # size of chunks fed to HTML HEAD parser, in bytes
DEFAULT_ENCODING = 'latin-1'


# This fixes a bug in urllib2 as of Python 2.1.3 and 2.2.2
#  (http://www.python.org/sf/549151)
# 2.2.3 is broken here (my fault!), 2.3 is fixed.
class HTTPRedirectHandler(BaseHandler):
    # maximum number of redirections to any single URL
    # this is needed because of the state that cookies introduce
    max_repeats = 4
    # maximum total number of redirections (regardless of URL) before
    # assuming we're in a loop
    max_redirections = 10

    # Implementation notes:

    # To avoid the server sending us into an infinite loop, the request
    # object needs to track what URLs we have already seen.  Do this by
    # adding a handler-specific attribute to the Request object.  The value
    # of the dict is used to count the number of times the same URL has
    # been visited.  This is needed because visiting the same URL twice
    # does not necessarily imply a loop, thanks to state introduced by
    # cookies.

    # Always unhandled redirection codes:
    # 300 Multiple Choices: should not handle this here.
    # 304 Not Modified: no need to handle here: only of interest to caches
    #     that do conditional GETs
    # 305 Use Proxy: probably not worth dealing with here
    # 306 Unused: what was this for in the previous versions of protocol??

    def redirect_request(self, newurl, req, fp, code, msg, headers):
        """Return a Request or None in response to a redirect.

        This is called by the http_error_30x methods when a redirection
        response is received.  If a redirection should take place, return a
        new Request to allow http_error_30x to perform the redirect;
        otherwise, return None to indicate that an HTTPError should be
        raised.

        """
        if code in (301, 302, 303, "refresh") or \
               (code == 307 and not req.has_data()):
            # Strictly (according to RFC 2616), 301 or 302 in response to
            # a POST MUST NOT cause a redirection without confirmation
            # from the user (of urllib2, in this case).  In practice,
            # essentially all clients do redirect in this case, so we do
            # the same.
            return Request(newurl,
                           headers=req.headers,
                           origin_req_host=req.get_origin_req_host(),
                           unverifiable=True)
        else:
            raise HTTPError(req.get_full_url(), code, msg, headers, fp)

    def http_error_302(self, req, fp, code, msg, headers):
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI).  Use first header.
        if headers.has_key('location'):
            newurl = getheaders(headers, 'location')[0]
        elif headers.has_key('uri'):
            newurl = getheaders(headers, 'uri')[0]
        else:
            return
        newurl = urlparse.urljoin(req.get_full_url(), newurl)

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new = self.redirect_request(newurl, req, fp, code, msg, headers)
        if new is None:
            return

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(req, 'redirect_dict'):
            visited = new.redirect_dict = req.redirect_dict
            if (visited.get(newurl, 0) >= self.max_repeats or
                len(visited) >= self.max_redirections):
                raise HTTPError(req.get_full_url(), code,
                                self.inf_msg + msg, headers, fp)
        else:
            visited = new.redirect_dict = req.redirect_dict = {}
        visited[newurl] = visited.get(newurl, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.  
        fp.read()
        fp.close()

        return self.parent.open(new)

    http_error_301 = http_error_303 = http_error_307 = http_error_302
    http_error_refresh = http_error_302

    inf_msg = "The HTTP server returned a redirect error that would " \
              "lead to an infinite loop.\n" \
              "The last 30x error message was:\n"


class HTTPRequestUpgradeProcessor(BaseHandler):
    # upgrade urllib2.Request to this module's Request
    # yuck!
    handler_order = 0  # before anything else

    def http_request(self, request):
        if not hasattr(request, "add_unredirected_header"):
            newrequest = Request(request._Request__original, request.data,
                                 request.headers)
            try: newrequest.origin_req_host = request.origin_req_host
            except AttributeError: pass
            try: newrequest.unverifiable = request.unverifiable
            except AttributeError: pass
            request = newrequest
        return request

    https_request = http_request

# XXX would self.reset() work, instead of raising this exception?
class EndOfHeadError(Exception): pass
class AbstractHeadParser:
    # only these elements are allowed in or before HEAD of document
    head_elems = ("html", "head",
                  "title", "base",
                  "script", "style", "meta", "link", "object")
    _entitydefs = htmlentitydefs.name2codepoint
    _encoding = DEFAULT_ENCODING

    def __init__(self):
        self.http_equiv = []

    def start_meta(self, attrs):
        http_equiv = content = None
        for key, value in attrs:
            if key == "http-equiv":
                http_equiv = self.unescape_attr_if_required(value)
            elif key == "content":
                content = self.unescape_attr_if_required(value)
        if http_equiv is not None:
            self.http_equiv.append((http_equiv, content))

    def end_head(self):
        raise EndOfHeadError()

    def handle_entityref(self, name):
        #debug("%s", name)
        self.handle_data(unescape(
            '&%s;' % name, self._entitydefs, self._encoding))

    def handle_charref(self, name):
        #debug("%s", name)
        self.handle_data(unescape_charref(name, self._encoding))

    def unescape_attr(self, name):
        #debug("%s", name)
        return unescape(name, self._entitydefs, self._encoding)

    def unescape_attrs(self, attrs):
        #debug("%s", attrs)
        escaped_attrs = {}
        for key, val in attrs.items():
            escaped_attrs[key] = self.unescape_attr(val)
        return escaped_attrs

    def unknown_entityref(self, ref):
        self.handle_data("&%s;" % ref)

    def unknown_charref(self, ref):
        self.handle_data("&#%s;" % ref)


try:
    import HTMLParser
except ImportError:
    pass
else:
    class XHTMLCompatibleHeadParser(AbstractHeadParser,
                                    HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            AbstractHeadParser.__init__(self)

        def handle_starttag(self, tag, attrs):
            if tag not in self.head_elems:
                raise EndOfHeadError()
            try:
                method = getattr(self, 'start_' + tag)
            except AttributeError:
                try:
                    method = getattr(self, 'do_' + tag)
                except AttributeError:
                    pass # unknown tag
                else:
                    method(attrs)
            else:
                method(attrs)

        def handle_endtag(self, tag):
            if tag not in self.head_elems:
                raise EndOfHeadError()
            try:
                method = getattr(self, 'end_' + tag)
            except AttributeError:
                pass # unknown tag
            else:
                method()

        def unescape(self, name):
            # Use the entitydefs passed into constructor, not
            # HTMLParser.HTMLParser's entitydefs.
            return self.unescape_attr(name)

        def unescape_attr_if_required(self, name):
            return name  # HTMLParser.HTMLParser already did it

class HeadParser(AbstractHeadParser, sgmllib.SGMLParser):

    def _not_called(self):
        assert False

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        AbstractHeadParser.__init__(self)

    def handle_starttag(self, tag, method, attrs):
        if tag not in self.head_elems:
            raise EndOfHeadError()
        if tag == "meta":
            method(attrs)

    def unknown_starttag(self, tag, attrs):
        self.handle_starttag(tag, self._not_called, attrs)

    def handle_endtag(self, tag, method):
        if tag in self.head_elems:
            method()
        else:
            raise EndOfHeadError()

    def unescape_attr_if_required(self, name):
        return self.unescape_attr(name)

def parse_head(fileobj, parser):
    """Return a list of key, value pairs."""
    while 1:
        data = fileobj.read(CHUNK)
        try:
            parser.feed(data)
        except EndOfHeadError:
            break
        if len(data) != CHUNK:
            # this should only happen if there is no HTML body, or if
            # CHUNK is big
            break
    return parser.http_equiv

class HTTPEquivProcessor(BaseHandler):
    """Append META HTTP-EQUIV headers to regular HTTP headers."""

    handler_order = 300  # before handlers that look at HTTP headers

    def __init__(self, head_parser_class=HeadParser,
                 i_want_broken_xhtml_support=False,
                 ):
        self.head_parser_class = head_parser_class
        self._allow_xhtml = i_want_broken_xhtml_support

    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = response_seek_wrapper(response)
        headers = response.info()
        url = response.geturl()
        ct_hdrs = getheaders(response.info(), "content-type")
        if is_html(ct_hdrs, url, self._allow_xhtml):
            try:
                try:
                    html_headers = parse_head(response, self.head_parser_class())
                finally:
                    response.seek(0)
            except (HTMLParser.HTMLParseError,
                    sgmllib.SGMLParseError):
                pass
            else:
                for hdr, val in html_headers:
                    # rfc822.Message interprets this as appending, not clobbering
                    headers[hdr] = val
        return response

    https_response = http_response

class SeekableProcessor(BaseHandler):
    """Make responses seekable."""

    def any_response(self, request, response):
        if not hasattr(response, "seek"):
            return response_seek_wrapper(response)
        return response

class HTTPCookieProcessor(BaseHandler):
    """Handle HTTP cookies.

    Public attributes:

    cookiejar: CookieJar instance

    """
    def __init__(self, cookiejar=None):
        if cookiejar is None:
            cookiejar = CookieJar()
        self.cookiejar = cookiejar

    def http_request(self, request):
        self.cookiejar.add_cookie_header(request)
        return request

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        return response

    https_request = http_request
    https_response = http_response

try:
    import robotparser
except ImportError:
    pass
else:
    class RobotExclusionError(urllib2.HTTPError):
        def __init__(self, request, *args):
            apply(urllib2.HTTPError.__init__, (self,)+args)
            self.request = request

    class HTTPRobotRulesProcessor(BaseHandler):
        # before redirections, after everything else
        handler_order = 800

        try:
            from httplib import HTTPMessage
        except:
            from mimetools import Message
            http_response_class = Message
        else:
            http_response_class = HTTPMessage

        def __init__(self, rfp_class=robotparser.RobotFileParser):
            self.rfp_class = rfp_class
            self.rfp = None
            self._host = None

        def http_request(self, request):
            host = request.get_host()
            scheme = request.get_type()
            if host != self._host:
                self.rfp = self.rfp_class()
                self.rfp.set_url(scheme+"://"+host+"/robots.txt")
                self.rfp.read()
                self._host = host

            ua = request.get_header("User-agent", "")
            if self.rfp.can_fetch(ua, request.get_full_url()):
                return request
            else:
                msg = "request disallowed by robots.txt"
                raise RobotExclusionError(
                    request,
                    request.get_full_url(),
                    403, msg,
                    self.http_response_class(StringIO()), StringIO(msg))

        https_request = http_request

class HTTPRefererProcessor(BaseHandler):
    """Add Referer header to requests.

    This only makes sense if you use each RefererProcessor for a single
    chain of requests only (so, for example, if you use a single
    HTTPRefererProcessor to fetch a series of URLs extracted from a single
    page, this will break).

    There's a proper implementation of this in module mechanize.

    """
    def __init__(self):
        self.referer = None

    def http_request(self, request):
        if ((self.referer is not None) and
            not request.has_header("Referer")):
            request.add_unredirected_header("Referer", self.referer)
        return request

    def http_response(self, request, response):
        self.referer = response.geturl()
        return response

    https_request = http_request
    https_response = http_response

class HTTPResponseDebugProcessor(BaseHandler):
    handler_order = 900  # before redirections, after everything else

    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = response_seek_wrapper(response)
        info = getLogger("mechanize.http_responses").info
        try:
            info(response.read())
        finally:
            response.seek(0)
        info("*****************************************************")
        return response

    https_response = http_response

class HTTPRedirectDebugProcessor(BaseHandler):
    def http_request(self, request):
        if hasattr(request, "redirect_dict"):
            info = getLogger("mechanize.http_redirects").info
            info("redirecting to %s", request.get_full_url())
        return request

class HTTPRefreshProcessor(BaseHandler):
    """Perform HTTP Refresh redirections.

    Note that if a non-200 HTTP code has occurred (for example, a 30x
    redirect), this processor will do nothing.

    By default, only zero-time Refresh headers are redirected.  Use the
    max_time attribute / constructor argument to allow Refresh with longer
    pauses.  Use the honor_time attribute / constructor argument to control
    whether the requested pause is honoured (with a time.sleep()) or
    skipped in favour of immediate redirection.

    Public attributes:

    max_time: see above
    honor_time: see above

    """
    handler_order = 1000

    def __init__(self, max_time=0, honor_time=True):
        self.max_time = max_time
        self.honor_time = honor_time

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        if code == 200 and hdrs.has_key("refresh"):
            refresh = getheaders(hdrs, "refresh")[0]
            ii = string.find(refresh, ";")
            if ii != -1:
                pause, newurl_spec = float(refresh[:ii]), refresh[ii+1:]
                jj = string.find(newurl_spec, "=")
                if jj != -1:
                    key, newurl = newurl_spec[:jj], newurl_spec[jj+1:]
                if key.strip().lower() != "url":
                    debug("bad Refresh header: %r" % refresh)
                    return response
            else:
                pause, newurl = float(refresh), response.geturl()
            if (self.max_time is None) or (pause <= self.max_time):
                if pause > 1E-3 and self.honor_time:
                    time.sleep(pause)
                hdrs["location"] = newurl
                # hardcoded http is NOT a bug
                response = self.parent.error(
                    "http", request, response,
                    "refresh", msg, hdrs)

        return response

    https_response = http_response

class HTTPErrorProcessor(BaseHandler):
    """Process HTTP error responses.

    The purpose of this handler is to to allow other response processors a
    look-in by removing the call to parent.error() from
    AbstractHTTPHandler.

    For non-200 error codes, this just passes the job on to the
    Handler.<proto>_error_<code> methods, via the OpenerDirector.error
    method.  Eventually, urllib2.HTTPDefaultErrorHandler will raise an
    HTTPError if no other handler handles the error.

    """
    handler_order = 1000  # after all other processors

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        if code != 200:
            # hardcoded http is NOT a bug
            response = self.parent.error(
                "http", request, response, code, msg, hdrs)

        return response

    https_response = http_response


class AbstractHTTPHandler(BaseHandler):

    def __init__(self, debuglevel=0):
        self._debuglevel = debuglevel

    def set_http_debuglevel(self, level):
        self._debuglevel = level

    def do_request_(self, request):
        host = request.get_host()
        if not host:
            raise URLError('no host given')

        if request.has_data():  # POST
            data = request.get_data()
            if not request.has_header('Content-type'):
                request.add_unredirected_header(
                    'Content-type',
                    'application/x-www-form-urlencoded')

        scheme, sel = urllib.splittype(request.get_selector())
        sel_host, sel_path = urllib.splithost(sel)
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', sel_host or host)
        for name, value in self.parent.addheaders:
            name = string.capitalize(name)
            if not request.has_header(name):
                request.add_unredirected_header(name, value)

        return request

    def do_open(self, http_class, req):
        """Return an addinfourl object for the request, using http_class.

        http_class must implement the HTTPConnection API from httplib.
        The addinfourl return value is a file-like object.  It also
        has methods and attributes including:
            - info(): return a mimetools.Message object for the headers
            - geturl(): return the original request URL
            - code: HTTP status code
        """
        host = req.get_host()
        if not host:
            raise URLError('no host given')

        h = http_class(host) # will parse host:port
        h.set_debuglevel(self._debuglevel)

        headers = req.headers.copy()
        headers.update(req.unredirected_hdrs)
        # We want to make an HTTP/1.1 request, but the addinfourl
        # class isn't prepared to deal with a persistent connection.
        # It will try to read all remaining data from the socket,
        # which will block while the server waits for the next request.
        # So make sure the connection gets closed after the (only)
        # request.
        headers["Connection"] = "close"
        try:
            h.request(req.get_method(), req.get_selector(), req.data, headers)
            r = h.getresponse()
        except socket.error, err: # XXX what error?
            raise URLError(err)

        # Pick apart the HTTPResponse object to get the addinfourl
        # object initialized properly.

        # Wrap the HTTPResponse object in socket's file object adapter
        # for Windows.  That adapter calls recv(), so delegate recv()
        # to read().  This weird wrapping allows the returned object to
        # have readline() and readlines() methods.

        # XXX It might be better to extract the read buffering code
        # out of socket._fileobject() and into a base class.

        r.recv = r.read
        fp = socket._fileobject(r, 'rb', -1)

        resp = closeable_response(fp, r.msg, req.get_full_url(),
                                  r.status, r.reason)
        return resp


class HTTPHandler(AbstractHTTPHandler):
    def http_open(self, req):
        return self.do_open(httplib.HTTPConnection, req)

    http_request = AbstractHTTPHandler.do_request_

if hasattr(httplib, 'HTTPS'):
    class HTTPSHandler(AbstractHTTPHandler):
        def https_open(self, req):
            return self.do_open(httplib.HTTPSConnection, req)

        https_request = AbstractHTTPHandler.do_request_

class OpenerFactory:
    """This class's interface is quite likely to change."""

    default_classes = [
        # handlers
        urllib2.ProxyHandler,
        urllib2.UnknownHandler,
        HTTPHandler,  # from this module (derived from new AbstractHTTPHandler)
        urllib2.HTTPDefaultErrorHandler,
        HTTPRedirectHandler,  # from this module (bugfixed)
        urllib2.FTPHandler,
        urllib2.FileHandler,
        # processors
        HTTPRequestUpgradeProcessor,
        HTTPCookieProcessor,
        HTTPErrorProcessor
        ]
    handlers = []
    replacement_handlers = []

    def __init__(self, klass=_opener.OpenerDirector):
        self.klass = klass

    def build_opener(self, *handlers):
        """Create an opener object from a list of handlers and processors.

        The opener will use several default handlers and processors, including
        support for HTTP and FTP.

        If any of the handlers passed as arguments are subclasses of the
        default handlers, the default handlers will not be used.

        """
        opener = self.klass()
        default_classes = list(self.default_classes)
        if hasattr(httplib, 'HTTPS'):
            default_classes.append(HTTPSHandler)
        skip = []
        for klass in default_classes:
            for check in handlers:
                if type(check) == types.ClassType:
                    if issubclass(check, klass):
                        skip.append(klass)
                elif type(check) == types.InstanceType:
                    if isinstance(check, klass):
                        skip.append(klass)
        for klass in skip:
            default_classes.remove(klass)

        for klass in default_classes:
            opener.add_handler(klass())
        for h in handlers:
            if type(h) == types.ClassType:
                h = h()
            opener.add_handler(h)

        return opener

build_opener = OpenerFactory().build_opener

_opener = None
urlopen_lock = _threading.Lock()
def urlopen(url, data=None):
    global _opener
    if _opener is None:
        urlopen_lock.acquire()
        try:
            if _opener is None:
                _opener = build_opener()
        finally:
            urlopen_lock.release()
    return _opener.open(url, data)

def urlretrieve(url, filename=None, reporthook=None, data=None):
    global _opener
    if _opener is None:
        urlopen_lock.acquire()
        try:
            if _opener is None:
                _opener = build_opener()
        finally:
            urlopen_lock.release()
    return _opener.retrieve(url, filename, reporthook, data)

def install_opener(opener):
    global _opener
    _opener = opener

"""Convenient HTTP UserAgent class.

This is a subclass of urllib2.OpenerDirector.


Copyright 2003-2006 John J. Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it under
the terms of the BSD or ZPL 2.1 licenses (see the file COPYING.txt
included with the distribution).

"""

import sys, warnings, urllib2

from _opener import OpenerDirector

import _urllib2
import _auth
import _gzip


class HTTPRefererProcessor(_urllib2.BaseHandler):
    def http_request(self, request):
        # See RFC 2616 14.36.  The only times we know the source of the
        # request URI has a URI associated with it are redirect, and
        # Browser.click() / Browser.submit() / Browser.follow_link().
        # Otherwise, it's the user's job to add any Referer header before
        # .open()ing.
        if hasattr(request, "redirect_dict"):
            request = self.parent._add_referer_header(
                request, origin_request=False)
        return request

    https_request = http_request


class UserAgent(OpenerDirector):
    """Convenient user-agent class.

    Do not use .add_handler() to add a handler for something already dealt with
    by this code.

    Public attributes:

    addheaders: list of (name, value) pairs specifying headers to send with
     every request, unless they are overridden in the Request instance.

     >>> ua = UserAgent()
     >>> ua.addheaders = [
     ...  ("User-agent", "Mozilla/5.0 (compatible)"),
     ...  ("From", "responsible.person@example.com")]

    """

    handler_classes = {
        # scheme handlers
        "http": _urllib2.HTTPHandler,
        # CacheFTPHandler is buggy, at least in 2.3, so we don't use it
        "ftp": _urllib2.FTPHandler,
        "file": _urllib2.FileHandler,
        "gopher": _urllib2.GopherHandler,

        # other handlers
        "_unknown": _urllib2.UnknownHandler,
        # HTTP{S,}Handler depend on HTTPErrorProcessor too
        "_http_error": _urllib2.HTTPErrorProcessor,
        "_http_request_upgrade": _urllib2.HTTPRequestUpgradeProcessor,
        "_http_default_error": _urllib2.HTTPDefaultErrorHandler,

        # feature handlers
        "_basicauth": _urllib2.HTTPBasicAuthHandler,
        "_digestauth": _urllib2.HTTPDigestAuthHandler,
        "_redirect": _urllib2.HTTPRedirectHandler,
        "_cookies": _urllib2.HTTPCookieProcessor,
        "_refresh": _urllib2.HTTPRefreshProcessor,
        "_referer": HTTPRefererProcessor,  # from this module, note
        "_equiv": _urllib2.HTTPEquivProcessor,
        "_seek": _urllib2.SeekableProcessor,
        "_proxy": _urllib2.ProxyHandler,
        "_proxy_basicauth": _urllib2.ProxyBasicAuthHandler,
        "_proxy_digestauth": _urllib2.ProxyDigestAuthHandler,
        "_robots": _urllib2.HTTPRobotRulesProcessor,
        "_gzip": _gzip.HTTPGzipProcessor,  # experimental!

        # debug handlers
        "_debug_redirect": _urllib2.HTTPRedirectDebugProcessor,
        "_debug_response_body": _urllib2.HTTPResponseDebugProcessor,
        }

    default_schemes = ["http", "ftp", "file", "gopher"]
    default_others = ["_unknown", "_http_error", "_http_request_upgrade",
                      "_http_default_error",
                      ]
    default_features = ["_redirect", "_cookies", "_referer",
                        "_refresh", "_equiv",
                        "_basicauth", "_digestauth",
                        "_proxy", "_proxy_basicauth", "_proxy_digestauth",
                        "_seek", "_robots",
                        ]
    if hasattr(_urllib2, 'HTTPSHandler'):
        handler_classes["https"] = _urllib2.HTTPSHandler
        default_schemes.append("https")

    def __init__(self):
        OpenerDirector.__init__(self)

        ua_handlers = self._ua_handlers = {}
        for scheme in (self.default_schemes+
                       self.default_others+
                       self.default_features):
            klass = self.handler_classes[scheme]
            ua_handlers[scheme] = klass()
        for handler in ua_handlers.itervalues():
            self.add_handler(handler)

        # Yuck.
        # Ensure correct default constructor args were passed to
        # HTTPRefererProcessor and HTTPEquivProcessor.
        if "_refresh" in ua_handlers:
            self.set_handle_refresh(True)
        if "_equiv" in ua_handlers:
            self.set_handle_equiv(True)
        # Ensure default password managers are installed.
        pm = ppm = None
        if "_basicauth" in ua_handlers or "_digestauth" in ua_handlers:
            pm = _urllib2.HTTPPasswordMgrWithDefaultRealm()
        if ("_proxy_basicauth" in ua_handlers or
            "_proxy_digestauth" in ua_handlers):
            ppm = _auth.HTTPProxyPasswordMgr()
        self.set_password_manager(pm)
        self.set_proxy_password_manager(ppm)

        # special case, requires extra support from mechanize.Browser
        self._handle_referer = True

    def close(self):
        OpenerDirector.close(self)
        self._ua_handlers = None

    # XXX
##     def set_timeout(self, timeout):
##         self._timeout = timeout
##     def set_http_connection_cache(self, conn_cache):
##         self._http_conn_cache = conn_cache
##     def set_ftp_connection_cache(self, conn_cache):
##         # XXX ATM, FTP has cache as part of handler; should it be separate?
##         self._ftp_conn_cache = conn_cache

    def set_handled_schemes(self, schemes):
        """Set sequence of URL scheme (protocol) strings.

        For example: ua.set_handled_schemes(["http", "ftp"])

        If this fails (with ValueError) because you've passed an unknown
        scheme, the set of handled schemes will not be changed.

        """
        want = {}
        for scheme in schemes:
            if scheme.startswith("_"):
                raise ValueError("not a scheme '%s'" % scheme)
            if scheme not in self.handler_classes:
                raise ValueError("unknown scheme '%s'")
            want[scheme] = None

        # get rid of scheme handlers we don't want
        for scheme, oldhandler in self._ua_handlers.items():
            if scheme.startswith("_"): continue  # not a scheme handler
            if scheme not in want:
                self._replace_handler(scheme, None)
            else:
                del want[scheme]  # already got it
        # add the scheme handlers that are missing
        for scheme in want.keys():
            self._set_handler(scheme, True)

    def _add_referer_header(self, request, origin_request=True):
        raise NotImplementedError(
            "this class can't do HTTP Referer: use mechanize.Browser instead")

    def set_cookiejar(self, cookiejar):
        """Set a mechanize.CookieJar, or None."""
        self._set_handler("_cookies", obj=cookiejar)

    # XXX could use Greg Stein's httpx for some of this instead?
    # or httplib2??
    def set_proxies(self, proxies):
        """Set a dictionary mapping URL scheme to proxy specification, or None.

        e.g. {"http": "joe:password@myproxy.example.com:3128",
              "ftp": "proxy.example.com"}

        """
        self._set_handler("_proxy", obj=proxies)

    def add_password(self, url, user, password, realm=None):
        self._password_manager.add_password(realm, url, user, password)
    def add_proxy_password(self, user, password, hostport=None, realm=None):
        self._proxy_password_manager.add_password(
            realm, hostport, user, password)

    # the following are rarely useful -- use add_password / add_proxy_password
    # instead
    def set_password_manager(self, password_manager):
        """Set a mechanize.HTTPPasswordMgrWithDefaultRealm, or None."""
        self._password_manager = password_manager
        self._set_handler("_basicauth", obj=password_manager)
        self._set_handler("_digestauth", obj=password_manager)
    def set_proxy_password_manager(self, password_manager):
        """Set a mechanize.HTTPProxyPasswordMgr, or None."""
        self._proxy_password_manager = password_manager
        self._set_handler("_proxy_basicauth", obj=password_manager)
        self._set_handler("_proxy_digestauth", obj=password_manager)

    # these methods all take a boolean parameter
    def set_handle_robots(self, handle):
        """Set whether to observe rules from robots.txt."""
        self._set_handler("_robots", handle)
    def set_handle_redirect(self, handle):
        """Set whether to handle HTTP 30x redirections."""
        self._set_handler("_redirect", handle)
    def set_handle_refresh(self, handle, max_time=None, honor_time=True):
        """Set whether to handle HTTP Refresh headers."""
        self._set_handler("_refresh", handle, constructor_kwds=
                          {"max_time": max_time, "honor_time": honor_time})
    def set_handle_equiv(self, handle, head_parser_class=None):
        """Set whether to treat HTML http-equiv headers like HTTP headers.

        Response objects will be .seek()able if this is set.

        """
        if head_parser_class is not None:
            constructor_kwds = {"head_parser_class": head_parser_class}
        else:
            constructor_kwds={}
        self._set_handler("_equiv", handle, constructor_kwds=constructor_kwds)
    def set_handle_referer(self, handle):
        """Set whether to add Referer header to each request.

        This base class does not implement this feature (so don't turn this on
        if you're using this base class directly), but the subclass
        mechanize.Browser does.

        """
        self._set_handler("_referer", handle)
        self._handle_referer = bool(handle)
    def set_handle_gzip(self, handle):
        """Handle gzip transfer encoding.

        """
        if handle:
            warnings.warn(
                "gzip transfer encoding is experimental!", stacklevel=2)
        self._set_handler("_gzip", handle)
    def set_debug_redirects(self, handle):
        """Log information about HTTP redirects (including refreshes).

        Logging is performed using module logging.  The logger name is
        "mechanize.http_redirects".  To actually print some debug output,
        eg:

        import sys, logging
        logger = logging.getLogger("mechanize.http_redirects")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)

        Other logger names relevant to this module:

        "mechanize.http_responses"
        "mechanize.cookies" (or "cookielib" if running Python 2.4)

        To turn on everything:

        import sys, logging
        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)

        """
        self._set_handler("_debug_redirect", handle)
    def set_debug_responses(self, handle):
        """Log HTTP response bodies.

        See docstring for .set_debug_redirects() for details of logging.

        """
        self._set_handler("_debug_response_body", handle)
    def set_debug_http(self, handle):
        """Print HTTP headers to sys.stdout."""
        level = int(bool(handle))
        for scheme in "http", "https":
            h = self._ua_handlers.get(scheme)
            if h is not None:
                h.set_http_debuglevel(level)

    def _set_handler(self, name, handle=None, obj=None,
                     constructor_args=(), constructor_kwds={}):
        if handle is None:
            handle = obj is not None
        if handle:
            handler_class = self.handler_classes[name]
            if obj is not None:
                newhandler = handler_class(obj)
            else:
                newhandler = handler_class(*constructor_args, **constructor_kwds)
        else:
            newhandler = None
        self._replace_handler(name, newhandler)

    def _replace_handler(self, name, newhandler=None):
        # first, if handler was previously added, remove it
        if name is not None:
            handler = self._ua_handlers.get(name)
            if handler:
                try:
                    self.handlers.remove(handler)
                except ValueError:
                    pass
        # then add the replacement, if any
        if newhandler is not None:
            self.add_handler(newhandler)
            self._ua_handlers[name] = newhandler

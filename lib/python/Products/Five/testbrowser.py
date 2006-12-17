"""Support for using zope.testbrowser from Zope2.

Mostly just copy and paste from zope.testbrowser.testing.
"""

import urllib2

import mechanize

from zope.testbrowser import testing
from zope.testbrowser import browser
import zope.publisher.http


class PublisherConnection(testing.PublisherConnection):

    def __init__(self, host):
        from Testing.ZopeTestCase.zopedoctest.functional import http
        self.caller = http
        self.host = host

    def getresponse(self):
        """Return a ``urllib2`` compatible response.

        The goal of ths method is to convert the Zope Publisher's reseponse to
        a ``urllib2`` compatible response, which is also understood by
        mechanize.
        """
        real_response = self.response._response
        status = real_response.getStatus()
        reason = zope.publisher.http.status_reasons[real_response.status]
        headers = []
        # Convert header keys to camel case. This is basically a copy
        # paste from ZPublisher.HTTPResponse
        for key, val in real_response.headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = "%s%s" % (key[:1].upper(), key[1:])
                start = 0
                l = key.find('-',start)
                while l >= start:
                    key = "%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start = l + 1
                    l = key.find('-', start)
            headers.append((key, val))
        # get the cookies, breaking them into tuples for sorting
        cookies = [(c[:10], c[12:]) for c in real_response._cookie_list()]
        headers.extend(cookies)
        headers.sort()
        headers.insert(0, ('Status', "%s %s" % (status, reason)))
        headers = '\r\n'.join('%s: %s' % h for h in headers)
        content = real_response.body
        return testing.PublisherResponse(content, headers, status, reason)


class PublisherHTTPHandler(urllib2.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(PublisherConnection, req)


class PublisherMechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    default_schemes = ['http']
    default_others = ['_http_error', '_http_request_upgrade',
                      '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth', '_seek' ]

    def __init__(self, *args, **kws):
        inherited_handlers = ['_unknown', '_http_error',
            '_http_request_upgrade', '_http_default_error', '_basicauth',
            '_digestauth', '_redirect', '_cookies', '_referer',
            '_refresh', '_equiv', '_seek', '_gzip']

        self.handler_classes = {"http": PublisherHTTPHandler}
        for name in inherited_handlers:
            self.handler_classes[name] = mechanize.Browser.handler_classes[name]

        mechanize.Browser.__init__(self, *args, **kws)


class Browser(browser.Browser):
    """A Zope ``testbrowser` Browser that uses the Zope Publisher."""

    def __init__(self, url=None):
        mech_browser = PublisherMechanizeBrowser()
        # override the http handler class
        mech_browser.handler_classes["http"] = PublisherHTTPHandler
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)


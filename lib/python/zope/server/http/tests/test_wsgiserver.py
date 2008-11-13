##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.  All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 1.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""Test Puvlisher-based HTTP Server

$Id: test_wsgiserver.py 76167 2007-06-02 18:39:35Z philikon $
"""
import StringIO
import unittest
from asyncore import socket_map, poll
from threading import Thread
from time import sleep
from httplib import HTTPConnection

from zope.server.taskthreads import ThreadedTaskDispatcher
from zope.server.http.wsgihttpserver import WSGIHTTPServer

from zope.component.testing import PlacelessSetup
import zope.component

from zope.i18n.interfaces import IUserPreferredCharsets

from zope.publisher.publish import publish
from zope.publisher.http import IHTTPRequest
from zope.publisher.http import HTTPCharsets
from zope.publisher.browser import BrowserRequest
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces import Redirect, Retry
from zope.publisher.http import HTTPRequest

td = ThreadedTaskDispatcher()

LOCALHOST = '127.0.0.1'

HTTPRequest.STAGGER_RETRIES = 0  # Don't pause.


class Conflict(Exception):
    """
    Pseudo ZODB conflict error.
    """


class PublicationWithConflict(DefaultPublication):

    def handleException(self, object, request, exc_info, retry_allowed=1):
        if exc_info[0] is Conflict and retry_allowed:
            # This simulates a ZODB retry.
            raise Retry(exc_info)
        else:
            DefaultPublication.handleException(self, object, request, exc_info,
                                               retry_allowed)

class Accepted(Exception):
    pass

class tested_object(object):
    """Docstring required by publisher."""
    tries = 0

    def __call__(self, REQUEST):
        return 'URL invoked: %s' % REQUEST.URL

    def redirect_method(self, REQUEST):
        "Generates a redirect using the redirect() method."
        REQUEST.response.redirect("http://somewhere.com/redirect")

    def redirect_exception(self):
        "Generates a redirect using an exception."
        raise Redirect("http://somewhere.com/exception")

    def conflict(self, REQUEST, wait_tries):
        """
        Returns 202 status only after (wait_tries) tries.
        """
        if self.tries >= int(wait_tries):
            raise Accepted
        else:
            self.tries += 1
            raise Conflict


class WSGIInfo(object):
    """Docstring required by publisher"""

    def __call__(self, REQUEST):
        """Return a list of variables beginning with 'wsgi.'"""
        r = []
        for name in REQUEST.keys():
            if name.startswith('wsgi.'):
                r.append(name)
        return ' '.join(r)

    def version(self, REQUEST):
        """Return WSGI version"""
        return str(REQUEST['wsgi.version'])

    def url_scheme(self, REQUEST):
        """Return WSGI URL scheme"""
        return REQUEST['wsgi.url_scheme']

    def multithread(self, REQUEST):
        """Return WSGI multithreadedness"""
        return str(bool(REQUEST['wsgi.multithread']))

    def multiprocess(self, REQUEST):
        """Return WSGI multiprocessedness"""
        return str(bool(REQUEST['wsgi.multiprocess']))

    def run_once(self, REQUEST):
        """Return whether WSGI app is invoked only once or not"""
        return str(bool(REQUEST['wsgi.run_once']))

class Tests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Tests, self).setUp()
        zope.component.provideAdapter(HTTPCharsets, [IHTTPRequest],
                                      IUserPreferredCharsets, '')
        obj = tested_object()
        obj.folder = tested_object()
        obj.folder.item = tested_object()
        obj._protected = tested_object()
        obj.wsgi = WSGIInfo()

        pub = PublicationWithConflict(obj)

        def application(environ, start_response):
            request = BrowserRequest(environ['wsgi.input'], environ)
            request.setPublication(pub)
            request = publish(request)
            response = request.response
            start_response(response.getStatusString(), response.getHeaders())
            return response.consumeBodyIter()

        td.setThreadCount(4)
        # Bind to any port on localhost.
        self.server = WSGIHTTPServer(application, 'Browser',
                                     LOCALHOST, 0, task_dispatcher=td)

        self.port = self.server.socket.getsockname()[1]
        self.run_loop = 1
        self.thread = Thread(target=self.loop)
        self.thread.start()
        sleep(0.1)  # Give the thread some time to start.

    def tearDown(self):
        self.run_loop = 0
        self.thread.join()
        td.shutdown()
        self.server.close()
        super(Tests, self).tearDown()

    def loop(self):
        while self.run_loop:
            poll(0.1, socket_map)

    def invokeRequest(self, path='/', add_headers=None, request_body=''):
        h = HTTPConnection(LOCALHOST, self.port)
        h.putrequest('GET', path)
        h.putheader('Accept', 'text/plain')
        if add_headers:
            for k, v in add_headers.items():
                h.putheader(k, v)
        if request_body:
            h.putheader('Content-Length', str(int(len(request_body))))
        h.endheaders()
        if request_body:
            h.send(request_body)
        response = h.getresponse()
        length = int(response.getheader('Content-Length', '0'))
        if length:
            response_body = response.read(length)
        else:
            response_body = ''

        self.assertEqual(length, len(response_body))

        return response.status, response_body


    def testDeeperPath(self):
        status, response_body = self.invokeRequest('/folder/item')
        self.assertEqual(status, 200)
        expect_response = 'URL invoked: http://%s:%d/folder/item' % (
            LOCALHOST, self.port)
        self.assertEqual(response_body, expect_response)

    def testNotFound(self):
        status, response_body = self.invokeRequest('/foo/bar')
        self.assertEqual(status, 404)

    def testUnauthorized(self):
        status, response_body = self.invokeRequest('/_protected')
        self.assertEqual(status, 401)

    def testRedirectMethod(self):
        status, response_body = self.invokeRequest('/redirect_method')
        self.assertEqual(status, 303)

    def testRedirectException(self):
        status, response_body = self.invokeRequest('/redirect_exception')
        self.assertEqual(status, 303)
        status, response_body = self.invokeRequest('/folder/redirect_exception')
        self.assertEqual(status, 303)

    def testConflictRetry(self):
        status, response_body = self.invokeRequest('/conflict?wait_tries=2')
        # Expect the "Accepted" response since the retries will succeed.
        self.assertEqual(status, 202)

    def testFailedConflictRetry(self):
        status, response_body = self.invokeRequest('/conflict?wait_tries=10')
        # Expect a "Conflict" response since there will be too many
        # conflicts.
        self.assertEqual(status, 409)

    def testWSGIVariables(self):
        # Assert that the environment contains all required WSGI variables
        status, response_body = self.invokeRequest('/wsgi')
        wsgi_variables = set(response_body.split())
        self.assertEqual(wsgi_variables,
                         set(['wsgi.version', 'wsgi.url_scheme', 'wsgi.input',
                              'wsgi.errors', 'wsgi.multithread',
                              'wsgi.multiprocess', 'wsgi.run_once']))

    def testWSGIVersion(self):
        status, response_body = self.invokeRequest('/wsgi/version')
        self.assertEqual("(1, 0)", response_body)

    def testWSGIURLScheme(self):
        status, response_body = self.invokeRequest('/wsgi/url_scheme')
        self.assertEqual('http', response_body)

    def testWSGIMultithread(self):
        status, response_body = self.invokeRequest('/wsgi/multithread')
        self.assertEqual('True', response_body)

    def testWSGIMultiprocess(self):
        status, response_body = self.invokeRequest('/wsgi/multiprocess')
        self.assertEqual('True', response_body)

    def testWSGIRunOnce(self):
        status, response_body = self.invokeRequest('/wsgi/run_once')
        self.assertEqual('False', response_body)

    def test_server_uses_iterable(self):
        # Make sure that the task write method isn't called with a
        # str or non iterable
        class FakeTask:
            getCGIEnvironment = lambda _: {}
            class request_data:
                getBodyStream = lambda _: StringIO.StringIO()
            request_data = request_data()
            setResponseStatus = appendResponseHeaders = lambda *_: None

            def write(self, v):
                if isinstance(v, str):
                    raise TypeError("Should only write iterables")
                list(v)
        self.server.executeRequest(FakeTask())


def test_suite():
    return unittest.TestSuite(unittest.makeSuite(Tests))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

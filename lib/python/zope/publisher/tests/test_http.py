# -*- coding: latin-1 -*-
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
"""HTTP Publisher Tests

$Id: test_http.py 69340 2006-08-02 14:16:04Z mj $
"""
import unittest

import zope.event
from zope.interface import implements
from zope.publisher.interfaces.logginginfo import ILoggingInfo
from zope.publisher.http import HTTPRequest, HTTPResponse
from zope.publisher.http import HTTPInputStream, StrResult
from zope.publisher.publish import publish
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces.http import IHTTPRequest, IHTTPResponse
from zope.publisher.interfaces.http import IHTTPApplicationResponse
from zope.publisher.interfaces import IResponse

from zope.i18n.interfaces.locales import ILocale

from zope.interface.verify import verifyObject

from StringIO import StringIO
from Cookie import CookieError


class UserStub(object):
    implements(ILoggingInfo)

    def __init__(self, id):
        self._id = id

    def getId(self):
        return self._id

    def getLogMessage(self):
        return self._id


data = '''\
line 1
line 2
line 3'''


class HTTPInputStreamTests(unittest.TestCase):

    def setUp(self):
        self.stream = HTTPInputStream(StringIO(data), {})

    def getCacheStreamValue(self):
        self.stream.cacheStream.seek(0)
        result = self.stream.cacheStream.read()
        # We just did a read on a file opened for update.  If the next
        # operation on that file is a write, behavior is 100% undefined,
        # and it in fact frequently (but not always) blows up on Windows.
        # Behavior is 100% defined instead if we explictly seek.  Since
        # we expect to be at EOF now, explicitly seek to the end.
        self.stream.cacheStream.seek(0, 2)
        return result

    def testRead(self):
        output = ''
        self.assertEqual(output, self.getCacheStreamValue())
        output += self.stream.read(5)
        self.assertEqual(output, self.getCacheStreamValue())
        output += self.stream.read()
        self.assertEqual(output, self.getCacheStreamValue())
        self.assertEqual(data, self.getCacheStreamValue())

    def testReadLine(self):
        output = self.stream.readline()
        self.assertEqual(output, self.getCacheStreamValue())
        output += self.stream.readline()
        self.assertEqual(output, self.getCacheStreamValue())
        output += self.stream.readline()
        self.assertEqual(output, self.getCacheStreamValue())
        output += self.stream.readline()
        self.assertEqual(output, self.getCacheStreamValue())
        self.assertEqual(data, self.getCacheStreamValue())

    def testReadLines(self):
        output = ''.join(self.stream.readlines(4))
        self.assertEqual(output, self.getCacheStreamValue())
        output += ''.join(self.stream.readlines())
        self.assertEqual(output, self.getCacheStreamValue())
        self.assertEqual(data, self.getCacheStreamValue())

    def testGetChacheStream(self):
        self.stream.read(5)
        self.assertEqual(data, self.stream.getCacheStream().read())


class HTTPTests(unittest.TestCase):

    _testEnv =  {
        'PATH_INFO':          '/folder/item',
        'a':                  '5',
        'b':                  6,
        'SERVER_URL':         'http://foobar.com',
        'HTTP_HOST':          'foobar.com',
        'CONTENT_LENGTH':     '0',
        'HTTP_AUTHORIZATION': 'Should be in accessible',
        'GATEWAY_INTERFACE':  'TestFooInterface/1.0',
        'HTTP_OFF_THE_WALL':  "Spam 'n eggs",
        'HTTP_ACCEPT_CHARSET': 'ISO-8859-1, UTF-8;q=0.66, UTF-16;q=0.33',
    }

    def setUp(self):
        class AppRoot(object):
            """Required docstring for the publisher."""

        class Folder(object):
            """Required docstring for the publisher."""

        class Item(object):
            """Required docstring for the publisher."""
            def __call__(self, a, b):
                return "%s, %s" % (`a`, `b`)

        self.app = AppRoot()
        self.app.folder = Folder()
        self.app.folder.item = Item()
        self.app.xxx = Item()

    def _createRequest(self, extra_env={}, body=""):
        env = self._testEnv.copy()
        env.update(extra_env)
        if len(body):
            env['CONTENT_LENGTH'] = str(len(body))

        publication = DefaultPublication(self.app)
        instream = StringIO(body)
        request = HTTPRequest(instream, env)
        request.setPublication(publication)
        return request

    def _publisherResults(self, extra_env={}, body=""):
        request = self._createRequest(extra_env, body)
        response = request.response
        publish(request, handle_errors=False)
        headers = response.getHeaders()
        headers.sort()
        return (
            "Status: %s\r\n" % response.getStatusString()
            +
            "\r\n".join([("%s: %s" % h) for h in headers]) + "\r\n\r\n"
            +
            ''.join(response.consumeBody())
            )

    def test_repr(self):
        request = self._createRequest()
        expect = '<%s.%s instance URL=http://foobar.com>' % (
            request.__class__.__module__, request.__class__.__name__)
        self.assertEqual(repr(request), expect)

    def testTraversalToItem(self):
        res = self._publisherResults()
        self.failUnlessEqual(
            res,
            "Status: 200 Ok\r\n"
            "Content-Length: 6\r\n"
            "X-Powered-By: Zope (www.zope.org), Python (www.python.org)\r\n"
            "\r\n"
            "'5', 6")

    def testRedirect(self):
        # test HTTP/1.0
        env = {'SERVER_PROTOCOL':'HTTP/1.0'}

        request = self._createRequest(env, '')
        location = request.response.redirect('http://foobar.com/redirected')
        self.assertEquals(location, 'http://foobar.com/redirected')
        self.assertEquals(request.response.getStatus(), 302)
        self.assertEquals(request.response.getHeader('location'), location)

        # test HTTP/1.1
        env = {'SERVER_PROTOCOL':'HTTP/1.1'}

        request = self._createRequest(env, '')
        location = request.response.redirect('http://foobar.com/redirected')
        self.assertEquals(request.response.getStatus(), 303)

        # test explicit status
        request = self._createRequest(env, '')
        request.response.redirect('http://foobar.com/explicit', 304)
        self.assertEquals(request.response.getStatus(), 304)

    def testRequestEnvironment(self):
        req = self._createRequest()
        publish(req, handle_errors=0) # Force expansion of URL variables

        self.assertEquals(str(req.URL), 'http://foobar.com/folder/item')
        self.assertEquals(req.URL['-1'], 'http://foobar.com/folder')
        self.assertEquals(req.URL['-2'], 'http://foobar.com')
        self.assertRaises(KeyError, req.URL.__getitem__, '-3')

        self.assertEquals(req.URL['0'], 'http://foobar.com')
        self.assertEquals(req.URL['1'], 'http://foobar.com/folder')
        self.assertEquals(req.URL['2'], 'http://foobar.com/folder/item')
        self.assertRaises(KeyError, req.URL.__getitem__, '3')

        self.assertEquals(req.URL.get('0'), 'http://foobar.com')
        self.assertEquals(req.URL.get('1'), 'http://foobar.com/folder')
        self.assertEquals(req.URL.get('2'), 'http://foobar.com/folder/item')
        self.assertEquals(req.URL.get('3', 'none'), 'none')

        self.assertEquals(req['SERVER_URL'], 'http://foobar.com')
        self.assertEquals(req['HTTP_HOST'], 'foobar.com')
        self.assertEquals(req['PATH_INFO'], '/folder/item')
        self.assertEquals(req['CONTENT_LENGTH'], '0')
        self.assertRaises(KeyError, req.__getitem__, 'HTTP_AUTHORIZATION')
        self.assertEquals(req['GATEWAY_INTERFACE'], 'TestFooInterface/1.0')
        self.assertEquals(req['HTTP_OFF_THE_WALL'], "Spam 'n eggs")

        self.assertRaises(KeyError, req.__getitem__,
                          'HTTP_WE_DID_NOT_PROVIDE_THIS')

    def testRequestLocale(self):
        eq = self.assertEqual
        unless = self.failUnless

        from zope.component import provideAdapter
        from zope.publisher.browser import BrowserLanguages
        from zope.publisher.interfaces.http import IHTTPRequest
        from zope.i18n.interfaces import IUserPreferredLanguages
        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)

        for httplang in ('it', 'it-ch', 'it-CH', 'IT', 'IT-CH', 'IT-ch'):
            req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': httplang})
            locale = req.locale
            unless(ILocale.providedBy(locale))
            parts = httplang.split('-')
            lang = parts.pop(0).lower()
            territory = variant = None
            if parts:
                territory = parts.pop(0).upper()
            if parts:
                variant = parts.pop(0).upper()
            eq(locale.id.language, lang)
            eq(locale.id.territory, territory)
            eq(locale.id.variant, variant)
        # Now test for non-existant locale fallback
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx'})
        locale = req.locale
        unless(ILocale.providedBy(locale))
        eq(locale.id.language, None)
        eq(locale.id.territory, None)
        eq(locale.id.variant, None)

        # If the first language is not available we should try others
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx,en;q=0.5'})
        locale = req.locale
        unless(ILocale.providedBy(locale))
        eq(locale.id.language, 'en')
        eq(locale.id.territory, None)
        eq(locale.id.variant, None)

        # Regression test: there was a bug where territory and variant were
        # not reset
        req = self._createRequest({'HTTP_ACCEPT_LANGUAGE': 'xx-YY,en;q=0.5'})
        locale = req.locale
        unless(ILocale.providedBy(locale))
        eq(locale.id.language, 'en')
        eq(locale.id.territory, None)
        eq(locale.id.variant, None)

        from zope.component.testing import tearDown
        tearDown()

    def testCookies(self):
        cookies = {
            'HTTP_COOKIE':
                'foo=bar; path=/; spam="eggs", this="Should be accepted"'
        }
        req = self._createRequest(extra_env=cookies)

        self.assertEquals(req.cookies[u'foo'], u'bar')
        self.assertEquals(req[u'foo'], u'bar')

        self.assertEquals(req.cookies[u'spam'], u'eggs')
        self.assertEquals(req[u'spam'], u'eggs')

        self.assertEquals(req.cookies[u'this'], u'Should be accepted')
        self.assertEquals(req[u'this'], u'Should be accepted')

        # Reserved key
        self.failIf(req.cookies.has_key('path'))

    def testCookieErrorToLog(self):
        cookies = {
            'HTTP_COOKIE':
                'foo=bar; path=/; spam="eggs", ldap/OU="Williams"'
        }
        req = self._createRequest(extra_env=cookies)

        self.failIf(req.cookies.has_key('foo'))
        self.failIf(req.has_key('foo'))

        self.failIf(req.cookies.has_key('spam'))
        self.failIf(req.has_key('spam'))

        self.failIf(req.cookies.has_key('ldap/OU'))
        self.failIf(req.has_key('ldap/OU'))

        # Reserved key
        self.failIf(req.cookies.has_key('path'))

    def testCookiesUnicode(self):
        # Cookie values are assumed to be UTF-8 encoded
        cookies = {'HTTP_COOKIE': r'key="\342\230\243";'}
        req = self._createRequest(extra_env=cookies)
        self.assertEquals(req.cookies[u'key'], u'\N{BIOHAZARD SIGN}')

    def testHeaders(self):
        headers = {
            'TEST_HEADER': 'test',
            'Another-Test': 'another',
        }
        req = self._createRequest(extra_env=headers)
        self.assertEquals(req.headers[u'TEST_HEADER'], u'test')
        self.assertEquals(req.headers[u'TEST-HEADER'], u'test')
        self.assertEquals(req.headers[u'test_header'], u'test')
        self.assertEquals(req.getHeader('TEST_HEADER', literal=True), u'test')
        self.assertEquals(req.getHeader('TEST-HEADER', literal=True), None)
        self.assertEquals(req.getHeader('test_header', literal=True), None)
        self.assertEquals(req.getHeader('Another-Test', literal=True),
                          'another')

    def testBasicAuth(self):
        from zope.publisher.interfaces.http import IHTTPCredentials
        req = self._createRequest()
        verifyObject(IHTTPCredentials, req)
        lpq = req._authUserPW()
        self.assertEquals(lpq, None)
        env = {}
        login, password = ("tim", "123:456")
        s = ("%s:%s" % (login, password)).encode("base64").rstrip()
        env['HTTP_AUTHORIZATION'] = "Basic %s" % s
        req = self._createRequest(env)
        lpw = req._authUserPW()
        self.assertEquals(lpw, (login, password))

    def testSetPrincipal(self):
        req = self._createRequest()
        req.setPrincipal(UserStub("jim"))
        self.assertEquals(req.response.authUser, 'jim')

    def test_method(self):
        r = self._createRequest(extra_env={'REQUEST_METHOD':'SPAM'})
        self.assertEqual(r.method, 'SPAM')
        r = self._createRequest(extra_env={'REQUEST_METHOD':'eggs'})
        self.assertEqual(r.method, 'EGGS')

    def test_setApplicationServer(self):
        events = []
        zope.event.subscribers.append(events.append)
        req = self._createRequest()
        req.setApplicationServer('foo')
        self.assertEquals(req._app_server, 'http://foo')
        req.setApplicationServer('foo', proto='https')
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', proto='https', port=8080)
        self.assertEquals(req._app_server, 'https://foo:8080')
        req.setApplicationServer('foo', proto='http', port='9673')
        self.assertEquals(req._app_server, 'http://foo:9673')
        req.setApplicationServer('foo', proto='https', port=443)
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', proto='https', port='443')
        self.assertEquals(req._app_server, 'https://foo')
        req.setApplicationServer('foo', port=80)
        self.assertEquals(req._app_server, 'http://foo')
        req.setApplicationServer('foo', proto='telnet', port=80)
        self.assertEquals(req._app_server, 'telnet://foo:80')
        zope.event.subscribers.pop()
        self.assertEquals(len(events), 8)
        for event in events:
            self.assertEquals(event.request, req)

    def test_setApplicationNames(self):
        events = []
        zope.event.subscribers.append(events.append)
        req = self._createRequest()
        names = ['x', 'y', 'z']
        req.setVirtualHostRoot(names)
        self.assertEquals(req._app_names, ['x', 'y', 'z'])
        names[0] = 'muahahahaha'
        self.assertEquals(req._app_names, ['x', 'y', 'z'])
        zope.event.subscribers.pop()
        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].request, req)

    def test_setVirtualHostRoot(self):
        events = []
        zope.event.subscribers.append(events.append)
        req = self._createRequest()
        req._traversed_names = ['x', 'y']
        req._last_obj_traversed = object()
        req.setVirtualHostRoot()
        self.failIf(req._traversed_names)
        self.assertEquals(req._vh_root, req._last_obj_traversed)
        zope.event.subscribers.pop()
        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].request, req)

    def test_getVirtualHostRoot(self):
        req = self._createRequest()
        self.assertEquals(req.getVirtualHostRoot(), None)
        req._vh_root = object()
        self.assertEquals(req.getVirtualHostRoot(), req._vh_root)

    def test_traverse(self):
        req = self._createRequest()
        req.traverse(self.app)
        self.assertEquals(req._traversed_names, ['folder', 'item'])

        # setting it during traversal matters
        req = self._createRequest()
        def hook(self, object, req=req, app=self.app):
            if object is app.folder:
                req.setVirtualHostRoot()
        req.publication.callTraversalHooks = hook
        req.traverse(self.app)
        self.assertEquals(req._traversed_names, ['item'])
        self.assertEquals(req._vh_root, self.app.folder)

    def testInterface(self):
        from zope.publisher.interfaces.http import IHTTPCredentials
        from zope.publisher.interfaces.http import IHTTPApplicationRequest
        rq = self._createRequest()
        verifyObject(IHTTPRequest, rq)
        verifyObject(IHTTPCredentials, rq)
        verifyObject(IHTTPApplicationRequest, rq)

    def testDeduceServerURL(self):
        req = self._createRequest()
        deduceServerURL = req._HTTPRequest__deduceServerURL
        req._environ = {'HTTP_HOST': 'example.com:80'}
        self.assertEquals(deduceServerURL(), 'http://example.com')
        req._environ = {'HTTP_HOST': 'example.com:8080'}
        self.assertEquals(deduceServerURL(), 'http://example.com:8080')
        req._environ = {'HTTP_HOST': 'example.com:443', 'HTTPS': 'on'}
        self.assertEquals(deduceServerURL(), 'https://example.com')
        req._environ = {'HTTP_HOST': 'example.com:80', 'HTTPS': 'ON'}
        self.assertEquals(deduceServerURL(), 'https://example.com:80')
        req._environ = {'HTTP_HOST': 'example.com:8080',
                        'SERVER_PORT_SECURE': '1'}
        self.assertEquals(deduceServerURL(), 'https://example.com:8080')
        req._environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT':'8080',
                        'SERVER_PORT_SECURE': '0'}
        self.assertEquals(deduceServerURL(), 'http://example.com:8080')
        req._environ = {'SERVER_NAME': 'example.com'}
        self.assertEquals(deduceServerURL(), 'http://example.com')

    def testUnicodeURLs(self):
        # The request expects PATH_INFO to be utf-8 encoded when it gets it.
        req = self._createRequest(
            {'PATH_INFO': '/\xc3\xa4\xc3\xb6/\xc3\xbc\xc3\x9f/foo/bar.html'})
        self.assertEqual(req._traversal_stack,
                         [u'bar.html', u'foo', u'üß', u'äö'])
        # the request should have converted PATH_INFO to unicode
        self.assertEqual(req['PATH_INFO'], u'/äö/üß/foo/bar.html')

    def testResponseWriteFaile(self):
        self.assertRaises(TypeError,
                          self._createRequest().response.write,
                          'some output',
                          )

class ConcreteHTTPTests(HTTPTests):
    """Tests that we don't have to worry about subclasses inheriting and
    breaking.
    """

    def test_shiftNameToApplication(self):
        r = self._createRequest()
        publish(r, handle_errors=0)
        appurl = r.getApplicationURL()

        # Verify that we can shift. It would be a little more realistic
        # if we could test this during traversal, but the api doesn't
        # let us do that.
        r = self._createRequest(extra_env={"PATH_INFO": "/xxx"})
        publish(r, handle_errors=0)
        r.shiftNameToApplication()
        self.assertEquals(r.getApplicationURL(), appurl+"/xxx")

        # Verify that we can only shift if we've traversed only a single name
        r = self._createRequest(extra_env={"PATH_INFO": "/folder/item"})
        publish(r, handle_errors=0)
        self.assertRaises(ValueError, r.shiftNameToApplication)



class TestHTTPResponse(unittest.TestCase):

    def testInterface(self):
        rp = HTTPResponse()
        verifyObject(IHTTPResponse, rp)
        verifyObject(IHTTPApplicationResponse, rp)
        verifyObject(IResponse, rp)

    def _createResponse(self):
        response = HTTPResponse()
        return response

    def _parseResult(self, response):
        return dict(response.getHeaders()), ''.join(response.consumeBody())

    def _getResultFromResponse(self, body, charset='utf-8', headers=None):
        response = self._createResponse()
        assert(charset == 'utf-8')
        if headers is not None:
            for hdr, val in headers.iteritems():
                response.setHeader(hdr, val)
        response.setResult(body)
        return self._parseResult(response)

    def testWrite_noContentLength(self):
        response = self._createResponse()
        # We have to set all the headers ourself, we choose not to provide a
        # content-length header
        response.setHeader('Content-Type', 'text/plain;charset=us-ascii')

        # Output the data
        data = 'a'*10
        response.setResult(StrResult(data))

        headers, body = self._parseResult(response)
        # Check that the data have been written, and that the header
        # has been preserved
        self.assertEqual(headers['Content-Type'], 'text/plain;charset=us-ascii')
        self.assertEqual(body, data)

        # Make sure that no Content-Length header was added
        self.assert_('Content-Length' not in headers)

    def testContentLength(self):
        eq = self.failUnlessEqual

        headers, body = self._getResultFromResponse("test", "utf-8",
            {"content-type": "text/plain"})
        eq("4", headers["Content-Length"])
        eq("test", body)

        headers, body = self._getResultFromResponse(
            u'\u0442\u0435\u0441\u0442', "utf-8",
            {"content-type": "text/plain"})
        eq("8", headers["Content-Length"])
        eq('\xd1\x82\xd0\xb5\xd1\x81\xd1\x82', body)

    def testContentType(self):
        eq = self.failUnlessEqual

        headers, body = self._getResultFromResponse("test", "utf-8")
        eq("", headers.get("Content-Type", ""))
        eq("test", body)

        headers, body = self._getResultFromResponse(u"test",
            headers={"content-type": "text/plain"})
        eq("text/plain;charset=utf-8", headers["Content-Type"])
        eq("test", body)

        headers, body = self._getResultFromResponse(u"test", "utf-8",
            {"content-type": "text/html"})
        eq("text/html;charset=utf-8", headers["Content-Type"])
        eq("test", body)

        headers, body = self._getResultFromResponse(u"test", "utf-8",
            {"content-type": "text/plain;charset=cp1251"})
        eq("text/plain;charset=cp1251", headers["Content-Type"])
        eq("test", body)

        headers, body = self._getResultFromResponse("test", "utf-8",
            {"content-type": "image/gif"})
        eq("image/gif", headers["Content-Type"])
        eq("test", body)

    def _getCookieFromResponse(self, cookies):
        # Shove the cookies through request, parse the Set-Cookie header
        # and spit out a list of headers for examination
        response = self._createResponse()
        for name, value, kw in cookies:
            response.setCookie(name, value, **kw)
        response.setResult('test')
        return [header[1]
                for header in response.getHeaders()
                if header[0] == "Set-Cookie"]

    def testSetCookie(self):
        c = self._getCookieFromResponse([
                ('foo', 'bar', {}),
                ])
        self.failUnless('foo=bar;' in c, 'foo=bar; not in %r' % c)

        c = self._getCookieFromResponse([
                ('foo', 'bar', {}),
                ('alpha', 'beta', {}),
                ])
        self.failUnless('foo=bar;' in c)
        self.failUnless('alpha=beta;' in c)

        c = self._getCookieFromResponse([
                ('sign', u'\N{BIOHAZARD SIGN}', {}),
                ])
        self.failUnless(r'sign="\342\230\243";' in c)

        self.assertRaises(
                CookieError,
                self._getCookieFromResponse,
                [('path', 'invalid key', {}),]
                )

        c = self._getCookieFromResponse([
                ('foo', 'bar', {
                    'Expires': 'Sat, 12 Jul 2014 23:26:28 GMT',
                    'domain': 'example.com',
                    'pAth': '/froboz',
                    'max_age': 3600,
                    'comment': u'blah;\N{BIOHAZARD SIGN}?',
                    'seCure': True,
                    }),
                ])[0]
        self.failUnless('foo=bar;' in c)
        self.failUnless('expires=Sat, 12 Jul 2014 23:26:28 GMT;' in c, repr(c))
        self.failUnless('Domain=example.com;' in c)
        self.failUnless('Path=/froboz;' in c)
        self.failUnless('Max-Age=3600;' in c)
        self.failUnless('Comment=blah%3B%E2%98%A3?;' in c, repr(c))
        self.failUnless('secure;' in c)

        c = self._getCookieFromResponse([('foo', 'bar', {'secure': False})])[0]
        self.failUnless('foo=bar;' in c)
        self.failIf('secure' in c)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConcreteHTTPTests))
    suite.addTest(unittest.makeSuite(TestHTTPResponse))
    suite.addTest(unittest.makeSuite(HTTPInputStreamTests))
    return suite


if __name__ == '__main__':
    unittest.main()

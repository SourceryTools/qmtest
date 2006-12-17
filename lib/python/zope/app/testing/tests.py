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
"""Test tcpdoc

$Id$
"""
import os
import unittest
import StringIO

from zope.testing.doctestunit import DocTestSuite

import zope.app.testing
from zope.app.publication.requestpublicationregistry import factoryRegistry
from zope.app.publication.requestpublicationfactories import BrowserFactory
from zope.app.testing import functional
from zope.app.testing.dochttp import dochttp

HEADERS = """\
HTTP/1.1 200 Ok
Content-Type: text/plain
"""

BODY = """\
This is the response body.
"""

directory = os.path.join(os.path.split(zope.app.testing.__file__)[0],
                         'recorded')

expected = r'''

  >>> print http(r"""
  ... GET /@@contents.html HTTP/1.1
  ... """)
  HTTP/1.1 401 Unauthorized
  Content-Length: 89
  Content-Type: text/html;charset=utf-8
  Www-Authenticate: basic realm="Zope"
  <BLANKLINE>
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
        lang="en">
  <BLANKLINE>
  ...
  <BLANKLINE>
  </html>
  <BLANKLINE>
  <BLANKLINE>


  >>> print http(r"""
  ... GET /@@contents.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... """)
  HTTP/1.1 200 Ok
  Content-Length: 89
  Content-Type: text/html;charset=utf-8
  <BLANKLINE>
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
        lang="en">
  <BLANKLINE>
  ...
  <BLANKLINE>
  </html>
  <BLANKLINE>
  <BLANKLINE>


  >>> print http(r"""
  ... GET /++etc++site/@@manage HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Referer: http://localhost:8081/
  ... """)
  HTTP/1.1 303 See Other
  Content-Length: 0
  Content-Type: text/plain;charset=utf-8
  Location: @@tasks.html
  <BLANKLINE>


  >>> print http(r"""
  ... GET / HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... """)
  HTTP/1.1 200 Ok
  Content-Length: 89
  Content-Type: text/html;charset=utf-8
  <BLANKLINE>
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
        lang="en">
  <BLANKLINE>
  ...
  <BLANKLINE>
  </html>
  <BLANKLINE>
  <BLANKLINE>


  >>> print http(r"""
  ... GET /++etc++site/@@tasks.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Referer: http://localhost:8081/
  ... """)
  HTTP/1.1 200 Ok
  Content-Length: 89
  Content-Type: text/html;charset=utf-8
  <BLANKLINE>
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
        lang="en">
  <BLANKLINE>
  ...
  <BLANKLINE>
  </html>
  <BLANKLINE>
  <BLANKLINE>
'''

class FunctionalHTTPDocTest(unittest.TestCase):

    def test_dochttp(self):
        import sys, StringIO
        old = sys.stdout
        sys.stdout = StringIO.StringIO()
        dochttp(['-p', 'test', directory])
        got = sys.stdout.getvalue()
        sys.stdout = old
        self.assertEquals(expected, got)


class AuthHeaderTestCase(unittest.TestCase):

    def test_auth_encoded(self):
        auth_header = functional.auth_header
        header = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEquals(auth_header(header), header)

    def test_auth_non_encoded(self):
        auth_header = functional.auth_header
        header = 'Basic globalmgr:globalmgrpw'
        expected = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEquals(auth_header(header), expected)

    def test_auth_non_encoded_empty(self):
        auth_header = functional.auth_header
        header = 'Basic globalmgr:'
        expected = 'Basic Z2xvYmFsbWdyOg=='
        self.assertEquals(auth_header(header), expected)
        header = 'Basic :pass'
        expected = 'Basic OnBhc3M='
        self.assertEquals(auth_header(header), expected)

    def test_auth_non_encoded_colon(self):
        auth_header = zope.app.testing.functional.auth_header
        header = 'Basic globalmgr:pass:pass'
        expected = 'Basic Z2xvYmFsbWdyOnBhc3M6cGFzcw=='
        self.assertEquals(auth_header(header), expected)


class HTTPCallerTestCase(unittest.TestCase):

    def test_chooseRequestClass(self):
        from zope.publisher.interfaces import IRequest, IPublication

        factoryRegistry.register('GET', '*', 'browser', 0, BrowserFactory())

        caller = functional.HTTPCaller()
        request_class, publication_class = caller.chooseRequestClass(
            method='GET', path='/', environment={})

        self.assert_(IRequest.implementedBy(request_class))
        self.assert_(IPublication.implementedBy(publication_class))

class DummyCookiesResponse(object):
    # Ugh, this simulates the *internals* of a HTTPResponse object
    # TODO: expand the IHTTPResponse interface to give access to all cookies
    _cookies = None
    
    def __init__(self, cookies=None):
        if not cookies:
            cookies = {}
        self._cookies = cookies
        
class CookieHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.handler = functional.CookieHandler()
    
    def test_saveCookies(self):
        response = DummyCookiesResponse(dict(
            spam=dict(value='eggs', path='/foo', comment='rest is ignored'),
            monty=dict(value='python')))
        self.handler.saveCookies(response)
        self.assertEqual(len(self.handler.cookies), 2)
        self.assertEqual(self.handler.cookies['spam'].OutputString(),
                         'spam=eggs; Path=/foo;')
        self.assertEqual(self.handler.cookies['monty'].OutputString(),
                         'monty=python;')
        
    def test_httpCookie(self):
        cookies = self.handler.cookies
        cookies['spam'] = 'eggs'
        cookies['spam']['path'] = '/foo'
        cookies['bar'] = 'baz'
        cookies['bar']['path'] = '/foo/baz'
        cookies['monty'] = 'python'
        
        cookieHeader = self.handler.httpCookie('/foo/bar')
        parts = cookieHeader.split('; ')
        parts.sort()
        self.assertEqual(parts, ['monty=python', 'spam=eggs'])
        
        cookieHeader = self.handler.httpCookie('/foo/baz')
        parts = cookieHeader.split('; ')
        parts.sort()
        self.assertEqual(parts, ['bar=baz', 'monty=python', 'spam=eggs'])
        
    # There is no test for CookieHandler.loadCookies because it that method
    # only passes the arguments on to Cookie.BaseCookie.load, which the 
    # standard library has tests for (we hope).

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FunctionalHTTPDocTest),
        unittest.makeSuite(AuthHeaderTestCase),
        unittest.makeSuite(HTTPCallerTestCase),
        unittest.makeSuite(CookieHandlerTestCase),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


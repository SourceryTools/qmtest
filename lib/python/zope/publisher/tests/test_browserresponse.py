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
"""Browser response tests

$Id: test_browserresponse.py 78269 2007-07-21 15:54:41Z nikhil_n $
"""

import sys
from unittest import TestCase, TestSuite, main, makeSuite
from zope.publisher.browser import BrowserResponse
from zope.interface.verify import verifyObject

from zope.publisher.interfaces.http import IHTTPResponse
from zope.publisher.interfaces.http import IHTTPApplicationResponse
from zope.publisher.interfaces import IResponse


# TODO: Waaa need more tests

class TestBrowserResponse(TestCase):

    def test_contentType_DWIM_in_setResult(self):
        response = BrowserResponse()
        response.setResult(
            """<html>
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse()
        response.setResult(
            """<html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse()
        response.setResult(
            """<html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse()
        response.setResult(
            """<!doctype html>
            <html foo="1"
            bar="x">
            <blah>
            </html>
            """)
        self.assert_(response.getHeader('content-type').startswith("text/html")
                     )

        response = BrowserResponse()
        response.setResult(
            """Hello world
            """)
        self.assert_(response.getHeader('content-type').startswith(
            "text/plain")
                     )

        response = BrowserResponse()
        response.setResult(
            """<p>Hello world
            """)
        self.assert_(
            response.getHeader('content-type').startswith("text/plain")
            )


    def testInsertBase(self):
        response = BrowserResponse()
        response.setHeader('content-type', 'text/html')

        insertBase = response._BrowserResponse__insertBase

        # Make sure that bases are inserted
        response.setBase('http://localhost/folder/')
        self.assert_(
            '<base href="http://localhost/folder/" />' in
            insertBase('<html><head></head><body>Page</body></html>'))

        # Ensure that unicode bases work as well
        response.setBase(u'http://localhost/folder/')
        body = insertBase('<html><head></head><body>Page</body></html>')
        self.assert_(isinstance(body, str))
        self.assert_('<base href="http://localhost/folder/" />' in body)

        # Ensure that encoded bodies work, when a base is inserted.
        response.setBase('http://localhost/folder')
        result = insertBase(
            '<html><head></head><body>\xc3\x9bung</body></html>')
        self.assert_(isinstance(body, str))
        self.assert_('<base href="http://localhost/folder" />' in result)

    def testInsertBaseInSetResultUpdatesContentLength(self):
        # Make sure that the Content-Length header is updated to account
        # for an inserted <base> tag.
        response = BrowserResponse()
        response.setHeader('content-type', 'text/html')
        base = 'http://localhost/folder/'
        response.setBase(base)
        inserted_text = '\n<base href="%s" />\n' % base
        html_page = """<html>
            <head></head>
            <blah>
            </html>
            """
        response.setResult(html_page)
        self.assertEquals(
            int(response.getHeader('content-length')),
            len(html_page) + len(inserted_text))

    def test_interface(self):
        rp = BrowserResponse()
        verifyObject(IHTTPResponse, rp)
        verifyObject(IHTTPApplicationResponse, rp)
        verifyObject(IResponse, rp)

    def test_handleException(self):
        response = BrowserResponse()
        try:
            raise ValueError(1)
        except:
            exc_info = sys.exc_info()

        response.handleException(exc_info)
        self.assertEquals(response.getHeader("content-type"),
            "text/html;charset=utf-8")
        self.assertEquals(response.getStatus(), 500)
        self.assert_(response.consumeBody() in
            ["<html><head><title>&lt;type 'exceptions.ValueError'&gt;</title></head>\n"
            "<body><h2>&lt;type 'exceptions.ValueError'&gt;</h2>\n"
            "A server error occurred.\n"
            "</body></html>\n",
            "<html><head><title>ValueError</title></head>\n"
            "<body><h2>ValueError</h2>\n"
            "A server error occurred.\n"
            "</body></html>\n"]
            )


def test_suite():
    return TestSuite((
        makeSuite(TestBrowserResponse),
        ))


if __name__=='__main__':
    main(defaultTest='test_suite')

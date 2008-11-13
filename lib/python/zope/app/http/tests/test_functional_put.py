##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Test HTTP PUT verb

$Id: test_functional_put.py 81052 2007-10-24 19:16:25Z srichter $
"""

from unittest import TestSuite, makeSuite

from zope.app.testing.functional import FunctionalTestCase, HTTPCaller
from zope.app.http.testing import AppHttpLayer

class TestPUT(FunctionalTestCase):
    def test_put(self):
        # PUT something for the first time
        response = HTTPCaller()(r"""PUT /testfile.txt HTTP/1.1
Authorization: Basic bWdyOm1ncnB3
Content-Length: 20
Content-Type: text/plain

This is just a test.""")
        self.assertEquals(response._response.getStatus(), 201)
        self.assertEquals(response._response.getHeader("Location"),
                          "http://localhost/testfile.txt")

        response = HTTPCaller()(r"""GET /testfile.txt HTTP/1.1
Authorization: Basic bWdyOm1ncnB3""")
        self.assertEquals(response.getBody(), "This is just a test.")

        # now modify it
        response = HTTPCaller()(r"""PUT /testfile.txt HTTP/1.1
Authorization: Basic bWdyOm1ncnB3
Content-Length: 22
Content-Type: text/plain

And now it is modified.""")
        self.assertEquals(response._response.getStatus(), 200)
        self.assertEquals(response.getBody(), "")

        response = HTTPCaller()(r"""GET /testfile.txt HTTP/1.1
Authorization: Basic bWdyOm1ncnB3""")
        self.assertEquals(response.getBody(), "And now it is modified.")
        
        
def test_suite():
    TestPUT.layer = AppHttpLayer
    return TestSuite((
        makeSuite(TestPUT),
        ))

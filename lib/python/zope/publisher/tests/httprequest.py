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
"""Test request for writing tests that need HTTP requests.

Note that this is used by tests in other packages.

$Id: httprequest.py 38357 2005-09-07 20:14:34Z srichter $
"""

from StringIO import StringIO

from zope.publisher.http import HTTPRequest

_testEnv =  {
    'SERVER_URL':         'http://foobar.com',
    'HTTP_HOST':          'foobar.com',
    'CONTENT_LENGTH':     '0',
    'GATEWAY_INTERFACE':  'Test/1.0',
}

class TestRequest(HTTPRequest):

    def __init__(self, body_instream=None, environ=None, **kw):
        if body_instream is None:
            body_instream = StringIO('')

        env = {}
        env.update(_testEnv)
        if environ: env.update(environ)
        env.update(kw)

        super(TestRequest, self).__init__(body_instream, env)

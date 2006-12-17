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
"""URLQuote Tests

I kept the tests quite small, just covering that the functions actually do
something (and don't really scramble stuff). We are relying on the python urllib
to be functional to avoid test duplication.

$Id: test_urlquote.py 27274 2004-08-26 12:09:15Z BjornT $
"""

import unittest

from zope.testing.doctestunit import DocTestSuite
from zope.app.pagetemplate.urlquote import URLQuote


class TestObject(object):

    def __str__(self):
        return "www.google.de"

def quote_simple():
    """
    >>> q = URLQuote(u"www.google.de")
    >>> q.quote()
    'www.google.de'
    >>> q.unquote()
    u'www.google.de'
    >>> q.quote_plus()
    'www.google.de'
    >>> q.unquote_plus()
    u'www.google.de'
    """

def quote_cast_needed():
    """
    >>> q = URLQuote(TestObject())
    >>> q.quote()
    'www.google.de'
    >>> q.unquote()
    u'www.google.de'
    >>> q.quote_plus()
    'www.google.de'
    >>> q.unquote_plus()
    u'www.google.de'
    """

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        DocTestSuite('zope.app.pagetemplate.urlquote'),
        ))

if __name__ == '__main__':
    unittest.main()

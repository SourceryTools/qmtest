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
"""WSGI tests

$Id: tests.py 41673 2006-02-18 20:49:44Z benji_york $
"""
import tempfile
import unittest

from zope import component, interface
from zope.testing import doctest

import zope.app.testing.functional
import zope.publisher.interfaces.browser
from zope.app.testing import placelesssetup
from zope.app.publication.requestpublicationregistry import factoryRegistry
from zope.app.publication.requestpublicationfactories import BrowserFactory

def setUp(test):
    placelesssetup.setUp(test)
    factoryRegistry.register('GET', '*', 'browser', 0, BrowserFactory())



class FileView:

    interface.implements(zope.publisher.interfaces.browser.IBrowserPublisher)
    component.adapts(interface.Interface,
                     zope.publisher.interfaces.browser.IBrowserRequest)

    def __init__(self, _, request):
        self.request = request

    def browserDefault(self, *_):
        return self, ()

    def __call__(self):
        self.request.response.setHeader('content-type', 'text/plain')
        f = tempfile.TemporaryFile()
        f.write("Hello\nWorld!\n")
        return f


def test_file_returns():
    """We want to make sure that file returns work

Let's register a view that returns a temporary file and make sure that
nothing bad happens. :)

    >>> component.provideAdapter(FileView, name='test-file-view.html')
    >>> from zope.security import checker
    >>> checker.defineChecker(
    ...     FileView,
    ...     checker.NamesChecker(['browserDefault', '__call__']),
    ...     )

    >>> from zope.testbrowser.testing import Browser
    >>> browser = Browser()
    >>> browser.handleErrors = False
    >>> browser.open('http://localhost/@@test-file-view.html')
    >>> browser.headers['content-type']
    'text/plain'

    >>> browser.headers['content-length']
    '13'

    >>> print browser.contents
    Hello
    World!
    <BLANKLINE>

Clean up:

    >>> checker.undefineChecker(FileView)
    >>> component.provideAdapter(
    ...     None,
    ...     (interface.Interface,
    ...      zope.publisher.interfaces.browser.IBrowserRequest),
    ...     zope.publisher.interfaces.browser.IBrowserPublisher,
    ...     'test-file-view.html',
    ...     )


"""

def test_suite():

    functional_suite = doctest.DocTestSuite()
    functional_suite.layer = zope.app.testing.functional.Functional

    return unittest.TestSuite((
        functional_suite,
        doctest.DocFileSuite(
            'README.txt', 'fileresult.txt',
            setUp=setUp,
            tearDown=placelesssetup.tearDown,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

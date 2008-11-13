##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Functional tests for xmlrpc

$Id: test_functional.py 73560 2007-03-25 09:38:45Z fdrake $
"""
import re

import zope.component
import zope.interface
import zope.publisher.interfaces.xmlrpc
from zope.testing import renormalizing

import zope.app.folder.folder
from zope.app.testing import functional, setup
from zope.app.publisher.testing import AppPublisherLayer

def setUp(test):
    setup.setUpTestAsModule(test, 'zope.app.publisher.xmlrpc.README')

def tearDown(test):
    # clean up the views we registered:
    
    # we use the fact that registering None unregisters whatever is
    # registered. We can't use an unregistration call because that
    # requires the object that was registered and we don't have that handy.
    # (OK, we could get it if we want. Maybe later.)

    zope.component.provideAdapter(None, (
        zope.app.folder.folder.IFolder,
        zope.publisher.interfaces.xmlrpc.IXMLRPCRequest
        ), zope.interface, 'contents')

    setup.tearDownTestAsModule(test)

def test_suite():
    checker = renormalizing.RENormalizing((
        (re.compile('<DateTime \''), '<DateTime u\''),
        (re.compile('at [-0-9a-fA-F]+'), 'at <SOME ADDRESS>'),
        ))
    suite = functional.FunctionalDocFileSuite(
        '../README.txt', setUp=setUp, tearDown=tearDown,
        checker=checker
        )
    suite.layer = AppPublisherLayer
    return suite

if __name__ == '__main__':
    import unittest
    unittest.main(defaultTest='test_suite')

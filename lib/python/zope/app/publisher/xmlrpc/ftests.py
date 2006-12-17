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

$Id: ftests.py 29787 2005-04-01 16:41:05Z srichter $
"""
import zope.interface
import zope.app.folder.folder
import zope.publisher.interfaces.xmlrpc
from zope.app.testing import ztapi, functional, setup

def setUp(test):
    setup.setUpTestAsModule(test, 'zope.app.publisher.xmlrpc.README')

def tearDown(test):
    # clean up the views we registered:
    
    # we use the fact that registering None unregisters whatever is
    # registered. We can't use an unregistration call because that
    # requires the object that was registered and we don't have that handy.
    # (OK, we could get it if we want. Maybe later.)

    ztapi.provideView(zope.app.folder.folder.IFolder,
                        zope.publisher.interfaces.xmlrpc.IXMLRPCRequest,
                        zope.interface,
                        'contents',
                        None,
                        )
    ztapi.provideView(zope.app.folder.folder.IFolder,
                        zope.publisher.interfaces.xmlrpc.IXMLRPCRequest,
                        zope.interface,
                        'contents',
                        None,
                        )
    
    setup.tearDownTestAsModule(test)

def test_suite():
    return functional.FunctionalDocFileSuite(
        'README.txt', setUp=setUp, tearDown=tearDown)

if __name__ == '__main__':
    import unittest
    unittest.main(defaultTest='test_suite')

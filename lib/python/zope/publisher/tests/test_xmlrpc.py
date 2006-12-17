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
"""Testing the XML-RPC Publisher code.

$Id: test_xmlrpc.py 69027 2006-07-07 14:39:18Z philikon $
"""
import xmlrpclib
import zope.component.testing
from zope.testing import doctest
from zope.publisher import xmlrpc
from zope.security.checker import defineChecker, Checker, CheckerPublic

def setUp(test):
    zope.component.testing.setUp(test)
    zope.component.provideAdapter(xmlrpc.ListPreMarshaller)
    zope.component.provideAdapter(xmlrpc.TuplePreMarshaller)
    zope.component.provideAdapter(xmlrpc.FaultPreMarshaller)
    zope.component.provideAdapter(xmlrpc.DateTimePreMarshaller)
    zope.component.provideAdapter(xmlrpc.PythonDateTimePreMarshaller)
    zope.component.provideAdapter(xmlrpc.DictPreMarshaller)

    defineChecker(xmlrpclib.Fault,
                  Checker({'faultCode':CheckerPublic,
                           'faultString': CheckerPublic}, {}))
    defineChecker(xmlrpclib.DateTime,
                  Checker({'value':CheckerPublic}, {}))

def test_suite():
    return doctest.DocFileSuite( 
        "xmlrpc.txt", package="zope.publisher",
        setUp=setUp, tearDown=zope.component.testing.tearDown,
        optionflags=doctest.ELLIPSIS
        )

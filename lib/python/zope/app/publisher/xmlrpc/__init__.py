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
"""XML-RPC Publisher Components

This module contains the XMLRPCView.

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.interface
import zope.location
import zope.publisher.interfaces.xmlrpc
import zope.app.publisher.interfaces.xmlrpc

class XMLRPCView(object):
    """A base XML-RPC view that can be used as mix-in for XML-RPC views.""" 
    zope.interface.implements(zope.app.publisher.interfaces.xmlrpc.IXMLRPCView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

class IMethodPublisher(zope.interface.Interface):
    """Marker interface for an object that wants to publish methods
    """

# Need to test new __parent__ attribute
class MethodPublisher(XMLRPCView, zope.location.Location):
    """Base class for very simple XML-RPC views that publish methods

    This class is meant to be more of an example than a standard base class. 

    This example is explained in the README.txt file for this package
    """
    zope.interface.implements(IMethodPublisher)

    def __getParent(self):
        return hasattr(self, '_parent') and self._parent or self.context

    def __setParent(self, parent):
        self._parent = parent

    __parent__ = property(__getParent, __setParent)


class MethodTraverser(object):
    zope.interface.implements(
        zope.publisher.interfaces.xmlrpc.IXMLRPCPublisher)

    __used_for__ = IMethodPublisher

    def __init__(self, context, request):
        self.context = context
        
    def publishTraverse(self, request, name):
        return getattr(self.context, name)

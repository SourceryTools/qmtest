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
"""Publication Interfaces

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope import interface
import zope.component.interfaces

class IPublicationRequestFactory(interface.Interface):
    """Publication request factory"""

    def __call__(input_stream, output_steam, env):
        """Create a request object to handle the given inputs

        A request is created and configured with a publication object.
        """

class IBeforeTraverseEvent(zope.component.interfaces.IObjectEvent):
    """An event which gets sent on publication traverse"""

    request = interface.Attribute("The current request")

class BeforeTraverseEvent(object):
    """An event which gets sent on publication traverse"""

    interface.implements(IBeforeTraverseEvent)

    def __init__(self, ob, request):
        self.object = ob
        self.request = request


class IEndRequestEvent(interface.Interface):
    """An event which gets sent when the publication is ended"""


class EndRequestEvent(object):
    """An event which gets sent when the publication is ended"""

    interface.implements(IEndRequestEvent)

    def __init__(self, ob, request):
        self.object = ob
        self.request = request

class IRequestFactory(interface.Interface):

    def __call__(input_stream, output_steam, env):
        """Create a request object to handle input."""

class ISOAPRequestFactory(IRequestFactory):
    """SOAP request factory"""

class IHTTPRequestFactory(IRequestFactory):
    # TODO: should SOAP, XMLRPC, and Browser extend this?
    """generic HTTP request factory"""

class IXMLRPCRequestFactory(IRequestFactory):
    """XMLRPC request factory"""

class IBrowserRequestFactory(IRequestFactory):
    """Browser request factory"""

class IFileContent(interface.Interface):
    """Marker interface for content that can be managed as files.

    The default view for file content has effective URLs that don't end in
    `/`.  In particular, if the content included HTML, relative links in
    the HTML are relative to the container the content is in.
    """


class IRequestPublicationFactory(interface.Interface):
    """ request-publication factory """

    def canHandle(environment):
        """Return ``True`` if it can handle the request, otherwise ``False``.

        `environment` can be used by the factory to make a decision based on
        the HTTP headers.
        """

    def __call__():
        """Return a tuple (request, publication)"""

class IRequestPublicationRegistry(interface.Interface):
    """A registry to lookup a RequestPublicationFactory by
       request method + mime-type. Multiple factories can be configured
       for the same method+mimetype. The factory itself can introspect
       the environment to decide if it can handle the request as given
       by the environment or not. Factories are sorted in the order
       of their registration in ZCML.
    """

    def register(method, mimetype, name, priority, factory):
        """Registers a factory for method+mimetype."""

    def lookup(method, mimetype, environment):
        """Lookup a factory for a given method+mimetype and a
        environment.
        """

    def getFactoriesFor(method, mimetype):
        """Return the internal datastructure representing the configured
        factories (basically for testing, not for introspection).
        """

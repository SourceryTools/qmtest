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
"""HTTP Factory

$Id: httpfactory.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope import interface

from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import setDefaultSkin

from zope.app.publication import interfaces
from zope.app.publication.requestpublicationregistry import factoryRegistry


def chooseClasses(method, environment):
    """Given the method and environment, choose the correct request and
    publication factort."""
    content_type = environment.get('CONTENT_TYPE', '')
    factory = factoryRegistry.lookup(method, content_type, environment)
    request_class, publication = factory()
    return request_class, publication


class HTTPPublicationRequestFactory(object):
    interface.implements(interfaces.IPublicationRequestFactory)

    def __init__(self, db):
        """See `zope.app.publication.interfaces.IPublicationRequestFactory`"""
        self._db = db
        self._publication_cache = {}

    def __call__(self, input_stream, env, output_stream=None):
        """See `zope.app.publication.interfaces.IPublicationRequestFactory`"""
        # BBB: This is backward-compatibility support for the deprecated
        # output stream.
        try:
            env.get
        except AttributeError:
            import warnings
            warnings.warn("Can't pass output streams to requests anymore. "
                          "This will go away in Zope 3.4.",
                          DeprecationWarning,
                          2)
            env, output_stream = output_stream, env


        method = env.get('REQUEST_METHOD', 'GET').upper()
        request_class, publication_class = chooseClasses(method, env)

        publication = self._publication_cache.get(publication_class)
        if publication is None:
            publication = publication_class(self._db)
            self._publication_cache[publication_class] = publication

        request = request_class(input_stream, env)
        request.setPublication(publication)
        if IBrowserRequest.providedBy(request):
            # only browser requests have skins
            setDefaultSkin(request)
        return request

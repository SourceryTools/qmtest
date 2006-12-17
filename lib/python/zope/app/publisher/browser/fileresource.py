##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""File-based browser resources.

$Id: fileresource.py 67630 2006-04-27 00:54:03Z jim $
"""

import time
from zope.security.proxy import Proxy
from zope.interface import implements
from zope.datetime import time as timeFromDateTimeString
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.browser import BrowserView

from zope.app.publisher.fileresource import File, Image
from zope.app.publisher.browser.resource import Resource

class FileResource(BrowserView, Resource):

    implements(IBrowserPublisher)

    def publishTraverse(self, request, name):
        '''See interface IBrowserPublisher'''
        raise NotFound(None, name)

    def browserDefault(self, request):
        '''See interface IBrowserPublisher'''
        return getattr(self, request.method), ()

    #
    ############################################################

    # for unit tests
    def _testData(self):
        f = open(self.context.path, 'rb')
        data = f.read()
        f.close()
        return data


    def chooseContext(self):
        """Choose the appropriate context"""
        return self.context


    def GET(self):
        """Default document"""

        file = self.chooseContext()
        request = self.request
        response = request.response

        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        header = request.getHeader('If-Modified-Since', None)
        if header is not None:
            header = header.split(';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            try:    mod_since=long(timeFromDateTimeString(header))
            except: mod_since=None
            if mod_since is not None:
                if getattr(file, 'lmt', None):
                    last_mod = long(file.lmt)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    response.setStatus(304)
                    return ''

        response.setHeader('Content-Type', file.content_type)
        response.setHeader('Last-Modified', file.lmh)

        setCacheControl(response)
        f = open(file.path,'rb')
        data = f.read()
        f.close()

        return data

    def HEAD(self):
        file = self.chooseContext()
        response = self.request.response
        response.setHeader('Content-Type', file.content_type)
        response.setHeader('Last-Modified', file.lmh)
        setCacheControl(response)
        return ''


def setCacheControl(response, secs=86400):
    # Cache for one day by default
    response.setHeader('Cache-Control', 'public,max-age=%s' % secs)
    t = time.time() + secs
    response.setHeader('Expires',
                       time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                     time.gmtime(t)))


class FileResourceFactory(object):

    def __init__(self, path, checker, name):
        self.__file = File(path, name)
        self.__checker = checker
        self.__name = name

    def __call__(self, request):
        resource = FileResource(self.__file, request)
        resource.__Security_checker__ = self.__checker
        resource.__name__ = self.__name
        return resource

class ImageResourceFactory(object):

    def __init__(self, path, checker, name):
        self.__file = Image(path, name)
        self.__checker = checker
        self.__name = name

    def __call__(self, request):
        resource = FileResource(self.__file, request)
        resource.__Security_checker__ = self.__checker
        resource.__name__ = self.__name
        return resource

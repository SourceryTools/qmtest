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
"""Resource Directory

A 'resource directory' is an on-disk directory which is registered as
a resource using the <resourceDirectory> ZCML directive.  The
directory is treated as a source for individual resources; it can be
traversed to retrieve resources represented by contained files, which
can in turn be treated as resources.  The contained files have
__name__ values which include a '/' separating the __name__ of the
resource directory from the name of the file within the directory.

$Id: directoryresource.py 69635 2006-08-18 09:47:04Z philikon $
"""
import os
import posixpath

from zope.interface import implements
from zope.publisher.interfaces import NotFound
from zope.security.proxy import Proxy
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.app.publisher.browser.resource import Resource

from fileresource import FileResourceFactory, ImageResourceFactory
from pagetemplateresource import PageTemplateResourceFactory
from resources import empty

_marker = object()

# we only need this class as a context for DirectoryResource
class Directory(object):

    def __init__(self, path, checker, name):
        self.path = path
        self.checker = checker
        self.__name__ = name

class DirectoryResource(BrowserView, Resource):

    implements(IBrowserPublisher)

    resource_factories = {
        '.gif':  ImageResourceFactory,
        '.png':  ImageResourceFactory,
        '.jpg':  ImageResourceFactory,
        '.pt':   PageTemplateResourceFactory,
        '.zpt':  PageTemplateResourceFactory,
        '.html': PageTemplateResourceFactory,
        }

    default_factory = FileResourceFactory

    def publishTraverse(self, request, name):
        '''See interface IBrowserPublisher'''
        return self.get(name)

    def browserDefault(self, request):
        '''See interface IBrowserPublisher'''
        return empty, ()

    def __getitem__(self, name):
        res = self.get(name, None)
        if res is None:
            raise KeyError(name)
        return res

    def get(self, name, default=_marker):
        path = self.context.path
        filename = os.path.join(path, name)
        isfile = os.path.isfile(filename)
        isdir = os.path.isdir(filename)
          
        if not (isfile or isdir):
            if default is _marker:
                raise NotFound(None, name)
            return default

        if isfile:
            ext = os.path.splitext(os.path.normcase(name))[1]
            factory = self.resource_factories.get(ext, self.default_factory)
        else:
            factory = DirectoryResourceFactory

        rname = posixpath.join(self.__name__, name)
        resource = factory(filename, self.context.checker, rname)(self.request)
        resource.__parent__ = self
        return resource

class DirectoryResourceFactory(object):

    def __init__(self, path, checker, name):
        self.__dir = Directory(path, checker, name)
        self.__checker = checker
        self.__name = name

    def __call__(self, request):
        resource = DirectoryResource(self.__dir, request)
        resource.__Security_checker__ = self.__checker
        resource.__name__ = self.__name
        return resource

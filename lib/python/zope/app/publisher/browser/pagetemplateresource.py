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
"""Page Template Resource

$Id: pagetemplateresource.py 73637 2007-03-26 16:22:07Z dobe $
"""

from zope.interface import implements
from zope.publisher.interfaces import NotFound
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.app.publisher.pagetemplateresource import PageTemplate
from zope.app.publisher.browser.resource import Resource

class PageTemplateResource(BrowserView, Resource):

    implements(IBrowserPublisher)

    def publishTraverse(self, request, name):
        '''See interface IBrowserPublisher'''
        raise NotFound(None, name)

    def browserDefault(self, request):
        '''See interface IBrowserPublisher'''
        return self, ()

    def __call__(self):
        pt = self.context
        response = self.request.response
        if not response.getHeader("Content-Type"):
            response.setHeader("Content-Type", pt.content_type)
        return pt(self.request)

class PageTemplateResourceFactory(object):

    def __init__(self, path, checker, name):
        self.__pt = PageTemplate(path)
        self.__checker = checker
        self.__name = name

    def __call__(self, request):
        resource = PageTemplateResource(self.__pt, request)
        resource.__Security_checker__ = self.__checker
        resource.__name__ = self.__name
        return resource

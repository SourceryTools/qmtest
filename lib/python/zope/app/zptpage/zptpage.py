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
"""ZPT Page (content object) implementation

$Id: zptpage.py 68696 2006-06-17 02:25:39Z ctheune $
"""
from persistent import Persistent

from zope.security.proxy import ProxyFactory
from zope.interface import implements
from zope.pagetemplate.pagetemplate import PageTemplate
from zope.size.interfaces import ISized
from zope.publisher.browser import BrowserView
from zope.traversing.api import getPath
from zope.filerepresentation.interfaces import IReadFile, IWriteFile
from zope.filerepresentation.interfaces import IFileFactory

from zope.app.pagetemplate.engine import AppPT
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.container.contained import Contained
from zope.app.publication.interfaces import IFileContent
from zope.app.zptpage.interfaces import IZPTPage, IRenderZPTPage

class ZPTPage(AppPT, PageTemplate, Persistent, Contained):

    implements(IZPTPage, IRenderZPTPage, IFileContent)

    # See zope.app.zptpage.interfaces.IZPTPage
    expand = False

    # See zope.app.zptpage.interfaces.IZPTPage
    evaluateInlineCode = False

    def getSource(self, request=None):
        """See zope.app.zptpage.interfaces.IZPTPage"""
        return self.read(request)

    def setSource(self, text, content_type='text/html'):
        """See zope.app.zptpage.interfaces.IZPTPage"""
        if not isinstance(text, unicode):
            raise TypeError("source text must be Unicode" , text)
        self.pt_edit(text, content_type)

    # See zope.app.zptpage.interfaces.IZPTPage
    source = property(getSource, setSource, None,
                      """Source of the Page Template.""")

    def pt_getEngineContext(self, namespace):
        context = self.pt_getEngine().getContext(namespace)
        context.evaluateInlineCode = self.evaluateInlineCode
        return context

    def pt_getContext(self, instance, request, **_kw):
        # instance is a View component
        namespace = super(ZPTPage, self).pt_getContext(**_kw)
        namespace['template'] = self
        namespace['request'] = request
        namespace['container'] = namespace['context'] = instance
        return namespace

    def pt_source_file(self):
        try:
            return getPath(self)
        except TypeError:
            return None

    def render(self, request, *args, **keywords):
        instance = self.__parent__

        debug_flags = request.debug
        request = ProxyFactory(request)
        instance = ProxyFactory(instance)
        if args:
            args = ProxyFactory(args)
        kw = ProxyFactory(keywords)

        namespace = self.pt_getContext(instance, request,
                                       args=args, options=kw)

        return self.pt_render(namespace, showtal=debug_flags.showTAL,
                              sourceAnnotations=debug_flags.sourceAnnotations)


class Sized(object):

    implements(ISized)

    def __init__(self, page):
        self.num_lines = len(page.getSource().splitlines())

    def sizeForSorting(self):
        'See ISized'
        return ('line', self.num_lines)

    def sizeForDisplay(self):
        'See ISized'
        if self.num_lines == 1:
            return _('1 line')
        return _('${lines} lines', mapping={'lines': str(self.num_lines)})

# File-system access adapters

class ZPTReadFile(object):

    implements(IReadFile)

    def __init__(self, context):
        self.context = context

    def read(self):
        return self.context.getSource()

    def size(self):
        return len(self.read())

class ZPTWriteFile(object):

    implements(IWriteFile)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        # We cannot communicate an encoding via FTP. Zope's default is UTF-8,
        # so use it.
        self.context.setSource(data.decode('UTF-8'), None)

class ZPTFactory(object):

    implements(IFileFactory)


    def __init__(self, context):
        self.context = context

    def __call__(self, name, content_type, data):
        page = ZPTPage()
        # We cannot communicate an encoding via FTP. Zope's default is UTF-8,
        # so use it.
        page.setSource(data.decode('UTF-8'), content_type or 'text/html')
        return page

class ZPTSourceView(BrowserView):

    def __str__(self):
        return self.context.getSource()

    __call__ = __str__

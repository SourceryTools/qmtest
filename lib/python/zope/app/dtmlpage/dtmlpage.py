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
"""DTML Page content component

$Id: dtmlpage.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from persistent import Persistent

from zope.documenttemplate.untrusted import UntrustedHTML
from zope.interface import implements
from zope.annotation.interfaces import IAnnotatable
from zope.filerepresentation.interfaces import IFileFactory

from zope.app.container.contained import Contained
from zope.app.publication.interfaces import IFileContent

from interfaces import IDTMLPage, IRenderDTMLPage

class DTMLPage(Persistent, Contained):
    implements(IDTMLPage, IRenderDTMLPage, IFileContent, IAnnotatable)

    def __init__(self, source=''):
        self.setSource(source)

    def getSource(self):
        '''See interface `IDTMLPage`'''
        return self.template.read()

    def setSource(self, text, content_type='text/html'):
        '''See interface `IDTMLPage`'''
        self.template = UntrustedHTML(text)
        self.content_type = content_type

    def render(self, request, *args, **kw):
        """See interface `IDTMLRenderPage`"""
        return self.template(self.__parent__, request, REQUEST=request, **kw)


    __call__ = render

    source = property(getSource, setSource, None,
                      """Source of the DTML Page.""")

class DTMLFactory(object):
    implements(IFileFactory)

    def __init__(self, context):
        self.context = context

    def __call__(self, name, content_type, data):
        r = DTMLPage()
        r.setSource(data, content_type or 'text/html')
        return r

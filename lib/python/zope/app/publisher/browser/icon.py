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
"""Icon support

$Id: icon.py 69142 2006-07-16 14:14:34Z jim $
"""
import os
import re

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.configuration.exceptions import ConfigurationError
from zope.traversing.namespace import getResource
from zope.component.interface import provideInterface
from zope.component.zcml import handler

from zope.app.publisher.browser import metaconfigure

IName = re.compile('I[A-Z][a-z]')

class IconView(object):

    def __init__(self, context, request, rname, alt):
        self.context = context
        self.request = request
        self.rname = rname
        self.alt = alt

    def __call__(self):
        # The context is important here, since it becomes the parent of the
        # icon, which is needed to generate the absolute URL.
        resource = getResource(self.context, self.rname, self.request)
        src = resource()

        return ('<img src="%s" alt="%s" width="16" height="16" border="0" />'
                % (src, self.alt))

    def url(self):
        resource = getResource(self.context, self.rname, self.request)
        src = resource()
        return src

class IconViewFactory(object):

    def __init__(self, rname, alt):
        self.rname = rname
        self.alt = alt

    def __call__(self, context, request):
        return IconView(context, request, self.rname, self.alt)

def IconDirective(_context, name, for_, file=None, resource=None,
                  layer=IDefaultBrowserLayer, title=None):

    iname = for_.getName()

    if title is None:
        title = iname
        if IName.match(title):
            title = title[1:] # Remove leading 'I'

    if file is not None and resource is not None:
        raise ConfigurationError(
            "Can't use more than one of file, and resource "
            "attributes for icon directives"
            )
    elif file is not None:
        resource = '-'.join(for_.__module__.split('.'))
        resource = "%s-%s-%s" % (resource, iname, name)
        ext = os.path.splitext(file)[1]
        if ext:
            resource += ext
        metaconfigure.resource(_context, image=file,
                               name=resource, layer=layer)
    elif resource is None:
        raise ConfigurationError(
            "At least one of the file, and resource "
            "attributes for resource directives must be specified"
            )

    vfactory = IconViewFactory(resource, title)

    _context.action(
        discriminator = ('view', name, vfactory, layer),
        callable = handler,
        args = ('registerAdapter',
                vfactory, (for_, layer), Interface, name, _context.info)
        )

    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (for_.__module__+'.'+for_.getName(),
                for_)
        )

    

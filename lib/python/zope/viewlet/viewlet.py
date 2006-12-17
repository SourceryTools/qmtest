##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Viewlet implementation

$Id: metaconfigure.py 38437 2005-09-10 01:59:07Z rogerineichen $
"""
__docformat__ = 'restructuredtext'

import os
import sys
import zope.interface
from zope.traversing import api
from zope.publisher.browser import BrowserView
from zope.viewlet import interfaces

from zope.app.pagetemplate import simpleviewclass
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

class ViewletBase(BrowserView):
    """Viewlet adapter class used in meta directive as a mixin class."""

    zope.interface.implements(interfaces.IViewlet)

    def __init__(self, context, request, view, manager):
        super(ViewletBase, self).__init__(context, request)
        self.__parent__ = view
        self.context = context
        self.request = request
        self.manager = manager

    def update(self):
        pass

    def render(self):
        raise NotImplementedError(
            '`render` method must be implemented by subclass.')


class SimpleAttributeViewlet(ViewletBase):
    """A viewlet that uses a specified method to produce its content."""

    def render(self, *args, **kw):
        # If a class doesn't provide it's own call, then get the attribute
        # given by the browser default.

        attr = self.__page_attribute__
        if attr == 'render':
            raise AttributeError("render")

        meth = getattr(self, attr)
        return meth(*args, **kw)


class simple(simpleviewclass.simple):
    """Simple viewlet class supporting the ``render()`` method."""

    render = simpleviewclass.simple.__call__


def SimpleViewletClass(template, offering=None, bases=(), attributes=None,
                       name=u''):
    """A function that can be used to generate a viewlet from a set of
    information.
    """
    # Get the current frame
    if offering is None:
        offering = sys._getframe(1).f_globals

    # Create the base class hierarchy
    bases += (simple, ViewletBase)

    attrs = {'index' : ViewPageTemplateFile(template, offering),
             '__name__' : name}
    if attributes:
        attrs.update(attributes)

    # Generate a derived view class.
    class_ = type("SimpleViewletClass from %s" % template, bases, attrs)

    return class_


class ResourceViewletBase(object):
    """A simple viewlet for inserting references to resources.

    This is an abstract class that is expected to be used as a base only.
    """
    _path = None

    def getURL(self):
        resource = api.traverse(self.context, '++resource++' + self._path,
                                request=self.request)
        return resource()

    def render(self, *args, **kw):
        return self.index(*args, **kw)


def JavaScriptViewlet(path):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'javascript_viewlet.pt')

    klass = type('JavaScriptViewlet',
                 (ResourceViewletBase, ViewletBase),
                  {'index': ViewPageTemplateFile(src),
                   '_path': path})

    return klass


class CSSResourceViewletBase(ResourceViewletBase):

    _media = 'all'
    _rel = 'stylesheet'

    def getMedia(self):
        return self._media

    def getRel(self):
        return self._rel


def CSSViewlet(path, media="all", rel="stylesheet"):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'css_viewlet.pt')

    klass = type('CSSViewlet',
                 (CSSResourceViewletBase, ViewletBase),
                  {'index': ViewPageTemplateFile(src),
                   '_path': path,
                   '_media':media,
                   '_rel':rel})

    return klass


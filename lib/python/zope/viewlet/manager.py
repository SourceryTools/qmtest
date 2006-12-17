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
"""Content Provider Manager implementation

$Id: manager.py 41120 2006-01-03 21:38:40Z srichter $
"""
__docformat__ = 'restructuredtext'

import zope.component
import zope.interface
import zope.security
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from zope.viewlet import interfaces

class ViewletManagerBase(object):
    """The Viewlet Manager Base

    A generic manager class which can be instantiated
    """
    zope.interface.implements(interfaces.IViewletManager)

    def __init__(self, context, request, view):
        self.__updated = False
        self.__parent__ = view
        self.context = context
        self.request = request


    def __getitem__(self, name):
        """See zope.interface.common.mapping.IReadMapping"""
        # Find the viewlet
        viewlet = zope.component.queryMultiAdapter(
            (self.context, self.request, self.__parent__, self),
            interfaces.IViewlet, name=name)

        # If the viewlet was not found, then raise a lookup error
        if viewlet is None:
            raise zope.component.interfaces.ComponentLookupError(
                'No provider with name `%s` found.' %name)

        # If the viewlet cannot be accessed, then raise an
        # unauthorized error
        if not zope.security.canAccess(viewlet, 'render'):
            raise zope.security.interfaces.Unauthorized(
                'You are not authorized to access the provider '
                'called `%s`.' %name)

        # Return the viewlet.
        return viewlet

    def get(self, name, default=None):
        """See zope.interface.common.mapping.IReadMapping"""
        try:
            return self[name]
        except (zope.component.interfaces.ComponentLookupError,
                zope.security.interfaces.Unauthorized):
            return default

    def filter(self, viewlets):
        """Sort out all content providers

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        # Only return viewlets accessible to the principal
        return [(name, viewlet) for name, viewlet in viewlets
                if zope.security.canAccess(viewlet, 'render')]

    def sort(self, viewlets):
        """Sort the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        # By default, use the standard Python way of doing sorting.
        return sorted(viewlets, lambda x, y: cmp(x[1], y[1]))

    def update(self):
        """See zope.contentprovider.interfaces.IContentProvider"""
        self.__updated = True

        # Find all content providers for the region
        viewlets = zope.component.getAdapters(
            (self.context, self.request, self.__parent__, self),
            interfaces.IViewlet)

        viewlets = self.filter(viewlets)
        viewlets = self.sort(viewlets)

        # Just use the viewlets from now on
        self.viewlets = [viewlet for name, viewlet in viewlets]

        # Update all viewlets
        [viewlet.update() for viewlet in self.viewlets]

    def render(self):
        """See zope.contentprovider.interfaces.IContentProvider"""
        # Now render the view
        if self.template:
            return self.template(viewlets=self.viewlets)
        else:
            return u'\n'.join([viewlet.render() for viewlet in self.viewlets])


def ViewletManager(name, interface, template=None, bases=()):

    if template is not None:
        template = ViewPageTemplateFile(template)

    if ViewletManagerBase not in bases:
        # Make sure that we do not get a default viewlet manager mixin, if the
        # provided base is already a full viewlet manager implementation.
        if not (len(bases) == 1 and
                interfaces.IViewletManager.implementedBy(bases[0])):
            bases = bases + (ViewletManagerBase,)

    ViewletManager = type(
        '<ViewletManager providing %s>' % interface.getName(),
        bases,
        {'template': template, '__name__' : name})
    zope.interface.classImplements(ViewletManager, interface)
    return ViewletManager

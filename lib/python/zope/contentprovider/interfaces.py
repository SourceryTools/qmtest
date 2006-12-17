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
"""Content provider interfaces

$Id: interfaces.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.component
import zope.interface
from zope.tales import interfaces
from zope.publisher.interfaces import browser

class IUpdateNotCalled(zope.interface.common.interfaces.IRuntimeError):
    """Update Not Called

    An error that is raised when any content provider method is called before
    the ``update()`` method.
    """

class UpdateNotCalled(RuntimeError):
    pass

# Make it a singelton
UpdateNotCalled = UpdateNotCalled('``update()`` was not called yet.')

class IContentProvider(browser.IBrowserView):
    """A piece of content to be shown on a page.

    Objects implementing this interface are providing HTML content when they
    are rendered. It is up to the implementation to decide how to lookup
    necessary data to complete the job.

    Content Providers use a two-stage process to fulfill their contract:

    (1) The first stage is responsible to calculate the state of the content
        provider and, if applicable, edit the data. This stage is executed
        using the ``update()`` method.

    (2) During the second stage the provider constructs/renders its HTML
        output based on the state that was calculated in the first stage. This
        stage is executed using the ``render()`` method.

    Content Providers are discriminated by three components: the context, the
    request and the view. This allows great control over the selection of the
    provider.
    """

    __parent__ = zope.interface.Attribute(
        """The view the provider appears in.

        The view is the third discriminator of the content provider. It allows
        that the content can be controlled for different views.

        Having it stored as the parent is also very important for the security
        context to be kept.
        """)

    def update():
        """Initialize the content provider.

        This method should perform all state calculation and *not* refer it to
        the rendering stage.

        In this method, all state must be calculated from the current
        interaction (e.g., the browser request); all contained or managed
        content providers must have ``update()`` be called as well; any
        additional stateful API for contained or managed content providers
        must be handled; and persistent objects should be modified, if the
        provider is going to do it.

        Do *not* store state about persistent objects: the rendering process
        should actually use the persistent objects for the data, in case other
        components modify the object between the update and render stages.

        This method *must* be called before any other method that mutates the
        instance (besides the class constructor). Non-mutating methods and
        attributes may raise an error if used before ``update()`` is
        called. The view may rely on this order but is *not required* to
        explicitly enforce this. Implementations *may* enforce it as a
        developer aid.
        """

    def render(*args, **kw):
        """Return the content provided by this content provider.

        Calling this method before ``update()`` *may* (but is not required to)
        raise an ``UpdateNotCalled`` error.
        """


class IContentProviderType(zope.interface.interfaces.IInterface):
    """Type interface for content provider types (interfaces derived from
       IContentProvider).
    """


class ITALNamespaceData(zope.interface.interfaces.IInterface):
    """A type interface that marks an interface as a TAL data specification.

    All fields specified in an interface that provides `ITALNamespaceData`
    will be looked up in the TAL context and stored on the content provider. A
    content provider can have multiple interfaces that are of this type.
    """


class ContentProviderLookupError(zope.component.ComponentLookupError):
    """No content provider was found."""


class ITALESProviderExpression(interfaces.ITALESExpression):
    """Return the HTML content of the named provider.

    To call a content provider in a view use the the following syntax in a page
    template::

      <tal:block replace="structure provider:provider.name">

    The content provider is looked up by the (context, request, view) objects
    and the name (`provider.name`).
    """

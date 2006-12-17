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
"""Viewlet metadirective

$Id: metadirectives.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.configuration.fields
import zope.schema
from zope.publisher.interfaces import browser
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

from zope.app.publisher.browser import metadirectives
from zope.viewlet import interfaces


class IContentProvider(metadirectives.IPagesDirective):
    """A directive to register a simple content provider.

    Content providers are registered by their context (`for` attribute), the
    request (`layer` attribute) and the view (`view` attribute). They also
    must provide a name, so that they can be found using the TALES
    ``provider`` namespace. Other than that, content providers are just like
    any other views.
    """

    view = zope.configuration.fields.GlobalObject(
        title=_("The view the content provider is registered for."),
        description=_("The view can either be an interface or a class. By "
                      "default the provider is registered for all views, "
                      "the most common case."),
        required=False,
        default=browser.IBrowserView)

    name = zope.schema.TextLine(
        title=_("The name of the content provider."),
        description=_("The name of the content provider is used in the TALES "
                      "``provider`` namespace to look up the content "
                      "provider."),
        required=True)


class ITemplatedContentProvider(IContentProvider):
    """A directive for registering a content provider that uses a page
    template to provide its content."""

    template = zope.configuration.fields.Path(
        title=_("Content-generating template."),
        description=_("Refers to a file containing a page template (should "
                      "end in extension ``.pt`` or ``.html``)."),
        required=False)


class IViewletManagerDirective(ITemplatedContentProvider):
    """A directive to register a new viewlet manager.

    Viewlet manager registrations are very similar to content provider
    registrations, since they are just a simple extension of content
    providers. However, viewlet managers commonly have a specific provided
    interface, which is used to discriminate the viewlets they are providing.
    """

    provides = zope.configuration.fields.GlobalInterface(
        title=_("The interface this viewlet manager provides."),
        description=_("A viewlet manager can provide an interface, which "
                      "is used to lookup its contained viewlets."),
        required=False,
        default=interfaces.IViewletManager,
        )


class IViewletDirective(ITemplatedContentProvider):
    """A directive to register a new viewlet.

    Viewlets are content providers that can only be displayed inside a viewlet
    manager. Thus they are additionally discriminated by the manager. Viewlets
    can rely on the specified viewlet manager interface to provide their
    content.

    The viewlet directive also supports an undefined set of keyword arguments
    that are set as attributes on the viewlet after creation. Those attributes
    can then be used to implement sorting and filtering, for example.
    """

    manager = zope.configuration.fields.GlobalObject(
        title=_("view"),
        description=u"The interface of the view this viewlet is for. "
                    u"(default IBrowserView)""",
        required=False,
        default=interfaces.IViewletManager)


# Arbitrary keys and values are allowed to be passed to the viewlet.
IViewletDirective.setTaggedValue('keyword_arguments', True)

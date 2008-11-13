##############################################################################
#
# Copyright (c) 2002, 2003 Zope Corporation and Contributors.
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
"""`OnlineHelp` views

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.security.proxy import removeSecurityProxy
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserView

from zope.app import zapi
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from zope.app.onlinehelp.interfaces import IOnlineHelpTopic, IOnlineHelp
from zope.app.onlinehelp import getTopicFor


class OnlineHelpTopicView(BrowserView):
    """View for one particular help topic."""

    def __init__(self, context, request):
        super(OnlineHelpTopicView, self).__init__(context, request)

    def topicContent(self):
        """ render the source of the help topic """
        source = zapi.createObject(self.context.type,
                                   self.context.source)
        view = zapi.getMultiAdapter((source, self.request))
        html = view.render()
        return html

    renderTopic = ViewPageTemplateFile('helptopic.pt')


class ZPTOnlineHelpTopicView(BrowserView):
    """View for a page template based help topic."""

    def __init__(self, context, request):
        super(ZPTOnlineHelpTopicView, self).__init__(context, request)

    def renderTopic(self):
        """Render the registred topic."""
        path = self.context.path
        view = ViewPageTemplateFile(path)
        return view(self)


class ContextHelpView(BrowserView):

    def __init__(self, context, request):
        super(ContextHelpView, self).__init__(context, request)
        self.topic = None

    def getContextualTopicView(self):
        """Retrieve and render the source of a context help topic """
        topic = self.getContextHelpTopic()
        view = zapi.getMultiAdapter((topic, self.request), name='index.html')
        return view.renderTopic()

    def getContextHelpTopic(self):
        """Retrieve a help topic based on the context of the
        help namespace.

        If the context is a view, try to find
        a matching help topic for the view and its context.
        If no help topic is found, try to get a help topic for
        the context only.

        If the context is not a view, try to retrieve a help topic
        based on the context.

        If nothing is found, return the onlinehelp root topic
        """
        if self.topic is not None:
            return self.topic

        onlinehelp = self.context
        help_context = onlinehelp.context
        self.topic = None
        if IBrowserView.providedBy(help_context):
            # called from a view
            self.topic = getTopicFor(
                zapi.getParent(help_context),
                zapi.getName(help_context)
                )
            if self.topic is None:
                # nothing found for view try context only
                self.topic = getTopicFor(
                    zapi.getParent(help_context)
                    )
        else:
            # called without view
            self.topic = getTopicFor(help_context)

        if self.topic is None:
            self.topic = onlinehelp

        return self.topic

    contextHelpTopic = property(getContextHelpTopic)

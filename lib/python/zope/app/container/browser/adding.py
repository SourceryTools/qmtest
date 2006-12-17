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
"""Adding View

The Adding View is used to add new objects to a container. It is sort of a
factory screen.

$Id: adding.py 67630 2006-04-27 00:54:03Z jim $
"""

__docformat__ = 'restructuredtext'

import zope.security.checker
from zope.component.interfaces import IFactory
from zope.event import notify
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.browser import BrowserView
from zope.security.proxy import removeSecurityProxy
from zope.exceptions.interfaces import UserError
from zope.location import LocationProxy
from zope.lifecycleevent import ObjectCreatedEvent

from zope.app.container.interfaces import IAdding, INameChooser
from zope.app.container.interfaces import IContainerNamesContainer
from zope.app.container.constraints import checkFactory, checkObject

from zope.app import zapi
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.publisher.browser.menu import getMenu


class Adding(BrowserView):
    implements(IAdding, IPublishTraverse)

    def add(self, content):
        """See zope.app.container.interfaces.IAdding
        """
        container = self.context
        name = self.contentName
        chooser = INameChooser(container)

        # check precondition
        checkObject(container, name, content)

        if IContainerNamesContainer.providedBy(container):
            # The container picks its own names.
            # We need to ask it to pick one.
            name = chooser.chooseName(self.contentName or '', content)
        else:
            request = self.request
            name = request.get('add_input_name', name)

            if name is None:
                name = chooser.chooseName(self.contentName or '', content)
            elif name == '':
                name = chooser.chooseName('', content)
            chooser.checkName(name, content)

        container[name] = content
        self.contentName = name # Set the added object Name
        return container[name]

    contentName = None # usually set by Adding traverser

    def nextURL(self):
        """See zope.app.container.interfaces.IAdding"""
        return zapi.absoluteURL(self.context, self.request) + '/@@contents.html'

    # set in BrowserView.__init__
    request = None
    context = None

    def publishTraverse(self, request, name):
        """See zope.app.container.interfaces.IAdding"""
        if '=' in name:
            view_name, content_name = name.split("=", 1)
            self.contentName = content_name

            if view_name.startswith('@@'):
                view_name = view_name[2:]
            return zapi.getMultiAdapter((self, request), name=view_name)

        if name.startswith('@@'):
            view_name = name[2:]
        else:
            view_name = name

        view = zapi.queryMultiAdapter((self, request), name=view_name)
        if view is not None:
            return view

        factory = zapi.queryUtility(IFactory, name)
        if factory is None:
            return super(Adding, self).publishTraverse(request, name)

        return factory

    def action(self, type_name='', id=''):
        if not type_name:
            raise UserError(_(u"You must select the type of object to add."))

        if type_name.startswith('@@'):
            type_name = type_name[2:]

        if '/' in type_name:
            view_name = type_name.split('/', 1)[0]
        else:
            view_name = type_name

        if zapi.queryMultiAdapter((self, self.request),
                                  name=view_name) is not None:
            url = "%s/%s=%s" % (
                zapi.absoluteURL(self, self.request), type_name, id)
            self.request.response.redirect(url)
            return

        if not self.contentName:
            self.contentName = id

        # TODO: If the factory wrapped by LocationProxy is already a Proxy,
        #       then ProxyFactory does not do the right thing and the
        #       original's checker info gets lost. No factory that was
        #       registered via ZCML and was used via addMenuItem worked
        #       here. (SR)
        factory = zapi.getUtility(IFactory, type_name)
        if not type(factory) is zope.security.checker.Proxy:
            factory = LocationProxy(factory, self, type_name)
            factory = zope.security.checker.ProxyFactory(factory)
        content = factory()

        # Can't store security proxies.
        # Note that it is important to do this here, rather than
        # in add, otherwise, someone might be able to trick add
        # into unproxying an existing object,
        content = removeSecurityProxy(content)

        notify(ObjectCreatedEvent(content))

        self.add(content)
        self.request.response.redirect(self.nextURL())

    def nameAllowed(self):
        """Return whether names can be input by the user."""
        return not IContainerNamesContainer.providedBy(self.context)

    menu_id = None
    index = ViewPageTemplateFile("add.pt")

    def addingInfo(self):
        """Return menu data.

        This is sorted by title.
        """
        container = self.context
        result = []
        for menu_id in (self.menu_id, 'zope.app.container.add'):
            if not menu_id:
                continue
            for item in getMenu(menu_id, self, self.request):
                extra = item.get('extra')
                if extra:
                    factory = extra.get('factory')
                    if factory:
                        factory = zapi.getUtility(IFactory, factory)
                        if not checkFactory(container, None, factory):
                            continue
                        elif item['extra']['factory'] != item['action']:
                            item['has_custom_add_view']=True
                result.append(item)

        result.sort(lambda a, b: cmp(a['title'], b['title']))
        return result

    def isSingleMenuItem(self):
        "Return whether there is single menu item or not."
        return len(self.addingInfo()) == 1

    def hasCustomAddView(self):
       "This should be called only if there is `singleMenuItem` else return 0"
       if self.isSingleMenuItem():
           menu_item = self.addingInfo()[0]
           if 'has_custom_add_view' in menu_item:
               return True
       return False

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
"""Browser configuration code

$Id: i18nresourcemeta.py 67630 2006-04-27 00:54:03Z jim $
"""
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.proxy import Proxy
from zope.security.checker import CheckerPublic, Checker
from zope.component.zcml import handler

from zope.app.publisher.fileresource import File, Image
from zope.app.publisher.browser.i18nfileresource import I18nFileResourceFactory


class I18nResource(object):

    type = IBrowserRequest
    default_allowed_attributes = '__call__'

    def __init__(self, _context, name=None, defaultLanguage='en',
                 layer=IDefaultBrowserLayer, permission=None):
        self._context = _context
        self.name = name
        self.defaultLanguage = defaultLanguage
        self.layer = layer
        self.permission = permission
        self.__data = {}
        self.__format = None

    def translation(self, _context, language, file=None, image=None):

        if file is not None and image is not None:
            raise ConfigurationError(
                "Can't use more than one of file, and image "
                "attributes for resource directives"
                )
        elif file is not None:
            if self.__format is not None and self.__format != File:
                raise ConfigurationError(
                    "Can't use both files and images in the same "
                    "i18n-resource directive"
                    )
            self.__data[language] = File(_context.path(file), self.name)
            self.__format = File
        elif image is not None:
            if self.__format is not None and self.__format != Image:
                raise ConfigurationError(
                    "Can't use both files and images in the same "
                    "i18n-resource directive"
                    )
            self.__data[language] = Image(_context.path(image), self.name)
            self.__format = Image
        else:
            raise ConfigurationError(
                "At least one of the file, and image "
                "attributes for resource directives must be specified"
                )

        return ()


    def __call__(self, require = None):
        if self.name is None:
            return ()

        if not self.__data.has_key(self.defaultLanguage):
            raise ConfigurationError(
                "A translation for the default language (%s) "
                "must be specified" % self.defaultLanguage
                )

        permission = self.permission
        factory = I18nFileResourceFactory(self.__data, self.defaultLanguage)

        if permission:
            if require is None:
                require = {}

            if permission == 'zope.Public':
                permission = CheckerPublic

        if require:
            checker = Checker(require)

            factory = self._proxyFactory(factory, checker)

        self._context.action(
            discriminator = ('i18n-resource', self.name, self.type, self.layer),
            callable = handler,
            args = ('registerAdapter',
                    factory, (self.layer,), Interface, self.name,
                    self._context.info)
            )


    def _proxyFactory(self, factory, checker):
        def proxyView(request,
                      factory=factory, checker=checker):
            resource = factory(request)

            # We need this in case the resource gets unwrapped and
            # needs to be rewrapped
            resource.__Security_checker__ = checker

            return Proxy(resource, checker)

        return proxyView

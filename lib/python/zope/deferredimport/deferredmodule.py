##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Modules with defered attributes

$Id: deferredmodule.py 67275 2006-04-22 18:53:22Z jim $
"""
import types
import sys
import warnings
import zope.proxy


class Deferred(object):

    def __init__(self, name, specifier):
        self.__name__ = name
        self.specifier = specifier

    _import_chicken = {}, {}, ['*']

    def get(self):

        specifier = self.specifier
        if ':' in specifier:
            module, name = specifier.split(':')
        else:
            module, name = specifier, ''

        v = __import__(module, *self._import_chicken)
        if name:
            for n in name.split('.'):
                v = getattr(v, n)
        return v

class DeferredAndDeprecated(Deferred):

    def __init__(self, name, specifier, message):
        super(DeferredAndDeprecated, self).__init__(name, specifier)
        self.message = message

    def get(self):
        warnings.warn(
            self.__name__ + " is deprecated. " + self.message,
            DeprecationWarning, stacklevel=3)
        
        return super(DeferredAndDeprecated, self).get()


class ModuleProxy(zope.proxy.ProxyBase):
    __slots__ = ('__deferred_definitions__', )

    def __init__(self, module):
        super(ModuleProxy, self).__init__(module)
        self.__deferred_definitions__ = {}

    def __getattr__(self, name):
        try:
            get = self.__deferred_definitions__.pop(name)
        except KeyError:
            raise AttributeError, name
        v = get.get()
        setattr(self, name, v)
        return v

def initialize(level=1):
    __name__ = sys._getframe(level).f_globals['__name__']
    module = sys.modules[__name__]
    if not (type(module) is ModuleProxy):
        module = ModuleProxy(module)
        sys.modules[__name__] = module

    if level == 1:
        return
    return module

def define(**names):
    module = initialize(2)
    __deferred_definitions__ = module.__deferred_definitions__
    for name, specifier in names.iteritems():
        __deferred_definitions__[name] = Deferred(name, specifier)

def defineFrom(from_name, *names):
    module = initialize(2)
    __deferred_definitions__ = module.__deferred_definitions__
    for name in names:
        specifier = from_name + ':' + name
        __deferred_definitions__[name] = Deferred(name, specifier)

def deprecated(message, **names):
    module = initialize(2)
    __deferred_definitions__ = module.__deferred_definitions__
    for name, specifier in names.iteritems():
        __deferred_definitions__[name] = DeferredAndDeprecated(
            name, specifier, message)

def deprecatedFrom(message, from_name, *names):
    module = initialize(2)
    __deferred_definitions__ = module.__deferred_definitions__
    for name in names:
        specifier = from_name + ':' + name
        __deferred_definitions__[name] = DeferredAndDeprecated(
            name, specifier, message)

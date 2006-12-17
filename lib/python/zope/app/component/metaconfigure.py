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
"""Generic Components ZCML Handlers

$Id: metaconfigure.py 68632 2006-06-14 16:29:42Z faassen $
"""
__docformat__ = 'restructuredtext'

import warnings
import zope.component
from zope import component
from zope.interface import Interface
from zope.component.zcml import handler, proxify, utility
from zope.component.interface import provideInterface
from zope.component.interfaces import IDefaultViewName, IFactory
from zope.configuration.exceptions import ConfigurationError
from zope.security.checker import CheckerPublic
from zope.security.checker import Checker, NamesChecker
import zope.deferredimport

PublicPermission = 'zope.Public'

zope.deferredimport.deprecatedFrom(
    "Moved to zope.component.zcml. Importing from here will stop working "
    "in Zope 3.5",
    "zope.component.zcml",
    "handler", "adapter", "subscriber", "utility", "interface",
    )
    


# BBB 2006/02/24, to be removed after 12 months
def factory(_context, component, id, title=None, description=None):
    try:
        dottedname = component.__module__ + "." + component.__name__
    except AttributeError:
        dottedname = '...'
    warnings.warn_explicit(
        "The 'factory' directive has been deprecated and will be "
        "removed in Zope 3.5.  Use the 'utility' directive instead:\n"
        '  <utility\n'
        '      provides="zope.component.interfaces.IFactory"\n'
        '      component="%s"\n'
        '      name="%s"\n'
        '      />' % (dottedname, id),
        DeprecationWarning, _context.info.file, _context.info.line)
    
    if title is not None:
        component.title = title

    if description is not None:
        component.description = description

    utility(_context, IFactory, component,
            permission=PublicPermission, name=id)


def _checker(_context, permission, allowed_interface, allowed_attributes):
    if (not allowed_attributes) and (not allowed_interface):
        allowed_attributes = ["__call__"]

    if permission == PublicPermission:
        permission = CheckerPublic

    require={}
    if allowed_attributes:
        for name in allowed_attributes:
            require[name] = permission
    if allowed_interface:
        for i in allowed_interface:
            for name in i.names(all=True):
                require[name] = permission

    checker = Checker(require)
    return checker

def resource(_context, factory, type, name, layer=None,
             permission=None,
             allowed_interface=None, allowed_attributes=None,
             provides=Interface):

    if ((allowed_attributes or allowed_interface)
        and (not permission)):
        raise ConfigurationError(
            "Must use name attribute with allowed_interface or "
            "allowed_attributes"
            )

    if permission:
        checker = _checker(_context, permission,
                           allowed_interface, allowed_attributes)

        def proxyResource(request, factory=factory, checker=checker):
            return proxify(factory(request), checker)

        factory = proxyResource

    if layer is not None:
        warnings.warn_explicit(
            "The 'layer' argument of the 'resource' directive has been "
            "deprecated.  Use the 'type' argument instead.",
            DeprecationWarning, _context.info.file, _context.info.line)
        type = layer

    _context.action(
        discriminator = ('resource', name, type, provides),
        callable = handler,
        args = ('registerAdapter',
                factory, (type,), provides, name, _context.info),
        )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (type.__module__ + '.' + type.__name__, type)
               )
    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = (provides.__module__ + '.' + provides.__name__, type)
               )

def view(_context, factory, type, name, for_, layer=None,
         permission=None, allowed_interface=None, allowed_attributes=None,
         provides=Interface):

    if ((allowed_attributes or allowed_interface)
        and (not permission)):
        raise ConfigurationError(
            "Must use name attribute with allowed_interface or "
            "allowed_attributes"
            )

    if not factory:
        raise ConfigurationError("No view factory specified.")

    if permission:

        checker = _checker(_context, permission,
                           allowed_interface, allowed_attributes)

        class ProxyView(object):
            """Class to create simple proxy views."""

            def __init__(self, factory, checker):
                self.factory = factory
                self.checker = checker

            def __call__(self, *objects):
                return proxify(self.factory(*objects), self.checker)

        factory[-1] = ProxyView(factory[-1], checker)


    if not for_:
        raise ValueError("No for interfaces specified");
    for_ = tuple(for_)

    # Generate a single factory from multiple factories:
    factories = factory
    if len(factories) == 1:
        factory = factories[0]
    elif len(factories) < 1:
        raise ValueError("No factory specified")
    elif len(factories) > 1 and len(for_) > 1:
        raise ValueError("Can't use multiple factories and multiple for")
    else:
        def factory(ob, request):
            for f in factories[:-1]:
                ob = f(ob)
            return factories[-1](ob, request)

    # BBB 2006/02/18, to be removed after 12 months
    if layer is not None:
        for_ = for_ + (layer,)
        warnings.warn_explicit(
            "The 'layer' argument of the 'view' directive has been "
            "deprecated.  Use the 'type' argument instead. If you have "
            "an existing 'type' argument IBrowserRequest, replace it with the "
            "'layer' argument (the layer subclasses IBrowserRequest).",
            DeprecationWarning, _context.info.file, _context.info.line)
    else:
        for_ = for_ + (type,)

    _context.action(
        discriminator = ('view', for_, name, provides),
        callable = handler,
        args = ('registerAdapter',
                factory, for_, provides, name, _context.info),
        )
    if type is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', type)
            )

    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', provides)
        )

    if for_ is not None:
        for iface in for_:
            if iface is not None:
                _context.action(
                    discriminator = None,
                    callable = provideInterface,
                    args = ('', iface)
                    )
############################################################################
# BBB: Deprecated. Will go away in 3.3.

def defaultView(_context, type, name, for_):

    _context.action(
        discriminator = ('defaultViewName', for_, type, name),
        callable = handler,
        args = ('registerAdapter',
                 name, (for_, type), IDefaultViewName, '',_context.info)
        )

    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', type)
        )

    _context.action(
        discriminator = None,
        callable = provideInterface,
        args = ('', for_)
        )

from zope.deprecation import deprecated
deprecated('defaultView',
           'The zope:defaultView directive has been deprecated in favor of '
           'the browser:defaultView directive. '
           'Will be gone in Zope 3.3.')

############################################################################
# BBB: Deprecated. Will go away in 3.4.
def defaultLayer(_context, type, layer):
    import warnings
    warnings.warn("""The defaultLayer directive is deprecated and will
go away in Zope 3.4.  It doesn't actually do anything, and never did.

(%s)
""" % _context.info, DeprecationWarning)

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
"""Viewlet metadconfigure

$Id: metaconfigure.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import os

from zope.security import checker
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface, classImplements
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IBrowserView
from zope.component import zcml
from zope.viewlet import viewlet, manager, interfaces

from zope.app.publisher.browser import viewmeta

def viewletManagerDirective(
    _context, name, permission,
    for_=Interface, layer=IDefaultBrowserLayer, view=IBrowserView,
    provides=interfaces.IViewletManager, class_=None, template=None,
    allowed_interface=None, allowed_attributes=None):

    # A list of attributes available under the provided permission
    required = {}

    # Get the permission; mainly to correctly handle CheckerPublic.
    permission = viewmeta._handle_permission(_context, permission)

    # If class is not given we use the basic viewlet manager.
    if class_ is None:
        class_ = manager.ViewletManagerBase

    # Make sure that the template exists and that all low-level API methods
    # have the right permission.
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)
        required['__getitem__'] = permission

        # Create a new class based on the template and class.
        new_class = manager.ViewletManager(
            name, provides, template=template, bases=(class_, ))
    else:
        # Create a new class based on the class.
        new_class = manager.ViewletManager(name, provides, bases=(class_, ))

    # Register some generic attributes with the security dictionary
    for attr_name in ('browserDefault', 'update', 'render', 'publishTraverse'):
        required[attr_name] = permission

    # Register the ``provides`` interface and register fields in the security
    # dictionary
    viewmeta._handle_allowed_interface(
        _context, (provides,), permission, required)

    # Register the allowed interface and add the field's security entries
    viewmeta._handle_allowed_interface(
        _context, allowed_interface, permission, required)

    # Register single allowed attributes in the security dictionary
    viewmeta._handle_allowed_attributes(
        _context, allowed_attributes, permission, required)

    # Register interfaces
    viewmeta._handle_for(_context, for_)
    zcml.interface(_context, view)

    # Create a checker for the viewlet manager
    checker.defineChecker(new_class, checker.Checker(required))

    # register a viewlet manager
    _context.action(
        discriminator = ('viewletManager', for_, layer, view, name),
        callable = zcml.handler,
        args = ('registerAdapter',
                new_class, (for_, layer, view), provides, name,
                 _context.info),)


def viewletDirective(
    _context, name, permission,
    for_=Interface, layer=IDefaultBrowserLayer, view=IBrowserView,
    manager=interfaces.IViewletManager, class_=None, template=None,
    attribute='render', allowed_interface=None, allowed_attributes=None,
    **kwargs):

    # Security map dictionary
    required = {}

    # Get the permission; mainly to correctly handle CheckerPublic.
    permission = viewmeta._handle_permission(_context, permission)

    # Either the class or template must be specified.
    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")

    # Make sure that all the non-default attribute specifications are correct.
    if attribute != 'render':
        if template:
            raise ConfigurationError(
                "Attribute and template cannot be used together.")

        # Note: The previous logic forbids this condition to evere occur.
        if not class_:
            raise ConfigurationError(
                "A class must be provided if attribute is used")

    # Make sure that the template exists and that all low-level API methods
    # have the right permission.
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)
        required['__getitem__'] = permission

    # Make sure the has the right form, if specified.
    if class_:
        if attribute != 'render':
            if not hasattr(class_, attribute):
                raise ConfigurationError(
                    "The provided class doesn't have the specified attribute "
                    )
        if template:
            # Create a new class for the viewlet template and class.
            new_class = viewlet.SimpleViewletClass(
                template, bases=(class_, ), attributes=kwargs, name=name)
        else:
            if not hasattr(class_, 'browserDefault'):
                cdict = {'browserDefault':
                         lambda self, request: (getattr(self, attribute), ())}
            else:
                cdict = {}

            cdict['__name__'] = name
            cdict['__page_attribute__'] = attribute
            cdict.update(kwargs)
            new_class = type(class_.__name__,
                             (class_, viewlet.SimpleAttributeViewlet), cdict)

        if hasattr(class_, '__implements__'):
            classImplements(new_class, IBrowserPublisher)

    else:
        # Create a new class for the viewlet template alone.
        new_class = viewlet.SimpleViewletClass(template, name=name,
                                               attributes=kwargs)

    # Set up permission mapping for various accessible attributes
    viewmeta._handle_allowed_interface(
        _context, allowed_interface, permission, required)
    viewmeta._handle_allowed_attributes(
        _context, allowed_attributes, permission, required)
    viewmeta._handle_allowed_attributes(
        _context, kwargs.keys(), permission, required)
    viewmeta._handle_allowed_attributes(
        _context,
        (attribute, 'browserDefault', 'update', 'render', 'publishTraverse'),
        permission, required)

    # Register the interfaces.
    viewmeta._handle_for(_context, for_)
    zcml.interface(_context, view)

    # Create the security checker for the new class
    checker.defineChecker(new_class, checker.Checker(required))

    # register viewlet
    _context.action(
        discriminator = ('viewlet', for_, layer, view, manager, name),
        callable = zcml.handler,
        args = ('registerAdapter',
                new_class, (for_, layer, view, manager), interfaces.IViewlet,
                 name, _context.info),)

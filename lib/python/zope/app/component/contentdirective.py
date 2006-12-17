#############################################################################
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
""" Register class directive.

$Id: contentdirective.py 69358 2006-08-05 17:54:32Z flox $
"""
__docformat__ = 'restructuredtext'

import warnings
from types import ModuleType
from persistent.interfaces import IPersistent

from zope.component.interfaces import IFactory
from zope.component.factory import Factory
from zope.component.interface import provideInterface
from zope.component.zcml import utility
from zope.interface import classImplements
from zope.schema.interfaces import IField
from zope.configuration.exceptions import ConfigurationError
from zope.location.interfaces import ILocation
from zope.annotation.interfaces import IAttributeAnnotatable

from zope.app.security.protectclass import protectLikeUnto, protectName
from zope.app.security.protectclass import protectSetAttribute

PublicPermission = 'zope.Public'

def dottedName(klass):
    if klass is None:
        return 'None'
    return klass.__module__ + '.' + klass.__name__

class ProtectionDeclarationException(Exception):
    """Security-protection-specific exceptions."""
    pass

class ClassDirective(object):

    def __init__(self, _context, class_):
        self.__id = dottedName(class_)
        self.__class = class_
        if isinstance(self.__class, ModuleType):
            raise ConfigurationError('Content class attribute must be a class')
        self.__context = _context

    def implements(self, _context, interface):
        for interface in interface:
            _context.action(
                discriminator = (
                'ContentDirective', self.__class, object()),
                callable = classImplements,
                args = (self.__class, interface),
                )
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = (interface.__module__ + '.' + interface.getName(),
                        interface)
                )

    def require(self, _context,
                permission=None, attributes=None, interface=None,
                like_class=None, set_attributes=None, set_schema=None):
        """Require a the permission to access a specific aspect"""
        if like_class:
            self.__mimic(_context, like_class)

        if not (interface or attributes or set_attributes or set_schema):
            if like_class:
                return
            raise ConfigurationError("Nothing required")

        if not permission:
            raise ConfigurationError("No permission specified")

        if interface:
            for i in interface:
                if i:
                    self.__protectByInterface(i, permission)
        if attributes:
            self.__protectNames(attributes, permission)
        if set_attributes:
            self.__protectSetAttributes(set_attributes, permission)
        if set_schema:
            for s in set_schema:
                self.__protectSetSchema(s, permission)

    def __mimic(self, _context, class_):
        """Base security requirements on those of the given class"""
        _context.action(
            discriminator=('mimic', self.__class, object()),
            callable=protectLikeUnto,
            args=(self.__class, class_),
            )

    def allow(self, _context, attributes=None, interface=None):
        """Like require, but with permission_id zope.Public"""
        return self.require(_context, PublicPermission, attributes, interface)

    def __protectByInterface(self, interface, permission_id):
        "Set a permission on names in an interface."
        for n, d in interface.namesAndDescriptions(1):
            self.__protectName(n, permission_id)
        self.__context.action(
            discriminator = None,
            callable = provideInterface,
            args = (interface.__module__ + '.' + interface.getName(),
                    interface)
            )

    def __protectName(self, name, permission_id):
        "Set a permission on a particular name."
        self.__context.action(
            discriminator = ('protectName', self.__class, name),
            callable = protectName,
            args = (self.__class, name, permission_id)
            )

    def __protectNames(self, names, permission_id):
        "Set a permission on a bunch of names."
        for name in names:
            self.__protectName(name, permission_id)

    def __protectSetAttributes(self, names, permission_id):
        "Set a permission on a bunch of names."
        for name in names:
            self.__context.action(
                discriminator = ('protectSetAttribute', self.__class, name),
                callable = protectSetAttribute,
                args = (self.__class, name, permission_id)
                )

    def __protectSetSchema(self, schema, permission_id):
        "Set a permission on a bunch of names."
        _context = self.__context
        for name in schema:
            field = schema[name]
            if IField.providedBy(field) and not field.readonly:
                _context.action(
                    discriminator = ('protectSetAttribute', self.__class, name),
                    callable = protectSetAttribute,
                    args = (self.__class, name, permission_id)
                    )
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = (schema.__module__ + '.' + schema.getName(),
                    schema)
            )

    def __call__(self):
        "Handle empty/simple declaration."
        return ()

    def factory(self, _context, id=None, title="", description=''):
        """Register a zmi factory for this class"""

        id = id or self.__id
        factoryObj = Factory(self.__class, title, description)

        # note factories are all in one pile, utilities and content,
        # so addable names must also act as if they were all in the
        # same namespace, despite the utilities/content division
        utility(_context, IFactory, factoryObj,
                permission=PublicPermission, name=id)

# BBB 2006/02/24, to be removed after 12 months
class ContentDirective(ClassDirective):
    """ *BBB: DEPRECATED*

    The ``content`` alias for the ``class`` directive has been
    deprecated and will be removed in Zope 3.5.
    """

    def __init__(self, _context, class_):
        warnings.warn_explicit(
            "The 'content' alias for the 'class' directive has been "
            "deprecated and will be removed in Zope 3.5.\n",
            DeprecationWarning, _context.info.file, _context.info.line)        
        super(ContentDirective, self).__init__(_context, class_)

class LocalUtilityDirective(ClassDirective):
    r"""localUtility directive handler.

    Examples:

      >>> from zope.interface import implements
      >>> class LU1(object):
      ...     pass

      >>> class LU2(LU1):
      ...     implements(ILocation)

      >>> class LU3(LU1):
      ...     __parent__ = None

      >>> class LU4(LU2):
      ...     implements(IPersistent)

      >>> dir = LocalUtilityDirective(None, LU4)
      >>> IAttributeAnnotatable.implementedBy(LU4)
      True

      >>> LocalUtilityDirective(None, LU3)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU3` does not implement `IPersistent`.

      >>> LocalUtilityDirective(None, LU2)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU2` does not implement `IPersistent`.

      >>> LocalUtilityDirective(None, LU1)
      Traceback (most recent call last):
      ...
      ConfigurationError: Class `LU1` does not implement `ILocation`.
    """

    def __init__(self, _context, class_):
        if not ILocation.implementedBy(class_) and \
               not hasattr(class_, '__parent__'):
            raise ConfigurationError('Class `%s` does not implement '
                                     '`ILocation`.' % class_.__name__)

        if not IPersistent.implementedBy(class_):
            raise ConfigurationError('Class `%s` does not implement '
                                     '`IPersistent`.' % class_.__name__)

        classImplements(class_, IAttributeAnnotatable)

        super(LocalUtilityDirective, self).__init__(_context, class_)

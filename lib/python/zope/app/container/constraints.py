##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Support for containment constraints

   Either a container or an object can provide constraints on the
   containment relationship.

   A container expresses constraints through a precondition on it's
   `__setitem__` method in it's interface.

   Preconditions can be simple callable objects, like functions. They
   should raise a ``zope.interface.Invalid`` exception to indicate that a
   constraint isn't satisfied:

   >>> def preNoZ(container, name, ob):
   ...     "Silly precondition example"
   ...     if name.startswith("Z"):
   ...         raise zope.interface.Invalid("Names can not start with Z")

   >>> class I1(zope.interface.Interface):
   ...     def __setitem__(name, on):
   ...         "Add an item"
   ...     __setitem__.precondition = preNoZ

   >>> from zope.app.container.interfaces import IContainer
   >>> class C1(object):
   ...     zope.interface.implements(I1, IContainer)
   ...     def __repr__(self):
   ...         return 'C1'

   Given such a precondition, we can then check whether an object can be
   added:

   >>> c1 = C1()
   >>> checkObject(c1, "bob", None)
   >>> checkObject(c1, "Zbob", None)
   Traceback (most recent call last):
   ...
   Invalid: Names can not start with Z

   We can also express constaints on the containers an object can be
   added to. We do this by setting a field constraint on an object's
   `__parent__` attribute:

   >>> import zope.schema

   A field constraint is a callable object that returns a boolean value:

   >>> def con1(container):
   ...     "silly container constraint"
   ...     if not hasattr(container, 'x'):
   ...         return False
   ...     return True

   >>> class I2(zope.interface.Interface):
   ...     __parent__ = zope.schema.Field(constraint = con1)

   >>> class O(object):
   ...     zope.interface.implements(I2)

   If the constraint isn't satisfied, we'll get a validation error when we
   check whether the object can be added:

   >>> checkObject(c1, "bob", O())
   Traceback (most recent call last):
   ...
   ConstraintNotSatisfied: C1

   Note that the validation error isn't very informative. For that
   reason, it's better for constraints to raise Invalid errors when they
   aren't satisfied:

   >>> def con1(container):
   ...     "silly container constraint"
   ...     if not hasattr(container, 'x'):
   ...         raise zope.interface.Invalid("What, no x?")
   ...     return True

   >>> class I2(zope.interface.Interface):
   ...     __parent__ = zope.schema.Field(constraint = con1)

   >>> class O(object):
   ...     zope.interface.implements(I2)

   >>> checkObject(c1, "bob", O())
   Traceback (most recent call last):
   ...
   Invalid: What, no x?

   >>> c1.x = 1
   >>> checkObject(c1, "bob", O())

   The `checkObject` function is handy when checking whether we can add an
   existing object to a container, but, sometimes, we want to check
   whether an object produced by a factory can be added.  To do this, we
   use `checkFactory`:

   >>> class Factory(object):
   ...     def __call__(self):
   ...         return O()
   ...     def getInterfaces(self):
   ...         return zope.interface.implementedBy(O)

   >>> factory = Factory()

   >>> checkFactory(c1, "bob", factory)
   True

   >>> del c1.x
   >>> checkFactory(c1, "bob", factory)
   False

   Unlike `checkObject`, `checkFactory`:

   - Returns a boolean value

   - Takes a factory (e.g. a class) rather than an argument.

   The container constraint we defined for C1 isn't actually used to
   check the factory:

   >>> c1.x = 1
   >>> checkFactory(c1, "Zbob", factory)
   True

   To work with `checkFactory`, a container precondition has to
   implement a factory method.  This is because a factory, rather than
   an object is passed.  To illustrate this, we'll make preNoZ its own
   factory method:

   >>> preNoZ.factory = preNoZ

   We can do this (silly thing) because preNoZ doesn't use the object
   argument.

   >>> checkFactory(c1, "Zbob", factory)
   False

   $Id: constraints.py 40369 2005-11-25 17:58:38Z jinty $
   """
__docformat__ = 'restructuredtext'

import sys

from zope.cachedescriptors.property import readproperty
from zope.dottedname.resolve import resolve
import zope.schema
from zope.interface import providedBy
from zope.app.container.interfaces import InvalidItemType, InvalidContainerType
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.container.interfaces import IContainer

def checkObject(container, name, object):
    """Check containement constraints for an object and container
    """

    # check __setitem__ precondition
    containerProvided = providedBy(container)
    __setitem__ = containerProvided.get('__setitem__')
    if __setitem__ is not None:
        precondition = __setitem__.queryTaggedValue('precondition')
        if precondition is not None:
            precondition(container, name, object)

    # check the constraint on __parent__
    __parent__ = providedBy(object).get('__parent__')
    if __parent__ is not None:
        try:
            validate = __parent__.validate
        except AttributeError:
            pass
        else:
            validate(container)


    if not containerProvided.extends(IContainer):
        # If it doesn't implement IContainer, it can't contain stuff.
        raise TypeError(
            _('Container is not a valid Zope container.')
            )

def checkFactory(container, name, factory):
    __setitem__ = providedBy(container).get('__setitem__')
    if __setitem__ is not None:
        precondition = __setitem__.queryTaggedValue('precondition')
        if precondition is not None:
            try:
                precondition = precondition.factory
            except AttributeError:
                pass
            else:
                try:
                    precondition(container, name, factory)
                except zope.interface.Invalid:
                    return False

    # check the constraint on __parent__
    __parent__ = factory.getInterfaces().get('__parent__')
    if __parent__ is not None:
        try:
            validate = __parent__.validate
        except AttributeError:
            pass
        else:
            try:
                validate(container)
            except zope.interface.Invalid:
                return False

    return True

class IItemTypePrecondition(zope.interface.Interface):

    def __call__(container, name, object):
        """Test whether container setitem arguments are valid.

        Raise zope.interface.Invalid if the object is invalid.
        """

    def factory(container, name, factory):
        """Test whether objects provided by the factory are acceptable

        Return a boolean value.
        """


class _TypesBased(object):

    @readproperty
    def types(self):
        raw_types, module = self.raw_types
        types = []
        for t in raw_types:
            if isinstance(t, str):
                t = resolve(t, module)
            types.append(t)

        self.types = types
        return types

    def __init__(self, *types, **kw):
        if [t for t in types if isinstance(t, str)]:
            # have dotted names
            module = kw.get('module', sys._getframe(1).f_globals['__name__'])
            self.raw_types = types, module
        else:
            self.types = types


class ItemTypePrecondition(_TypesBased):
    """Specify a `__setitem__` precondition that restricts item types

    Items must be one of the given types.

    >>> class I1(zope.interface.Interface):
    ...     pass
    >>> class I2(zope.interface.Interface):
    ...     pass


    >>> precondition = ItemTypePrecondition(I1, I2)

    >>> class Ob(object):
    ...     pass
    >>> ob = Ob()

    >>> class Factory(object):
    ...     def __call__(self):
    ...         return Ob()
    ...     def getInterfaces(self):
    ...         return zope.interface.implementedBy(Ob)

    >>> factory = Factory()

    >>> try:
    ...     precondition(None, 'foo', ob)
    ... except InvalidItemType, v:
    ...     print v[0], (v[1] is ob), (v[2] == (I1, I2))
    ... else:
    ...     print 'Should have failed'
    None True True

    >>> try:
    ...     precondition.factory(None, 'foo', factory)
    ... except InvalidItemType, v:
    ...     print v[0], (v[1] is factory), (v[2] == (I1, I2))
    ... else:
    ...     print 'Should have failed'
    None True True

    >>> zope.interface.classImplements(Ob, I2)
    >>> precondition(None, 'foo', ob)
    >>> precondition.factory(None, 'foo', factory)

    """

    zope.interface.implements(IItemTypePrecondition)

    def __call__(self, container, name, object):
        for iface in self.types:
            if iface.providedBy(object):
                return
        raise InvalidItemType(container, object, self.types)

    def factory(self, container, name, factory):
        implemented = factory.getInterfaces()

        for iface in self.types:
            if implemented.isOrExtends(iface):
               return
        raise InvalidItemType(container, factory, self.types)


def contains(*types):
    """Declare that a container type contains only the given types

    This is used within a class suite defining an interface to create
    a __setitem__ specification with a precondition allowing only the
    given types:

      >>> class IFoo(zope.interface.Interface):
      ...     pass
      >>> class IBar(zope.interface.Interface):
      ...     pass
      >>> class IFooBarContainer(IContainer):
      ...     contains(IFoo, IBar)

      >>> __setitem__ = IFooBarContainer['__setitem__']
      >>> __setitem__.getTaggedValue('precondition').types == (IFoo, IBar)
      True

    It is invalid to call contains outside a class suite:

      >>> contains(IFoo, IBar)
      Traceback (most recent call last):
      ...
      TypeError: contains not called from suite
    """

    frame = sys._getframe(1)
    f_locals = frame.f_locals
    f_globals = frame.f_globals

    if not (f_locals is not f_globals
            and f_locals.get('__module__')
            and f_locals.get('__module__') == f_globals.get('__name__')
            ):
        raise TypeError("contains not called from suite")

    def __setitem__(key, value):
        pass
    __setitem__.__doc__ = IContainer['__setitem__'].__doc__
    __setitem__.precondition = ItemTypePrecondition(
        *types,
        **dict(module=f_globals['__name__'])
        )
    f_locals['__setitem__'] = __setitem__


class IContainerTypesConstraint(zope.interface.Interface):

    def __call__(object):
        """Test whether object is valid.

        Return True if valid.
        Raise zope.interface.Invalid if the objet is invalid.
        """


class ContainerTypesConstraint(_TypesBased):
    """Constrain a container to be one of a number of types

    >>> class I1(zope.interface.Interface):
    ...     pass
    >>> class I2(zope.interface.Interface):
    ...     pass
    >>> class Ob(object):
    ...     pass
    >>> ob = Ob()
    >>> constraint = ContainerTypesConstraint(I1, I2)
    >>> try:
    ...     constraint(ob)
    ... except InvalidContainerType, v:
    ...     print (v[0] is ob), (v[1] == (I1, I2))
    ... else:
    ...     print 'Should have failed'
    True True

    >>> zope.interface.classImplements(Ob, I2)
    >>> constraint(Ob())
    True

    """

    zope.interface.implements(IContainerTypesConstraint)

    def __call__(self, object):
       for iface in self.types:
           if iface.providedBy(object):
               return True
       else:
           raise InvalidContainerType(object, self.types)


def containers(*types):
    """Declare the container types a type can be contained in

    This is used within a class suite defining an interface to create
    a __parent__ specification with a constraint allowing only the
    given types:

      >>> class IFoo(IContainer):
      ...     pass
      >>> class IBar(IContainer):
      ...     pass

      >>> from zope.app.container.interfaces import IContained
      >>> class IFooBarContained(IContained):
      ...     containers(IFoo, IBar)

      >>> __parent__ = IFooBarContained['__parent__']
      >>> __parent__.constraint.types == (IFoo, IBar)
      True

    It is invalid to call containers outside a class suite:

      >>> containers(IFoo, IBar)
      Traceback (most recent call last):
      ...
      TypeError: containers not called from suite
    """

    frame = sys._getframe(1)
    f_locals = frame.f_locals
    f_globals = frame.f_globals

    if not (f_locals is not f_globals
            and f_locals.get('__module__')
            and f_locals.get('__module__') == f_globals.get('__name__')
            ):
        raise TypeError("containers not called from suite")

    __parent__ = zope.schema.Field(
        constraint = ContainerTypesConstraint(
            *types,
            **dict(module=f_globals['__name__'])
            )
        )
    f_locals['__parent__'] = __parent__


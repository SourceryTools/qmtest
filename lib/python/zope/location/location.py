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
"""Location support

$Id: location.py 66534 2006-04-05 14:09:33Z philikon $
"""
__docformat__ = 'restructuredtext'

import zope.interface
from zope.location.interfaces import ILocation
from zope.proxy import ProxyBase, getProxiedObject, non_overridable
from zope.decorator import DecoratorSpecificationDescriptor
from zope.decorator import DecoratedSecurityCheckerDescriptor

class Location(object):
    """Stupid mix-in that defines `__parent__` and `__name__` attributes

    Usage within an Object field:

    >>> from zope.interface import implements, Interface
    >>> from zope.schema import Object
    >>> from zope.schema.fieldproperty import FieldProperty
    >>> from zope.location.interfaces import ILocation
    >>> from zope.location.location import Location

    >>> class IA(Interface):
    ...     location = Object(schema=ILocation, required=False, default=None)
    >>> class A(object):
    ...     implements(IA)
    ...     location = FieldProperty(IA['location'])

    >>> a = A()
    >>> a.location = Location()
    
    >>> loc = Location(); loc.__name__ = u'foo'
    >>> a.location = loc

    >>> loc = Location(); loc.__name__ = None
    >>> a.location = loc

    >>> loc = Location(); loc.__name__ = 'foo'
    >>> a.location = loc
    Traceback (most recent call last):
    ...
    WrongContainedType: [foo <type 'unicode'>]

    """

    zope.interface.implements(ILocation)

    __parent__ = __name__ = None

def locate(object, parent, name=None):
    """Locate an object in another

    This method should only be called from trusted code, because it
    sets attributes that are normally unsettable.
    """

    object.__parent__ = parent
    object.__name__ = name

def LocationIterator(object):
    while object is not None:
        yield object
        object = getattr(object, '__parent__', None)

def inside(l1, l2):
    """Is l1 inside l2

    L1 is inside l2 if l2 is an ancestor of l1.

    >>> o1 = Location()
    >>> o2 = Location(); o2.__parent__ = o1
    >>> o3 = Location(); o3.__parent__ = o2
    >>> o4 = Location(); o4.__parent__ = o3

    >>> inside(o1, o1)
    1
    >>> inside(o2, o1)
    1
    >>> inside(o3, o1)
    1
    >>> inside(o4, o1)
    1

    >>> inside(o1, o4)
    0

    >>> inside(o1, None)
    0

    """

    while l1 is not None:
        if l1 is l2:
            return True
        l1 = l1.__parent__

    return False

class ClassAndInstanceDescr(object):

    def __init__(self, *args):
        self.funcs = args

    def __get__(self, inst, cls):
        if inst is None:
            return self.funcs[1](cls)
        return self.funcs[0](inst)

class LocationProxy(ProxyBase):
    __doc__ = """Location-object proxy

    This is a non-picklable proxy that can be put around objects that
    don't implement `ILocation`.

    >>> l = [1, 2, 3]
    >>> p = LocationProxy(l, "Dad", "p")
    >>> p
    [1, 2, 3]
    >>> p.__parent__
    'Dad'
    >>> p.__name__
    'p'

    >>> import pickle
    >>> p2 = pickle.dumps(p)
    Traceback (most recent call last):
    ...
    TypeError: Not picklable

    Proxies should get their doc strings from the object they proxy:

    >>> p.__doc__ == l.__doc__
    True

    """

    zope.interface.implements(ILocation)

    __slots__ = '__parent__', '__name__'
    __safe_for_unpickling__ = True

    def __new__(self, ob, container=None, name=None):
        return ProxyBase.__new__(self, ob)

    def __init__(self, ob, container=None, name=None):
        ProxyBase.__init__(self, ob)
        self.__parent__ = container
        self.__name__ = name

    @non_overridable
    def __reduce__(self, proto=None):
        raise TypeError("Not picklable")


    __doc__ = ClassAndInstanceDescr(
        lambda inst: getProxiedObject(inst).__doc__,
        lambda cls, __doc__ = __doc__: __doc__,
        )
    
    __reduce_ex__ = __reduce__

    __providedBy__ = DecoratorSpecificationDescriptor()

    __Security_checker__ = DecoratedSecurityCheckerDescriptor()

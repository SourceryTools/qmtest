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
"""Decorator support

Decorators are proxies that are mostly transparent but that may provide
additional features.

$Id: __init__.py 66343 2006-04-03 04:59:49Z philikon $
"""
__docformat__ = "reStructuredText"

from zope.proxy import getProxiedObject, ProxyBase
from zope.security.checker import selectChecker, CombinedChecker
from zope.security.proxy import Proxy, getChecker
from zope.interface.declarations import ObjectSpecificationDescriptor
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecification
from zope.interface import providedBy

class DecoratorSpecificationDescriptor(ObjectSpecificationDescriptor):
    """Support for interface declarations on decorators

    >>> from zope.interface import *
    >>> class I1(Interface):
    ...     pass
    >>> class I2(Interface):
    ...     pass
    >>> class I3(Interface):
    ...     pass
    >>> class I4(Interface):
    ...     pass

    >>> class D1(Decorator):
    ...   implements(I1)


    >>> class D2(Decorator):
    ...   implements(I2)

    >>> class X(object):
    ...   implements(I3)

    >>> x = X()
    >>> directlyProvides(x, I4)

    Interfaces of X are ordered with the directly-provided interfaces first

    >>> [interface.getName() for interface in list(providedBy(x))]
    ['I4', 'I3']

    When we decorate objects, what order should the interfaces come
    in?  One could argue that decorators are less specific, so they
    should come last.

    >>> [interface.getName() for interface in list(providedBy(D1(x)))]
    ['I4', 'I3', 'I1']

    >>> [interface.getName() for interface in list(providedBy(D2(D1(x))))]
    ['I4', 'I3', 'I1', 'I2']
    """
    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)
        else:
            provided = providedBy(getProxiedObject(inst))

            # Use type rather than __class__ because inst is a proxy and
            # will return the proxied object's class.
            cls = type(inst)
            return ObjectSpecification(provided, cls)

    def __set__(self, inst, value):
        raise TypeError("Can't set __providedBy__ on a decorated object")

class DecoratedSecurityCheckerDescriptor(object):
    """Descriptor for a Decorator that provides a decorated security checker.

    To illustrate, we'll create a class that will be proxied:

      >>> class Foo(object):
      ...     a = 'a'

    and a class to proxy it that uses a decorated security checker:

      >>> class Wrapper(ProxyBase):
      ...     b = 'b'
      ...     __Security_checker__ = DecoratedSecurityCheckerDescriptor()

    Next we'll create and register a checker for `Foo`:

      >>> from zope.security.checker import NamesChecker, defineChecker
      >>> fooChecker = NamesChecker(['a'])
      >>> defineChecker(Foo, fooChecker)

    along with a checker for `Wrapper`:

      >>> wrapperChecker = NamesChecker(['b'])
      >>> defineChecker(Wrapper, wrapperChecker)

    Using `selectChecker()`, we can confirm that a `Foo` object uses
    `fooChecker`:

      >>> foo = Foo()
      >>> selectChecker(foo) is fooChecker
      True
      >>> fooChecker.check(foo, 'a')
      >>> fooChecker.check(foo, 'b')  # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ForbiddenAttribute: ('b', <zope.decorator.Foo object ...>)

    and that a `Wrapper` object uses `wrappeChecker`:

      >>> wrapper = Wrapper(foo)
      >>> selectChecker(wrapper) is wrapperChecker
      True
      >>> wrapperChecker.check(wrapper, 'b')
      >>> wrapperChecker.check(wrapper, 'a')  # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ForbiddenAttribute: ('a', <zope.decorator.Foo object ...>)

    (Note that the object description says `Foo` because the object is a
    proxy and generally looks and acts like the object it's proxying.)

    When we access wrapper's ``__Security_checker__`` attribute, we invoke
    the decorated security checker descriptor. The decorator's job is to make
    sure checkers from both objects are used when available. In this case,
    because both objects have checkers, we get a combined checker:

      >>> checker = wrapper.__Security_checker__
      >>> type(checker)
      <class 'zope.security.checker.CombinedChecker'>
      >>> checker.check(wrapper, 'a')
      >>> checker.check(wrapper, 'b')

    The decorator checker will work even with security proxied objects. To
    illustrate, we'll proxify `foo`:

      >>> from zope.security.proxy import ProxyFactory
      >>> secure_foo = ProxyFactory(foo)
      >>> secure_foo.a
      'a'
      >>> secure_foo.b  # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ForbiddenAttribute: ('b', <zope.decorator.Foo object ...>)

    when we wrap the secured `foo`:

      >>> wrapper = Wrapper(secure_foo)

    we still get a combined checker:

      >>> checker = wrapper.__Security_checker__
      >>> type(checker)
      <class 'zope.security.checker.CombinedChecker'>
      >>> checker.check(wrapper, 'a')
      >>> checker.check(wrapper, 'b')

    The decorator checker has three other scenarios:

      - the wrapper has a checker but the proxied object doesn't
      - the proxied object has a checker but the wrapper doesn't
      - neither the wrapper nor the proxied object have checkers

    When the wrapper has a checker but the proxied object doesn't:

      >>> from zope.security.checker import NoProxy, _checkers
      >>> del _checkers[Foo]
      >>> defineChecker(Foo, NoProxy)
      >>> selectChecker(foo) is None
      True
      >>> selectChecker(wrapper) is wrapperChecker
      True

    the decorator uses only the wrapper checker:

      >>> wrapper = Wrapper(foo)
      >>> wrapper.__Security_checker__ is wrapperChecker
      True

    When the proxied object has a checker but the wrapper doesn't:

      >>> del _checkers[Wrapper]
      >>> defineChecker(Wrapper, NoProxy)
      >>> selectChecker(wrapper) is None
      True
      >>> del _checkers[Foo]
      >>> defineChecker(Foo, fooChecker)
      >>> selectChecker(foo) is fooChecker
      True

    the decorator uses only the proxied object checker:

      >>> wrapper.__Security_checker__ is fooChecker
      True

    Finally, if neither the wrapper not the proxied have checkers:

      >>> del _checkers[Foo]
      >>> defineChecker(Foo, NoProxy)
      >>> selectChecker(foo) is None
      True
      >>> selectChecker(wrapper) is None
      True

    the decorator doesn't have a checker:

      >>> wrapper.__Security_checker__ is None
      True

    """
    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            proxied_object = getProxiedObject(inst)
            if type(proxied_object) is Proxy:
                checker = getChecker(proxied_object)
            else:
                checker = getattr(proxied_object, '__Security_checker__', None)
                if checker is None:
                    checker = selectChecker(proxied_object)
            wrapper_checker = selectChecker(inst)
            if wrapper_checker is None:
                return checker
            elif checker is None:
                return wrapper_checker
            else:
                return CombinedChecker(wrapper_checker, checker)

    def __set__(self, inst, value):
        raise TypeError("Can't set __Security_checker__ on a decorated object")

class Decorator(ProxyBase):
    """Decorator base class"""

    __providedBy__ = DecoratorSpecificationDescriptor()
    __Security_checker__ = DecoratedSecurityCheckerDescriptor()


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
"""Security Checkers

You can set the environment variable ZOPE_WATCH_CHECKERS to get additional
security checker debugging output on the standard error.

Setting ZOPE_WATCH_CHECKERS to 1 will display messages about unauthorized or
forbidden attribute access.  Setting it to a larger number will also display
messages about granted attribute access.

Note that the ZOPE_WATCH_CHECKERS mechanism will eventually be
replaced with a more general security auditing mechanism.

$Id: checker.py 69148 2006-07-16 17:10:19Z jim $
"""
import os
import sys
import sets
import types
import datetime
import pytz
import weakref

from zope.exceptions import DuplicationError
import zope.interface.interface
import zope.interface.interfaces
import zope.interface.declarations
from zope.interface import directlyProvides, Interface, implements
from zope.interface.interfaces import IInterface, IDeclaration

from zope.security.interfaces import IChecker, INameBasedChecker
from zope.security.interfaces import ISecurityProxyFactory
from zope.security.interfaces import Unauthorized, ForbiddenAttribute
from zope.security.management import thread_local
from zope.security._proxy import _Proxy as Proxy, getChecker

if os.environ.get('ZOPE_WATCH_CHECKERS'):
    try:
        WATCH_CHECKERS = int(os.environ.get('ZOPE_WATCH_CHECKERS'))
    except ValueError:
        WATCH_CHECKERS = 1
else:
    WATCH_CHECKERS = 0


def ProxyFactory(object, checker=None):
    """Factory function that creates a proxy for an object

    The proxy checker is looked up if not provided.
    """
    if type(object) is Proxy:
        if checker is None or checker is getChecker(object):
            return object
        else:
            # We have a proxy, but someone asked us to change its checker.
            # Let's raise an exception.
            #
            # Other reasonable actions would be to either keep the existing
            # proxy, or to create a new one with the given checker.
            # The latter might be a security hole though, if untrusted code
            # can call ProxyFactory.
            raise TypeError("Tried to use ProxyFactory to change a Proxy's"
                            " checker.")
    if checker is None:
        checker = getattr(object, '__Security_checker__', None)

        if checker is None:
            checker = selectChecker(object)
            if checker is None:
                return object

    return Proxy(object, checker)

directlyProvides(ProxyFactory, ISecurityProxyFactory)

def canWrite(obj, name):
    """Check whether the interaction may write an attribute named name on obj.

    Convenience method.  Rather than using checkPermission in high level code,
    use canWrite and canAccess to avoid binding code to permissions.
    """
    obj = ProxyFactory(obj)
    checker = getChecker(obj)
    try:
        checker.check_setattr(obj, name)
    except Unauthorized:
        return False
    except ForbiddenAttribute:
        # we are going to be a bit DWIM-y here: see
        # http://www.zope.org/Collectors/Zope3-dev/506
        
        # generally, if the check is ForbiddenAttribute we want it to be
        # raised: it probably indicates a programming or configuration error.
        # However, we special case a write ForbiddenAttribute when one can
        # actually read the attribute: this represents a reasonable
        # configuration of a readonly attribute, and returning False (meaning
        # "no, you can't write it") is arguably more useful than raising the
        # exception.
        try:
            checker.check_getattr(obj, name)
            # we'll let *this* ForbiddenAttribute fall through, if any.  It
            # means that both read and write are forbidden.
        except Unauthorized:
            pass
        return False
    # all other exceptions, other than Unauthorized and ForbiddenAttribute,
    # should be passed through uncaught, as they indicate programmer error
    return True

def canAccess(obj, name):
    """Check whether the interaction may access an attribute named name on obj.

    Convenience method.  Rather than using checkPermission in high level code,
    use canWrite and canAccess to avoid binding code to permissions.
    """
    # access attributes and methods, including, in the current checker
    # implementation, special names like __getitem__
    obj = ProxyFactory(obj)
    checker = getChecker(obj)
    try:
        checker.check_getattr(obj, name)
    except Unauthorized:
        return False
    # if it is Forbidden (or anything else), let it be raised: it probably
    # indicates a programming or configuration error
    return True

class Checker(object):
    implements(INameBasedChecker)

    def __init__(self, get_permissions, set_permissions=None):
        """Create a checker

        A dictionary must be provided for computing permissions for
        names. The dictionary get will be called with attribute names
        and must return a permission id, None, or the special marker,
        CheckerPublic. If None is returned, then access to the name is
        forbidden. If CheckerPublic is returned, then access will be
        granted without checking a permission.

        An optional setattr dictionary may be provided for checking
        set attribute access.

        """
        assert isinstance(get_permissions, dict)
        self.get_permissions = get_permissions
        if set_permissions is not None:
            assert isinstance(set_permissions, dict)
        self.set_permissions = set_permissions

    def permission_id(self, name):
        'See INameBasedChecker'
        return self.get_permissions.get(name)

    def setattr_permission_id(self, name):
        'See INameBasedChecker'
        if self.set_permissions:
            return self.set_permissions.get(name)

    def check_getattr(self, object, name):
        'See IChecker'
        self.check(object, name)

    def check_setattr(self, object, name):
        'See IChecker'
        if self.set_permissions:
            permission = self.set_permissions.get(name)
        else:
            permission = None

        if permission is not None:
            if permission is CheckerPublic:
                return # Public
            if thread_local.interaction.checkPermission(permission, object):
                return # allowed
            else:
                __traceback_supplement__ = (TracebackSupplement, object)
                raise Unauthorized(object, name, permission)

        __traceback_supplement__ = (TracebackSupplement, object)
        raise ForbiddenAttribute(name, object)

    def check(self, object, name):
        'See IChecker'
        permission = self.get_permissions.get(name)
        if permission is not None:
            if permission is CheckerPublic:
                return # Public
            if thread_local.interaction.checkPermission(permission, object):
                return
            else:
                __traceback_supplement__ = (TracebackSupplement, object)
                raise Unauthorized(object, name, permission)
        elif name in _available_by_default:
            return

        if name != '__iter__' or hasattr(object, name):
            __traceback_supplement__ = (TracebackSupplement, object)
            raise ForbiddenAttribute(name, object)

    def proxy(self, value):
        'See IChecker'
        if type(value) is Proxy:
            return value
        checker = getattr(value, '__Security_checker__', None)
        if checker is None:
            checker = selectChecker(value)
            if checker is None:
                return value

        return Proxy(value, checker)



# Helper class for __traceback_supplement__
class TracebackSupplement(object):

    def __init__(self, obj):
        self.obj = obj

    def getInfo(self):
        result = []
        try:
            cls = self.obj.__class__
            if hasattr(cls, "__module__"):
                s = "%s.%s" % (cls.__module__, cls.__name__)
            else:
                s = str(cls.__name__)
            result.append("   - class: " + s)
        except:
            pass
        try:
            cls = type(self.obj)
            if hasattr(cls, "__module__"):
                s = "%s.%s" % (cls.__module__, cls.__name__)
            else:
                s = str(cls.__name__)
            result.append("   - type: " + s)
        except:
            pass
        return "\n".join(result)


class Global(object):
    """A global object that behaves like a string.

    We want this to behave as a global, meaning it's pickled
    by name, rather than value. We need to arrange that it has a suitable
    __reduce__.
    """

    def __init__(self, name, module=None):
        if module is None:
            module = sys._getframe(1).f_locals['__name__']

        self.__name__ = name
        self.__module__ = module

    def __reduce__(self):
        return self.__name__

    def __repr__(self):
        return "%s(%s,%s)" % (self.__class__.__name__,
                              self.__name__, self.__module__)

# Marker for public attributes
CheckerPublic = Global('CheckerPublic')

# Now we wrap it in a security proxy so that it retains it's
# identity when it needs to be security proxied.
d={}
CheckerPublic = Proxy(CheckerPublic, Checker(d))
d['__reduce__'] = CheckerPublic
del d

# TODO: It's a bit scary above that we can pickle a proxy if access is
# granted to __reduce__. We might want to bother to prevent this in
# general and only allow it in this specific case.

def NamesChecker(names=(), permission_id=CheckerPublic, **__kw__):
    """Return a checker that grants access to a set of names.

    A sequence of names is given as the first argument. If a second
    argument, permission_id, is given, it is the permission required
    to access the names.  Additional names and permission ids can be
    supplied as keyword arguments.
    """

    data = {}
    data.update(__kw__)
    for name in names:
        if data.get(name, permission_id) is not permission_id:
            raise DuplicationError(name)
        data[name] = permission_id

    return Checker(data)

def InterfaceChecker(interface, permission_id=CheckerPublic, **__kw__):
    return NamesChecker(interface.names(all=True), permission_id, **__kw__)

def MultiChecker(specs):
    """Create a checker from a sequence of specifications

    A specification is:

    - A two-tuple with:

      o a sequence of names or an interface

      o a permission id

      All the names in the sequence of names or the interface are
      protected by the permission.

    - A dictionoid (having an items method), with items that are
      name/permission-id pairs.
    """
    data = {}

    for spec in specs:
        if type(spec) is tuple:
            names, permission_id = spec
            if IInterface.providedBy(names):
                names = names.names(all=True)
            for name in names:
                if data.get(name, permission_id) is not permission_id:
                    raise DuplicationError(name)
                data[name] = permission_id
        else:
            for name, permission_id in spec.items():
                if data.get(name, permission_id) is not permission_id:
                    raise DuplicationError(name)
                data[name] = permission_id

    return Checker(data)

def selectChecker(object):
    """Get a checker for the given object

    The appropriate checker is returned or None is returned. If the
    return value is None, then object should not be wrapped in a proxy.
    """

    # We need to be careful here. We might have a proxy, in which case
    # we can't use the type.  OTOH, we might not be able to use the
    # __class__ either, since not everything has one.

    # TODO: we really need formal proxy introspection

    #if type(object) is Proxy:
    #    # Is this already a security proxy?
    #    return None

    checker = _getChecker(type(object), _defaultChecker)

    #checker = _getChecker(getattr(object, '__class__', type(object)),
    #                      _defaultChecker)

    if checker is NoProxy:
        return None

    while not isinstance(checker, Checker):
        checker = checker(object)
        if checker is NoProxy or checker is None:
            return None

    return checker

def getCheckerForInstancesOf(class_):
    return _checkers.get(class_)

def defineChecker(type_, checker):
    """Define a checker for a given type of object

    The checker can be a Checker, or a function that, when called with
    an object, returns a Checker.
    """
    if not isinstance(type_, (type, types.ClassType, types.ModuleType)):
        raise TypeError(
                'type_ must be a type, class or module, not a %s' % type_)
    if type_ in _checkers:
        raise DuplicationError(type_)
    _checkers[type_] = checker

def undefineChecker(type_):
    del _checkers[type_]

NoProxy = object()

# _checkers is a mapping.
#
#  - Keys are types
#
#  - Values are
#
#    o None => rock
#    o a Checker
#    o a function returning None or a Checker
#
_checkers = {}

_defaultChecker = Checker({})
_available_by_default = []

# Get optimized versions
try:
    import zope.security._zope_security_checker
except ImportError:
    pass
else:
    from zope.security._zope_security_checker import _checkers, selectChecker
    from zope.security._zope_security_checker import NoProxy, Checker
    from zope.security._zope_security_checker import _defaultChecker
    from zope.security._zope_security_checker import _available_by_default
    zope.interface.classImplements(Checker, INameBasedChecker)


_getChecker = _checkers.get

class CombinedChecker(Checker):
    """A checker that combines two other checkers in a logical-or fashion.

    The following table describes the result of a combined checker in detail.

    checker1           checker2           CombinedChecker(checker1, checker2)
    ------------------ ------------------ -----------------------------------
    ok                 anything           ok (checker2 is never called)
    Unauthorized       ok                 ok
    Unauthorized       Unauthorized       Unauthorized
    Unauthorized       ForbiddenAttribute Unauthorized
    ForbiddenAttribute ok                 ok
    ForbiddenAttribute Unauthorized       Unauthorized
    ForbiddenAttribute ForbiddenAttribute ForbiddenAttribute
    ------------------ ------------------ -----------------------------------
    """
    implements(IChecker)

    def __init__(self, checker1, checker2):
        """Create a combined checker."""
        Checker.__init__(self,
                         checker1.get_permissions,
                         checker1.set_permissions)
        self._checker2 = checker2

    def check(self, object, name):
        'See IChecker'
        try:
            Checker.check(self, object, name)
        except ForbiddenAttribute:
            self._checker2.check(object, name)
        except Unauthorized, unauthorized_exception:
            try: self._checker2.check(object, name)
            except ForbiddenAttribute:
                raise unauthorized_exception

    check_getattr = __setitem__ = check

    def check_setattr(self, object, name):
        'See IChecker'
        try:
            Checker.check_setattr(self, object, name)
        except ForbiddenAttribute:
            self._checker2.check_setattr(object, name)
        except Unauthorized, unauthorized_exception:
            try: self._checker2.check_setattr(object, name)
            except ForbiddenAttribute:
                raise unauthorized_exception

class CheckerLoggingMixin(object):
    """Debugging mixin for checkers.

    Prints verbose debugging information about every performed check to
    sys.stderr.

    If verbosity is set to 1, only displays Unauthorized and Forbidden messages.
    If verbosity is set to a larger number, displays all messages.
    """

    verbosity = 1

    def check(self, object, name):
        try:
            super(CheckerLoggingMixin, self).check(object, name)
            if self.verbosity > 1:
                if name in _available_by_default:
                    print >> sys.stderr, (
                        '[CHK] + Always available: %s on %r' % (name, object))
                else:
                    print >> sys.stderr, (
                        '[CHK] + Granted: %s on %r' % (name, object))
        except Unauthorized:
            print >> sys.stderr, (
                '[CHK] - Unauthorized: %s on %r' % (name, object))
            raise
        except ForbiddenAttribute:
            print >> sys.stderr, (
                '[CHK] - Forbidden: %s on %r' % (name, object))
            raise

    def check_getattr(self, object, name):
        try:
            super(CheckerLoggingMixin, self).check(object, name)
            if self.verbosity > 1:
                if name in _available_by_default:
                    print >> sys.stderr, (
                        '[CHK] + Always available getattr: %s on %r'
                        % (name, object))
                else:
                    print >> sys.stderr, (
                        '[CHK] + Granted getattr: %s on %r'
                        % (name, object))
        except Unauthorized:
            print >> sys.stderr, (
                '[CHK] - Unauthorized getattr: %s on %r' % (name, object))
            raise
        except ForbiddenAttribute:
            print >> sys.stderr, (
                '[CHK] - Forbidden getattr: %s on %r' % (name, object))
            raise

    def check_setattr(self, object, name):
        try:
            super(CheckerLoggingMixin, self).check_setattr(object, name)
            if self.verbosity > 1:
                print >> sys.stderr, (
                    '[CHK] + Granted setattr: %s on %r' % (name, object))
        except Unauthorized:
            print >> sys.stderr, (
                '[CHK] - Unauthorized setattr: %s on %r' % (name, object))
            raise
        except ForbiddenAttribute:
            print >> sys.stderr, (
                '[CHK] - Forbidden setattr: %s on %r' % (name, object))
            raise


if WATCH_CHECKERS:
    class Checker(CheckerLoggingMixin, Checker):
        verbosity = WATCH_CHECKERS
    class CombinedChecker(CheckerLoggingMixin, CombinedChecker):
        verbosity = WATCH_CHECKERS

def _instanceChecker(inst):
    return _checkers.get(inst.__class__, _defaultChecker)

def moduleChecker(module):
    return _checkers.get(module)


_available_by_default[:] = ['__lt__', '__le__', '__eq__',
                            '__gt__', '__ge__', '__ne__',
                            '__hash__', '__nonzero__',
                            '__class__', '__providedBy__', '__implements__',
                            '__repr__', '__conform__',
                            ]

_callableChecker = NamesChecker(['__str__', '__name__', '__call__'])
_typeChecker = NamesChecker(
    ['__str__', '__name__', '__module__', '__bases__', '__mro__',
     '__implemented__'])
_namedChecker = NamesChecker(['__name__'])

_iteratorChecker = NamesChecker(['next', '__iter__'])

_setChecker = NamesChecker(['__iter__', '__len__', '__str__', '__contains__',
                            'copy', 'difference', 'intersection', 'issubset',
                            'issuperset', 'symmetric_difference', 'union',
                            '__and__', '__or__', '__sub__', '__xor__',
                            '__rand__', '__ror__', '__rsub__', '__rxor__',
                            '__eq__', '__ne__', '__lt__', '__gt__',
                            '__le__', '__ge__'])

class BasicTypes(dict):
    """Basic Types Dictionary

    Make sure that the checkers a really updated, when a new type is added.
    """
    def __setitem__(self, name, value):
        super(BasicTypes.__class__, self).__setitem__(name, value)
        _checkers[name] = value

    def __delitem__(self, name):
        super(BasicTypes.__class__, self).__delitem__(name)
        del _checkers[name]

    def clear(self):
        # Make sure you cannot clear the values
        raise NotImplementedError

    def update(self, d):
        super(BasicTypes.__class__, self).update(d)
        _checkers.update(d)

BasicTypes = BasicTypes({
    object: NoProxy,
    int: NoProxy,
    float: NoProxy,
    long: NoProxy,
    complex: NoProxy,
    types.NoneType: NoProxy,
    str: NoProxy,
    unicode: NoProxy,
    bool: NoProxy,
    datetime.timedelta: NoProxy,
    datetime.datetime: NoProxy,
    datetime.date: NoProxy,
    datetime.time: NoProxy,
    datetime.tzinfo: NoProxy,
    type(pytz.UTC): NoProxy,
})

# Available for tests. Located here so it can be kept in sync with BasicTypes.
BasicTypes_examples = {
    object: object(),
    int: 65536,
    float: -1.4142,
    long: 65536l,
    complex: -1.4142j,
    types.NoneType: None,
    str: 'abc',
    unicode: u'uabc',
    bool: True,
    datetime.timedelta: datetime.timedelta(3),
    datetime.datetime: datetime.datetime(2003, 1, 1),
    datetime.date: datetime.date(2003, 1, 1),
    datetime.time: datetime.time(23, 58)
}


class _Sequence(object):
    def __len__(self): return 0
    def __getitem__(self, i): raise IndexError

_Declaration_checker = InterfaceChecker(
    IDeclaration,
    _implied=CheckerPublic,
    subscribe=CheckerPublic,
    unsubscribe=CheckerPublic,
    __call__=CheckerPublic,
    )

def f():
    yield f


_default_checkers = {
    dict: NamesChecker(['__getitem__', '__len__', '__iter__',
                        'get', 'has_key', 'copy', '__str__', 'keys',
                        'values', 'items', 'iterkeys', 'iteritems',
                        'itervalues', '__contains__']),
    list: NamesChecker(['__getitem__', '__getslice__', '__len__', '__iter__',
                        '__contains__', 'index', 'count', '__str__',
                        '__add__', '__radd__', ]),
    sets.Set: _setChecker,
    sets.ImmutableSet: _setChecker,
    set: _setChecker,
    frozenset: _setChecker,

    # YAGNI: () a rock
    tuple: NamesChecker(['__getitem__', '__getslice__', '__add__', '__radd__',
                         '__contains__', '__len__', '__iter__',
                         '__str__']),
    types.InstanceType: _instanceChecker,
    Proxy: NoProxy,
    type(weakref.ref(_Sequence())): NamesChecker(['__call__']),
    types.ClassType: _typeChecker,
    types.FunctionType: _callableChecker,
    types.MethodType: _callableChecker,
    types.BuiltinFunctionType: _callableChecker,
    types.BuiltinMethodType: _callableChecker,
    type(().__getslice__): _callableChecker, # slot description
    type: _typeChecker,
    types.ModuleType: lambda module: _checkers.get(module, _namedChecker),
    type(iter([])): _iteratorChecker, # Same types in Python 2.2.1,
    type(iter(())): _iteratorChecker, # different in Python 2.3.
    type(iter({})): _iteratorChecker,
    type({}.iteritems()): _iteratorChecker,
    type({}.iterkeys()): _iteratorChecker,
    type({}.itervalues()): _iteratorChecker,
    type(iter(_Sequence())): _iteratorChecker,
    type(f()): _iteratorChecker,
    type(Interface): InterfaceChecker(
        IInterface,
        __str__=CheckerPublic, _implied=CheckerPublic, subscribe=CheckerPublic,
        # BBB 2004-07-13: backward compatability for deprecated
        # interface methods
        isImplementedByInstancesOf=CheckerPublic,
        isImplementedBy=CheckerPublic,
        ),
    zope.interface.interface.Method: InterfaceChecker(
                                        zope.interface.interfaces.IMethod),
    zope.interface.declarations.ProvidesClass: _Declaration_checker,
    zope.interface.declarations.ClassProvides: _Declaration_checker,
    zope.interface.declarations.Implements: _Declaration_checker,
    zope.interface.declarations.Declaration: _Declaration_checker,
}

def _clear():
    _checkers.clear()
    _checkers.update(_default_checkers)
    _checkers.update(BasicTypes)

_clear()

from zope.testing.cleanup import addCleanUp
addCleanUp(_clear)

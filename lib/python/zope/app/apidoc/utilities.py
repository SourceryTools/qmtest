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
"""Utilties to make the life of Documentation Modules easier.

$Id: utilities.py 70020 2006-09-07 09:08:16Z flox $
"""
__docformat__ = 'restructuredtext'

import re
import sys
import types
import inspect
from os.path import dirname

from zope.component import createObject, getMultiAdapter
from zope.interface import implements, implementedBy
from zope.publisher.browser import TestRequest
from zope.security.checker import getCheckerForInstancesOf, Global
from zope.security.interfaces import INameBasedChecker
from zope.security.proxy import isinstance, removeSecurityProxy

import zope.app
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.container.interfaces import IReadContainer

from zope.app.apidoc.classregistry import safe_import, IGNORE_MODULES

_remove_html_overhead = re.compile(
    r'(?sm)^<html.*<body.*?>\n(.*)</body>\n</html>\n')

space_re = re.compile('\n^( *)\S', re.M)

_marker = object()

BASEDIR = dirname(dirname(dirname(dirname(zope.app.__file__))))

def relativizePath(path):
    return path.replace(BASEDIR, 'Zope3')


def truncateSysPath(path):
    """Remove the system path prefix from the path."""
    for syspath in sys.path:
        if path.startswith(syspath):
            return path.replace(syspath, '')[1:]
    return path


class ReadContainerBase(object):
    """Base for `IReadContainer` objects."""
    implements(IReadContainer)

    def get(self, key, default=None):
        raise NotImplemented

    def items(self):
        raise NotImplemented

    def __getitem__(self, key):
        default = object()
        obj = self.get(key, default)
        if obj is default:
            raise KeyError(key)
        return obj

    def __contains__(self, key):
        return self.get(key) is not None

    def keys(self):
        return map(lambda x: x[0], self.items())

    def __iter__(self):
        return self.values().__iter__()

    def values(self):
        return map(lambda x: x[1], self.items())

    def __len__(self):
        return len(self.items())


def getPythonPath(obj):
    """Return the path of the object in standard Python notation.

    This method should try very hard to return a string, even if it is not a
    valid Python path.
    """
    if obj is None:
        return None

    # Even for methods `im_class` and `__module__` is not allowed to be
    # accessed (which is probably not a bad idea). So, we remove the security
    # proxies for this check.
    naked = removeSecurityProxy(obj)
    if hasattr(naked, "im_class"):
        naked = naked.im_class
    module = getattr(naked, '__module__', _marker)
    if module is _marker:
        return naked.__name__
    return '%s.%s' %(module, naked.__name__)


def isReferencable(path):
    """Return whether the Python path is referencable."""
    # Sometimes no path exists, so make a simple check first; example: None
    if path is None:
        return False

    # There are certain paths that we do not want to reference, most often
    # because they are outside the scope of this documentation
    for exclude_name in IGNORE_MODULES:
        if path.startswith(exclude_name):
            return False
    split_path = path.rsplit('.', 1)
    if len(split_path) == 2:
        module_name, obj_name = split_path
    else:
        module_name, obj_name = split_path[0], None

    # Do not allow private attributes to be accessible
    if (obj_name is not None and
        obj_name.startswith('_') and
        not (obj_name.startswith('__') and obj_name.endswith('__'))):
        return False
    module = safe_import(module_name)
    if module is None:
        return False

    # If the module imported correctly and no name is provided, then we are
    # all good.
    if obj_name is None:
        return True

    obj = getattr(module, obj_name, _marker)
    if obj is _marker:
        return False
    # Detect singeltons; those are not referencable in apidoc (yet)
    if hasattr(obj, '__class__') and getPythonPath(obj.__class__) == path:
        return False
    return True


def _evalId(id):
    if isinstance(id, Global):
        id = id.__name__
        if id == 'CheckerPublic':
            id = 'zope.Public'
    return id


def getPermissionIds(name, checker=_marker, klass=_marker):
    """Get the permissions of an attribute."""
    assert (klass is _marker) != (checker is _marker)
    entry = {}

    if klass is not _marker:
        checker = getCheckerForInstancesOf(klass)

    if checker is not None and INameBasedChecker.providedBy(checker):
        entry['read_perm'] = _evalId(checker.permission_id(name)) \
                             or _('n/a')
        entry['write_perm'] = _evalId(checker.setattr_permission_id(name)) \
                              or _('n/a')
    else:
        entry['read_perm'] = entry['write_perm'] = None

    return entry


def getFunctionSignature(func):
    """Return the signature of a function or method."""
    if not isinstance(func, (types.FunctionType, types.MethodType)):
        raise TypeError("func must be a function or method")

    args, varargs, varkw, defaults = inspect.getargspec(func)
    placeholder = object()
    sig = '('
    # By filling up the default tuple, we now have equal indeces for args and
    # default.
    if defaults is not None:
        defaults = (placeholder,)*(len(args)-len(defaults)) + defaults
    else:
        defaults = (placeholder,)*len(args)

    str_args = []

    for name, default in zip(args, defaults):
        # Neglect self, since it is always there and not part of the signature.
        # This way the implementation and interface signatures should match.
        if name == 'self' and type(func) == types.MethodType:
            continue

        # Make sure the name is a string
        if isinstance(name, (tuple, list)):
            name = '(' + ', '.join(name) + ')'
        elif not isinstance(name, str):
            name = repr(name)

        if default is placeholder:
            str_args.append(name)
        else:
            str_args.append(name + '=' + repr(default))

    if varargs:
        str_args.append('*'+varargs)
    if varkw:
        str_args.append('**'+varkw)

    sig += ', '.join(str_args)
    return sig + ')'


def getPublicAttributes(obj):
    """Return a list of public attribute names."""
    attrs = []
    for attr in dir(obj):
        if attr.startswith('_'):
            continue
        
        try:
            getattr(obj, attr)
        except AttributeError:
            continue

        attrs.append(attr)

    return attrs

def getInterfaceForAttribute(name, interfaces=_marker, klass=_marker,
                             asPath=True):
    """Determine the interface in which an attribute is defined."""
    if (interfaces is _marker) and (klass is _marker):
        raise ValueError("need to specify interfaces or klass")
    if (interfaces is not _marker) and (klass is not _marker):
        raise ValueError("must specify only one of interfaces and klass")

    if interfaces is _marker:
        direct_interfaces = list(implementedBy(klass))
        interfaces = {}
        for interface in direct_interfaces:
            interfaces[interface] = 1
            for base in interface.getBases():
                interfaces[base] = 1
        interfaces = interfaces.keys()

    for interface in interfaces:
        if name in interface.names():
            if asPath:
                return getPythonPath(interface)
            return interface

    return None


def columnize(entries, columns=3):
    """Place a list of entries into columns."""
    if len(entries)%columns == 0:
        per_col = len(entries)/columns
        last_full_col = columns
    else:
        per_col = len(entries)/columns + 1
        last_full_col = len(entries)%columns
    columns = []
    col = []
    in_col = 0
    for entry in entries:
        if in_col < per_col - int(len(columns)+1 > last_full_col):
            col.append(entry)
            in_col += 1
        else:
            columns.append(col)
            col = [entry]
            in_col = 1
    if col:
        columns.append(col)
    return columns


_format_dict = {
    'plaintext': 'zope.source.plaintext',
    'structuredtext': 'zope.source.stx',
    'restructuredtext': 'zope.source.rest'
    }

def getDocFormat(module):
    """Convert a module's __docformat__ specification to a renderer source
    id"""
    format = getattr(module, '__docformat__', 'structuredtext').lower()
    # The format can also contain the language, so just get the first part
    format = format.split(' ')[0]
    return _format_dict.get(format, 'zope.source.stx')


def dedentString(text):
    """Dedent the docstring, so that docutils can correctly render it."""
    dedent = min([len(match) for match in space_re.findall(text)] or [0])
    return re.compile('\n {%i}' % dedent, re.M).sub('\n', text)


def renderText(text, module=None, format=None, dedent=True):
    if not text:
        return u''

    if module is not None:
        if isinstance(module, (str, unicode)):
            module = sys.modules.get(module, None)
        format = getDocFormat(module)

    if format is None:
        format = 'zope.source.stx'

    assert format in _format_dict.values()

    text = dedentString(text)

    source = createObject(format, text)
    renderer = getMultiAdapter((source, TestRequest()))
    return renderer.render()

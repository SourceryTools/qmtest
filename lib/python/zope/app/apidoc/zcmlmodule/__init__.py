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
"""ZCML Documentation module

The ZCML documentation module reads all of the meta directives (but does not
execute them) and uses the collected data to generate the tree. The result of
the evaluation is stored in thread-global variables, so that we have to parse
the files only once.

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.configuration import docutils, xmlconfig
from zope.interface import implements
from zope.location.interfaces import ILocation

import zope.app.appsetup.appsetup
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase

# Caching variables, so that the meta-ZCML files need to be read only once
namespaces = None
subdirs = None

def quoteNS(ns):
    """Quotes a namespace to make it URL-secure."""
    ns = ns.replace(':', '_co_')
    ns = ns.replace('/', '_sl_')
    return ns

def unquoteNS(ns):
    """Un-quotes a namespace from a URL-secure version."""
    ns = ns.replace('_sl_', '/')
    ns = ns.replace('_co_', ':')
    return ns


class Namespace(ReadContainerBase):
    """Simple namespace object for the ZCML Documentation Module."""

    implements(ILocation)

    def __init__(self, parent, name):
        self.__parent__ = parent
        self.__realname__ = name
        self.__name__ = self.getQuotedName()

    def getShortName(self):
        """Get the short name of the namespace."""
        name = self.__realname__
        if name.startswith('http://namespaces.zope.org/'):
            name = name[27:]
        return name

    def getFullName(self):
        """Get the full name of the namespace."""
        return self.__realname__

    def getQuotedName(self):
        """Get the full name, but quoted for a URL."""
        name = self.getFullName()
        name = quoteNS(name)
        return name

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer"""
        ns = self.getFullName()
        if not namespaces[ns].has_key(key):
            return default
        schema, handler, info = namespaces[ns][key]
        sd = subdirs.get((ns, key), [])
        directive = Directive(self, key, schema, handler, info, sd)
        return directive

    def items(self):
        """See zope.app.container.interfaces.IReadContainer"""
        list = []
        for key in namespaces[self.getFullName()].keys():
            list.append((key, self.get(key)))
        list.sort()
        return list


class Directive(object):
    """Represents a ZCML Directive."""

    implements(ILocation)

    def __init__(self, ns, name, schema, handler, info, subdirs):
        self.__parent__ = ns
        self.__name__ = name
        self.schema = schema
        self.handler = handler
        self.info = info
        self.subdirs = subdirs


class ZCMLModule(ReadContainerBase):
    r"""Represent the Documentation of all ZCML namespaces.

    This documentation is implemented using a simple `IReadContainer`. The
    items of the container."""

    implements(IDocumentationModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('ZCML Reference')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    This module presents you with a complete list of ZCML directives and
    serves therefore well as reference. The menu provides you with a tree that
    organizes the directives by namespaces.

    The documentation contents for each directive tells you all the available
    attributes and their semantics. It also provides a link to the interface
    the directive confirms to. If available, it will even tell you the
    file the directive was declared in. At the end a list of available
    subdirectives is given, also listing the implemented interface and
    available attributes.
    """)

    def _makeDocStructure(self):
        # Some trivial caching
        global namespaces
        global subdirs
        context = zope.app.appsetup.appsetup.getConfigContext()
        namespaces, subdirs = docutils.makeDocStructures(context)

        # Empty keys are not so good for a container
        if namespaces.has_key(''):
            namespaces['ALL'] = namespaces['']
            del namespaces['']


    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer

        Get the namespace by name; long and abbreviated names work.
        """
        if namespaces is None or subdirs is None:
            self._makeDocStructure()

        key = unquoteNS(key)
        if namespaces.has_key(key):
            return Namespace(self, key)

        full_key = 'http://namespaces.zope.org/' + key
        if namespaces.has_key(full_key):
            return Namespace(self, full_key)

        return default


    def items(self):
        """See zope.app.container.interfaces.IReadContainer"""
        if namespaces is None or subdirs is None:
            self._makeDocStructure()
        list = []
        for key in namespaces.keys():
            namespace = Namespace(self, key)
            # We need to make sure that we use the quoted URL as key
            list.append((namespace.getQuotedName(), namespace))
        list.sort()
        return list


def _clear():
    global namespaces
    global subdirs
    namespaces = None
    subdirs = None

from zope.testing.cleanup import addCleanUp
addCleanUp(_clear)

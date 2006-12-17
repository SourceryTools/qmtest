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
"""Introspector

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.interface import implements, implementedBy
from zope.interface import directlyProvides, directlyProvidedBy, providedBy
from zope.interface.interfaces import IInterface
from zope.interface.interface import InterfaceClass
from zope.security.proxy import removeSecurityProxy
from zope.component.interface import searchInterface, getInterface

from zope.app.introspector.interfaces import IIntrospector

##############################################################################
# from zope.app.module import resolve

# Break the dependency on zope.app.module.  In the long run,
# we need to handle this better.  Perhaps througha utility.

## def findModule(name, context=None):
##     """Find the module matching the provided name."""
##     module = ZopeModuleRegistry.findModule(name)
##     return module or sys.modules.get(name)

import sys

def resolve(name, context=None):
    """Resolve a dotted name to a Python object."""
    pos = name.rfind('.')
    mod = sys.modules.get(name[:pos])
##    mod = findModule(name[:pos], context)
    return getattr(mod, name[pos+1:], None)

# from zope.app.module import resolve
##############################################################################


class Introspector(object):
    """Introspects an object"""

    implements(IIntrospector)

    def __init__(self, context):
        self.context = context
        self.request = None
        self.currentclass = None

    def isInterface(self):
        "Checks if the context is class or interface"
        return IInterface.providedBy(self.context)

    def setRequest(self, request):
        """sets the request"""
        self.request = request
        if 'PATH_INFO' in request:
            path = self.request['PATH_INFO']
        else:
            path = ''
        name = path[path.rfind('++module++') + len('++module++'):]
        name = name.split('/')[0]
        if path.find('++module++') != -1:
            if (self.context == Interface and
                name != 'Interface._Interface.Interface'):
                self.currentclass = resolve(name)
                self.context = self.currentclass
            else:
                self.currentclass = self.context
        else:
            self.currentclass = self.context.__class__

    def _unpackTuple(self, tuple_obj):
        res = []
        for item in tuple_obj:
            if type(item)==tuple:
                res.extend(self._unpackTuple(item))
            else:
                res.append(item)
        return tuple(res)

    def getClass(self):
        """Returns the class name"""
        return self.currentclass.__name__

    def getBaseClassNames(self):
        """Returns the names of the classes"""
        bases = self.getExtends()
        base_names = []
        for base in bases:
            base_names.append(base.__module__+'.'+base.__name__)
            return base_names

    def getModule(self):
        """Returns the module name of the class"""
        return self.currentclass.__module__

    def getDocString(self):
        """Returns the description of the class"""
        return removeSecurityProxy(self.currentclass).__doc__

    def getInterfaces(self):
        """Returns interfaces implemented by this class"""
        return tuple(implementedBy(self.currentclass))

    def getInterfaceNames(self, interfaces=None):
        if interfaces is None:
            interfaces = self.getInterfaces()
        names = []
        for intObj in interfaces:
            names.append(interfaceToName(self.context, intObj))
        names.sort()
        return names

    def getInterfaceDetails(self):
        """Returns the entire documentation in the interface"""
        interface = self.context
        Iname = interfaceToName(self.context, interface).split('.')[-1]
        bases = []
        desc = ''
        methods = []
        attributes = []
        if interface is not None:
            namesAndDescriptions = list(interface.namesAndDescriptions())
            namesAndDescriptions.sort()
            for name, desc in namesAndDescriptions:
                if hasattr(desc, 'getSignatureString'):
                    methods.append((desc.__name__,
                                    desc.getSignatureString(),
                                    desc.getDoc()))
                else:
                    attributes.append((desc.getName(), desc.getDoc()))

            for base in interface.__bases__:
                bases.append(base.__module__+'.'+base.__name__)
            desc = str(interface.getDoc())
        return [Iname, bases, desc, methods, attributes]

    def getExtends(self):
        """Returns all the class extended up to the top most level"""
        bases = self._unpackTuple(
            removeSecurityProxy(self.currentclass).__bases__)
        return bases

    def getDirectlyProvided(self):
        """See `IIntrospector`"""
        return directlyProvidedBy(removeSecurityProxy(self.context))

    def getDirectlyProvidedNames(self):
        """See `IIntrospector`"""
        return self.getInterfaceNames(self.getDirectlyProvided())

    def getMarkerInterfaceNames(self):
        """See `IIntrospector`"""
        result = list(self.getInterfaceNames(self.getMarkerInterfaces()))
        result.sort()
        return tuple(result)

    def getMarkerInterfaces(self):
        """See `IIntrospector`"""

        results = []
        todo = list(providedBy(self.context))
        done = []
        while todo:
            interface = todo.pop()
            done.append(interface)
            for base in interface.__bases__:
                if base not in todo and base not in done:
                    todo.append(base)
            markers = self.getDirectMarkersOf(interface)
            for interface in markers:
                if (interface not in results
                    and not interface.providedBy(self.context)):
                    results.append(interface)
            todo += markers
        results.sort()
        return tuple(results)

    def getDirectMarkersOf(self, base):
        """Returns empty interfaces directly inheriting from the given one"""

        results = []
        interfaces = searchInterface(self.context, base=base)
        for interface in interfaces:
            # There are things registered with the site manager
            # that are not interfaces. Duh!
            if not IInterface.providedBy(interface):
                continue
            if base in interface.__bases__ and not interface.names():
                results.append(interface)

        results.sort()
        return tuple(results)
    

# TODO: This method should go away and only registered interface utilities
# should be used.
def interfaceToName(context, interface):
    if interface is None:
        return 'None'
    items = searchInterface(context, base=interface)
    ids = [('%s.%s' %(iface.__module__, iface.__name__))
           for iface in items
           if iface == interface]
    
    if not ids:
        # Do not fail badly, instead resort to the standard
        # way of getting the interface name, cause not all interfaces
        # may be registered as utilities.
        return interface.__module__ + '.' + interface.__name__

    assert len(ids) == 1, "Ambiguous interface names: %s" % ids
    return ids[0]

# BBB: Deprecated module; Will be gone in 3.3.
from zope.deprecation import deprecated
deprecated('Introspector',
           'Use the public apidoc utilities. Will be gone in 3.3.')

deprecated('interfaceToName',
           'Use zope.app.component.interface.interfaceToName instead. '
           'Will be gone in 3.3.')

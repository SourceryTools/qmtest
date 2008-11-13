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
"""XML-RPC Introspection mechanism

$Id: xmlrpcintrospection.py 74090 2007-04-10 14:25:10Z dobe $
"""
__docformat__ = 'restructuredtext'

import types
import inspect

from zope.interface import providedBy
from zope.publisher.interfaces.xmlrpc import IXMLRPCRequest
from zope.component import getGlobalSiteManager

def getViews(ifaces):
    """Get all view registrations for methods"""
    gsm = getGlobalSiteManager()
    for reg in gsm.registeredAdapters():
        if (len(reg.required) > 0 and
            reg.required[-1] is not None and
            reg.required[-1].isOrExtends(IXMLRPCRequest)):
            for required_iface in reg.required[:-1]:
                if required_iface is not None:
                    for iface in ifaces:
                        if iface.isOrExtends(required_iface):
                            yield reg

def xmlrpccallable(return_type, *parameters_types):
    def wrapper(func):
        # adding info on the function object
        func.return_type = return_type
        func.parameters_types = parameters_types
        return func
    return wrapper

class XMLRPCIntrospection(object):

    def listMethods(self):
        """ lists all methods available """
        return self._getXMLRPCMethods()

    def methodSignature(self, method_name):
        """ returns the method signature """
        return self._getXMLRPCMethodSignature(method_name)

    def methodHelp(self, method_name):
        """ returns the docstring of the method """
        return self._getXMLRPCMethodHelp(method_name)

    def __call__(self, *args, **kw):
        return self.listMethods()

    #
    # Introspection APIS
    #
    _reserved_method_names = (u'', u'listMethods', u'methodHelp',
                              u'methodSignature')

    def _filterXMLRPCRequestRegistrations(self, registrations):
        # TODO might be outsourced to some utility
        for registration in registrations:
            for required_iface in registration.required:
                if (required_iface is IXMLRPCRequest and
                    registration.name.strip() not in
                    self._reserved_method_names):
                    yield registration

    def _getRegistrationAdapters(self, interfaces):
        # TODO might be outsourced to some utility
        registrations = list(getViews(interfaces))
        filtered_adapters = list(
            self._filterXMLRPCRequestRegistrations(registrations))
        return filtered_adapters

    def _getFunctionArgumentSize(self, func):
        args, varargs, varkw, defaults = inspect.getargspec(func)
        num_params = len(args) - 1
        if varargs is not None:
            num_params += len(varargs)
        if varkw is not None:
            num_params += len(varkw)

        return num_params

    def _getFunctionSignature(self, func):
        """Return the signature of a function or method."""
        if not isinstance(func, (types.FunctionType, types.MethodType)):
            raise TypeError("func must be a function or method")

        # see if the function has been decorated
        if hasattr(func, 'return_type') and hasattr(func, 'parameters_types'):
            signature = [func.return_type] + list(func.parameters_types)
            # we want to return the type name as string
            # to avoid marshall problems
            str_signature = []
            for element in signature:
                if element is None or not hasattr(element, '__name__'):
                    str_signature.append('undef')
                else:
                    str_signature.append(element.__name__)
            return [str_signature]

        # no decorator, let's just return Nones
        # TODO if defaults are given, render their type
        return [['undef'] * (self._getFunctionArgumentSize(func) + 1)]

    def _getFunctionHelp(self, func):
        if hasattr(func, '__doc__') and func.__doc__ is not None:
            if func.__doc__.strip() != '':
                return func.__doc__
        return 'undef'

    #
    # Lookup APIS
    #
    def _getXMLRPCMethods(self):
        adapter_registrations = []
        interfaces = list(providedBy(self.context))

        for result in self._getRegistrationAdapters(interfaces):
            if result.name not in adapter_registrations:
                adapter_registrations.append(result.name)

        adapter_registrations.sort()
        return adapter_registrations

    def _getXMLRPCMethodSignature(self, method_name):
        """ The signature of a method is an array of
            signatures (if the method returns multiple signatures)
            and each array contains the return type then the parameters
            types:

                [[return type, param1 type, param2 type, ...], [...], ...]
        """
        interfaces = list(providedBy(self.context))

        for result in self._getRegistrationAdapters(interfaces):
            if result.name == method_name:
                method = getattr(result.factory, method_name)
                return self._getFunctionSignature(method)

        return 'undef'

    def _getXMLRPCMethodHelp(self, method_name):
        """ The help of a method is just the doctstring, if given
        """
        interfaces = list(providedBy(self.context))

        for result in self._getRegistrationAdapters(interfaces):
            if result.name == method_name:
                method = getattr(result.factory, method_name)
                return self._getFunctionHelp(method)

        return 'undef'

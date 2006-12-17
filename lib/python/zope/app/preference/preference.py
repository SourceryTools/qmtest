##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""User Preferences System

$Id: preference.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = "reStructuredText"
from BTrees.OOBTree import OOBTree

import zope.interface
from zope.schema import getFields
from zope.security.checker import CheckerPublic, Checker, defineChecker
from zope.security.management import getInteraction
from zope.traversing.interfaces import IContainmentRoot
from zope.location import LocationProxy, locate, Location

import zope.app.component.hooks
from zope.app import zapi
from zope.app.container.contained import Contained
from zope.app.container.interfaces import IReadContainer
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility

from zope.app.preference.interfaces import IPreferenceGroup 
from zope.app.preference.interfaces import IPreferenceCategory 
from zope.app.preference.interfaces import IDefaultPreferenceProvider 

pref_key = 'zope.app.user.UserPreferences'


class PreferenceGroup(Location):
    """A feature-rich ``IPreferenceGroup`` implementation.

    This class implements the 
    """
    zope.interface.implements(IPreferenceGroup, IReadContainer)

    # Declare attributes here, so that they are always available.
    __id__ = ''
    __schema__ = None
    __title__ = None
    __description__ = None

    def __init__(self, id, schema=None, title=u'', description=u'',
                 isCategory=False):
        self.__id__ = id
        self.__schema__ = schema
        self.__title__ = title
        self.__description__ = description

        # The last part of the id is the name.
        self.__name__ = id.split('.')[-1]

        # Make sure this group provides all important interfaces.
        directlyProvided = ()
        if isCategory:
            directlyProvided += (IPreferenceCategory,)
        if schema:
            directlyProvided += (schema,)
        zope.interface.directlyProvides(self, directlyProvided)

    # Store the actual parent in ``__parent``. Usually we would just override
    # the property to an actual value during binding, but because we overrode
    # ``__setattr__`` this is not possible anymore. 
    __parent = None
    def __parent__(self):
        return self.__parent or zope.app.component.hooks.getSite()
    __parent__ = property(__parent__)


    def __bind__(self, parent):
        clone = self.__class__.__new__(self.__class__)
        clone.__dict__.update(self.__dict__)
        clone.__parent = parent
        return clone


    def get(self, key, default=None):
        id = self.__id__ and self.__id__ + '.' + key or key
        group = zapi.queryUtility(IPreferenceGroup, id, default)
        if group is default:
            return default
        return group.__bind__(self)
    

    def items(self):
        cutoff = self.__id__ and len(self.__id__)+1 or 0
        return [(id[cutoff:], group.__bind__(self))
                for id, group in zapi.getUtilitiesFor(IPreferenceGroup)
                if id != self.__id__ and \
                   id.startswith(self.__id__) and \
                   id[cutoff:].find('.') == -1]

    def __getitem__(self, key):
        """See zope.app.container.interfaces.IReadContainer"""
        default = object()
        obj = self.get(key, default)
        if obj is default:
            raise KeyError(key)
        return obj

    def __contains__(self, key):
        """See zope.app.container.interfaces.IReadContainer"""
        return self.get(key) is not None

    def keys(self):
        """See zope.app.container.interfaces.IReadContainer"""
        return [id for id, group in self.items()]

    def __iter__(self):
        """See zope.app.container.interfaces.IReadContainer"""
        return self.values().__iter__()
        
    def values(self):
        """See zope.app.container.interfaces.IReadContainer"""
        return [group for id, group in self.items()]

    def __len__(self):
        """See zope.app.container.interfaces.IReadContainer"""
        return len(self.items())    

    def __getattr__(self, key):
        # Try to find a sub-group of the given id
        group = self.get(key)
        if group is not None:
            return group

        # Try to find a preference of the given name
        if self.__schema__ and key in self.__schema__:
            marker = object()
            value = self.data.get(key, marker)
            if value is marker:
                # Try to find a default preference provider
                provider = zapi.queryUtility(IDefaultPreferenceProvider,
                                             context=self)
                if provider is None:
                    return self.__schema__[key].default
                defaultGroup = provider.getDefaultPreferenceGroup(self.__id__)
                return getattr(defaultGroup, key)
            return value

        # Nothing found, raise an attribute error
        raise AttributeError("'%s' is not a preference or sub-group." % key)

    def __setattr__(self, key, value):
        if self.__schema__ and key in self.__schema__:
            # Validate the value
            bound = self.__schema__[key].bind(self)
            bound.validate(value)
            # Assign value
            self.data[key] = value
        else:
            self.__dict__[key] = value
            # If the schema changed, we really need to change the security
            # checker as well.
            if key is '__schema__':
                checker = PreferenceGroupChecker(self)
                self.__dict__['__Security_checker__'] = checker

    def __delattr__(self, key):
        if self.__schema__ and key in self.__schema__:
            del self.data[key]
        else:
            del self.__dict__[key]

    def data(self):
        utility = zapi.getUtility(IPrincipalAnnotationUtility, context=self)
        # TODO: what if we have multiple participations?
        principal = getInteraction().participations[0].principal
        ann = utility.getAnnotations(principal)

        # If no preferences exist, create the root preferences object.
        if  ann.get(pref_key) is None:
            ann[pref_key] = OOBTree()
        prefs = ann[pref_key]

        # If no entry for the group exists, create a new entry.
        if self.__id__ not in prefs.keys():
            prefs[self.__id__] = OOBTree()

        return prefs[self.__id__]
    data = property(data)


def PreferenceGroupChecker(instance):
    """A function that generates a custom security checker.

    The attributes available in a preference group are dynamically generated
    based on the group schema and the available sub-groups. Thus, the
    permission dictionaries have to be generated at runtime and are unique for
    each preference group instance.
    """
    read_perm_dict = {}
    write_perm_dict = {}

    # Make sure that the attributes from IPreferenceGroup and IReadContainer
    # are public.
    for attrName in ('__id__', '__schema__', '__title__', '__description__',
                     'get', 'items', 'keys', 'values',
                     '__getitem__', '__contains__', '__iter__', '__len__'):
        read_perm_dict[attrName] = CheckerPublic

    # Make the attributes generated from the schema available as well.
    if instance.__schema__ is not None:
        for name in getFields(instance.__schema__):
            read_perm_dict[name] = CheckerPublic
            write_perm_dict[name] = CheckerPublic

    # Make all sub-groups available as well.
    for name in instance.keys():
        read_perm_dict[name] = CheckerPublic
        write_perm_dict[name] = CheckerPublic

    return Checker(read_perm_dict, write_perm_dict)


def UserPreferences(context=None):
    """Adapts an ``ILocation`` object to the ``IUserPreferences`` interface."""
    if context is None:
        context = zapi.getSiteManager()
    rootGroup = zapi.getUtility(IPreferenceGroup)
    rootGroup = rootGroup.__bind__(context)
    rootGroup.__name__ = '++preferences++'
    zope.interface.alsoProvides(rootGroup, IContainmentRoot)
    return rootGroup

class preferencesNamespace(object):
    """Used to traverse to the root preferences group."""

    def __init__(self, ob, request=None):
        self.context = ob
        
    def traverse(self, name, ignore):
        rootGroup = zapi.getUtility(IPreferenceGroup)
        rootGroup = rootGroup.__bind__(self.context)
        rootGroup.__name__ = '++preferences++'
        zope.interface.alsoProvides(rootGroup, IContainmentRoot)
        return name and rootGroup[name] or rootGroup

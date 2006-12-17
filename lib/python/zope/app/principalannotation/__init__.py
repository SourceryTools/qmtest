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
"""Implementation of `IPrincipalAnnotationUtility`.

$Id: __init__.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

# TODO: register utility as adapter for IAnnotations on utility activation.

from persistent import Persistent
from persistent.dict import PersistentDict
from BTrees.OOBTree import OOBTree
import zope.security.interfaces
from zope import interface, component
from zope.location import Location
from zope.annotation.interfaces import IAnnotations

from zope.app.container.contained import Contained
from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
from zope.app.component import queryNextUtility

class PrincipalAnnotationUtility(Persistent, Contained):
    """Stores `IAnnotations` for `IPrinicipals`.

    The utility ID is 'PrincipalAnnotation'.
    """

    interface.implements(IPrincipalAnnotationUtility)

    def __init__(self):
        self.annotations = OOBTree()

    def getAnnotations(self, principal):
        """Return object implementing IAnnotations for the given principal.

        If there is no `IAnnotations` it will be created and then returned.
        """
        return self.getAnnotationsById(principal.id)

    def getAnnotationsById(self, principalId):
        """Return object implementing `IAnnotations` for the given principal.

        If there is no `IAnnotations` it will be created and then returned.
        """

        annotations = self.annotations.get(principalId)
        if annotations is None:
            annotations = Annotations(principalId, store=self.annotations)
            annotations.__parent__ = self
            annotations.__name__ = principalId

        return annotations

    def hasAnnotations(self, principal):
        """Return boolean indicating if given principal has `IAnnotations`."""
        return principal.id in self.annotations


class Annotations(Persistent, Location):
    """Stores annotations."""

    interface.implements(IAnnotations)

    def __init__(self, principalId, store=None):
        self.principalId = principalId
        self.data = PersistentDict() # We don't really expect that many

        # _v_store is used to remember a mapping object that we should
        # be saved in if we ever change
        self._v_store = store

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            # We failed locally: delegate to a higher-level utility.
            utility = queryNextUtility(self, IPrincipalAnnotationUtility)
            if utility is not None:
                annotations = utility.getAnnotationsById(self.principalId)
                return annotations[key]
            raise

    def __setitem__(self, key, value):
        if getattr(self, '_v_store', None) is not None:
            # _v_store is used to remember a mapping object that we should
            # be saved in if we ever change
            self._v_store[self.principalId] = self
            del self._v_store

        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

def annotations(principal):
    """adapt principal to annotations via principal annotation utility.
    
    To illustrate, we'll register the adapter and a dummy 
    principal annotation utility.
    
    >>> component.provideAdapter(annotations)
    >>> class DummyPrincipal(object):
    ...     interface.implements(zope.security.interfaces.IPrincipal)
    ...     def __init__(self, id, title=None, description=None):
    ...         self.id = id
    ...         self.title = title
    ...         self.description = description
    ...
    >>> dummy_annotation = {}
    >>> class DummyPAU(object):
    ...     interface.implements(interfaces.IPrincipalAnnotationUtility)
    ...     def getAnnotations(self, principal):
    ...         if principal.id == 'sue':
    ...             return dummy_annotation
    ...         raise NotImplementedError
    ...
    >>> pau = DummyPAU()
    >>> component.provideUtility(pau)
    >>> sue = DummyPrincipal('sue')
    >>> annotation = IAnnotations(sue)
    >>> annotation is dummy_annotation
    True
    """ # TODO move this out to a doctest file when we have one...
    utility = component.getUtility(IPrincipalAnnotationUtility)
    return utility.getAnnotations(principal)
component.adapter(zope.security.interfaces.IPrincipal)(annotations)
interface.implementer(IAnnotations)(annotations)

#############################################################################
# BBB: 12/20/2004
PrincipalAnnotationService = PrincipalAnnotationUtility
#############################################################################

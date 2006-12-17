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
"""Code about interfaces.

This module contains code for interfaces in persistent modules.

$Id: __init__.py 39759 2005-10-31 05:03:42Z srichter $
"""
__docformat__ = 'restructuredtext'

from persistent import Persistent
from persistent.dict import PersistentDict
from zodbcode.patch import registerWrapper, Wrapper

from zope.interface.interface import InterfaceClass
from zope.interface import Interface
from zope.security.proxy import removeSecurityProxy

class PersistentInterfaceClass(Persistent, InterfaceClass):

    def __init__(self, *args, **kw):
        Persistent.__init__(self)
        InterfaceClass.__init__(self, *args, **kw)

        self.dependents = PersistentDict()

# PersistentInterface is equivalent to the zope.interface.Interface object
# except that it is also persistent.  It is used in conjunction with
# zodb.code to support interfaces in persistent modules.
PersistentInterface = PersistentInterfaceClass("PersistentInterface",
                                               (Interface, ))

class PersistentInterfaceWrapper(Wrapper):

    def unwrap(self):
        return PersistentInterfaceClass(self._obj.__name__)


def getInterfaceStateForPersistentInterfaceCreation(iface):
    # Need to convert the dependents weakref dict to a persistent dict
    dict = iface.__dict__.copy()
    dependents = PersistentDict()
    for k, v in dict['dependents'].iteritems():
        dependents[k] = v
    dict['dependents'] = dependents
    return dict

registerWrapper(InterfaceClass, PersistentInterfaceWrapper,
                lambda iface: (),
                getInterfaceStateForPersistentInterfaceCreation,
                )

from zope.interface.declarations import providedBy

def queryType(object, interface):
    """Returns the object's interface which implements interface.

    >>> from zope.app.content.interfaces import IContentType
    >>> from zope.interface import Interface, implements, directlyProvides
    >>> class I(Interface):
    ...     pass
    >>> class J(Interface):
    ...     pass
    >>> directlyProvides(I, IContentType)
    >>> class C(object):
    ...     implements(I)
    >>> class D(object):
    ...     implements(J,I)
    >>> obj = C()
    >>> c1_ctype = queryType(obj, IContentType)
    >>> c1_ctype.__name__
    'I'
    >>> class I1(I):
    ...     pass
    >>> class I2(I1):
    ...     pass
    >>> class I3(Interface):
    ...     pass
    >>> class C1(object):
    ...     implements(I1)
    >>> obj1 = C1()
    >>> c1_ctype = queryType(obj1, IContentType)
    >>> c1_ctype.__name__
    'I'
    >>> class C2(object):
    ...     implements(I2)
    >>> obj2 = C2()
    >>> c2_ctype = queryType(obj2, IContentType)
    >>> c2_ctype.__name__
    'I'

    >>> class C3(object):
    ...     implements(I3)
    >>> obj3 = C3()

    If Interface doesn't provide `IContentType`, `queryType` returns ``None``.

    >>> c3_ctype = queryType(obj3, IContentType)
    >>> c3_ctype
    >>> c3_ctype is None
    True
    >>> class I4(I):
    ...     pass
    >>> directlyProvides(I4, IContentType)
    >>> class C4(object):
    ...     implements(I4)
    >>> obj4 = C4()
    >>> c4_ctype = queryType(obj4, IContentType)
    >>> c4_ctype.__name__
    'I4'

    """
    # Remove the security proxy, so that we can introspect the type of the
    # object's interfaces.
    naked = removeSecurityProxy(object)
    object_iro = providedBy(naked).__iro__
    for iface in object_iro:
        if interface.providedBy(iface):
            return iface

    return None

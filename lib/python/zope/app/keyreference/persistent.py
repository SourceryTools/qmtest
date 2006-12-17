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
"""Unique id utility.

This utility assigns unique integer ids to objects and allows lookups
by object and by id.

This functionality can be used in cataloging.

$Id: persistent.py 69785 2006-08-26 18:04:06Z philikon $
"""
from ZODB.interfaces import IConnection
import zope.interface

import zope.app.keyreference.interfaces

class KeyReferenceToPersistent(object):
    """An IReference for persistent object which is comparable.

    These references compare by _p_oids of the objects they reference.
    """
    zope.interface.implements(zope.app.keyreference.interfaces.IKeyReference)

    key_type_id = 'zope.app.keyreference.persistent'

    def __init__(self, object):
        if not getattr(object, '_p_oid', None):
            connection = IConnection(object, None)
            if connection is None:
                raise zope.app.keyreference.interfaces.NotYet(object)

            connection.add(object)

        self.object = object

    def __call__(self):
        return self.object

    def __hash__(self):
        return hash((self.object._p_jar.db().database_name,
                     self.object._p_oid,
                     ))

    def __cmp__(self, other):
        if self.key_type_id == other.key_type_id:
            return cmp(
                (self.object._p_jar.db().database_name,  self.object._p_oid),
                (other.object._p_jar.db().database_name, other.object._p_oid),
                )

        return cmp(self.key_type_id, other.key_type_id)


@zope.interface.implementer(IConnection)
def connectionOfPersistent(ob):
    """An adapter which gets a ZODB connection of a persistent object.

    We are assuming the object has a parent if it has been created in
    this transaction.

    Raises ValueError if it is impossible to get a connection.
    """
    cur = ob
    while not getattr(cur, '_p_jar', None):
        cur = getattr(cur, '__parent__', None)
        if cur is None:
            return None
    return cur._p_jar

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
"""Testing components

$Id: testing.py 67937 2006-05-03 22:01:49Z srichter $
"""
import zope.interface
import zope.component
import zope.app.keyreference.interfaces

class SimpleKeyReference(object):
    """An IReference for all objects. This implementation is *not* ZODB safe.
    """
    zope.component.adapts(zope.interface.Interface)
    zope.interface.implements(zope.app.keyreference.interfaces.IKeyReference)

    key_type_id = 'zope.app.keyreference.simple'

    def __init__(self, object):
        self.object = object

    def __call__(self):
        return self.object

    def __hash__(self):
        return hash(self.object)

    def __cmp__(self, other):
        if self.key_type_id == other.key_type_id:
            return cmp(hash(self.object), hash(other))

        return cmp(self.key_type_id, other.key_type_id)

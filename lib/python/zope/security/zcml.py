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
"""Security related configuration fields.

$Id: zcml.py 70539 2006-10-05 08:45:29Z flox $
"""
__docformat__ = 'restructuredtext'

import zope.schema
from zope.interface import Interface, implements
from zope.schema.interfaces import IFromUnicode
from zope.security.permission import checkPermission
from zope.security.management import setSecurityPolicy
from zope.configuration.fields import MessageID, GlobalObject

class Permission(zope.schema.Id):
    r"""This field describes a permission.

    Let's look at an example:

    >>> class FauxContext(object):
    ...     permission_mapping = {'zope.ManageCode':'zope.private'}
    ...     _actions = []
    ...     def action(self, **kws):
    ...        self._actions.append(kws)
    >>> context = FauxContext()
    >>> field = Permission().bind(context)

    Let's test the fromUnicode method:

    >>> field.fromUnicode(u'zope.foo')
    'zope.foo'
    >>> field.fromUnicode(u'zope.ManageCode')
    'zope.private'

    Now let's see whether validation works alright

    >>> field._validate('zope.ManageCode')
    >>> context._actions[0]['args']
    (None, 'zope.foo')
    >>> field._validate('3 foo')
    Traceback (most recent call last):
    ...
    InvalidId: 3 foo

    zope.Public is always valid
    >>> field._validate('zope.Public')
    """
    implements(IFromUnicode)

    def fromUnicode(self, u):
        u = super(Permission, self).fromUnicode(u)

        map = getattr(self.context, 'permission_mapping', {})
        return map.get(u, u)

    def _validate(self, value):
        super(Permission, self)._validate(value)

        if value != 'zope.Public':
            self.context.action(
                discriminator = None,
                callable = checkPermission,
                args = (None, value),

                # Delay execution till end. This is an
                # optimization. We don't want to intersperse utility
                # lookup, done when checking permissions, with utility
                # definitions. Utility lookup is expensive after
                # utility definition, as extensive caches have to be
                # rebuilt.
                order=9999999,
                )


class ISecurityPolicyDirective(Interface):
    """Defines the security policy that will be used for Zope."""

    component = GlobalObject(
        title=u"Component",
        description=u"Pointer to the object that will handle the security.",
        required=True)

def securityPolicy(_context, component):
    _context.action(
            discriminator = 'defaultPolicy',
            callable = setSecurityPolicy,
            args = (component,) )

class IPermissionDirective(Interface):
    """Define a new security object."""

    id = zope.schema.Id(
        title=u"Id",
        description=u"Id as which this object will be known and used.",
        required=True)

    title = MessageID(
        title=u"Title",
        description=u"Provides a title for the object.",
        required=True)

    description = MessageID(
        title=u"Description",
        description=u"Provides a description for the object.",
        required=False)

def permission(_context, id, title, description=''):
    from zope.security.interfaces import IPermission
    from zope.security.permission import Permission
    from zope.component.zcml import utility
    permission = Permission(id, title, description)
    utility(_context, IPermission, permission, name=id)

class IRedefinePermission(Interface):
    """Define a permission to replace another permission."""

    from_ = Permission(
        title=u"Original permission",
        description=u"Original permission id to redefine.",
        required=True)

    to = Permission(
        title=u"Substituted permission",
        description=u"Substituted permission id.",
        required=True)

def redefinePermission(_context, from_, to):
    _context = _context.context

    # check if context has any permission mappings yet
    if not hasattr(_context, 'permission_mapping'):
        _context.permission_mapping={}

    _context.permission_mapping[from_] = to

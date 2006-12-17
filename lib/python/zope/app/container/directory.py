##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""File-system representation adapters for containers

This module includes two adapters (adapter factories, really) for
providing a file-system representation for containers:

`noop`
  Factory that "adapts" `IContainer` to `IWriteDirectory`.
  This is a lie, since it just returns the original object.

`Cloner`
  An `IDirectoryFactory` adapter that just clones the original object.

$Id: directory.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.filerepresentation.interfaces
from zope.security.proxy import removeSecurityProxy
from zope.interface import implements

def noop(container):
    """Adapt an `IContainer` to an `IWriteDirectory` by just returning it

    This "works" because `IContainer` and `IWriteDirectory` have the same
    methods, however, the output doesn't actually implement `IWriteDirectory`.
    """
    return container


class Cloner(object):
    """`IContainer` to `IDirectoryFactory` adapter that clones

    This adapter provides a factory that creates a new empty container
    of the same class as it's context.
    """

    implements(zope.filerepresentation.interfaces.IDirectoryFactory)

    def __init__(self, context):
        self.context = context

    def __call__(self, name):
        
        # We remove the security proxy so we can actually call the
        # class and return an unproxied new object.  (We can't use a
        # trusted adapter, because the result must be unproxied.)  By
        # registering this adapter, one effectively gives permission
        # to clone the class.  Don't use this for classes that have
        # exciting side effects as a result of instantiation. :)

        return removeSecurityProxy(self.context).__class__()

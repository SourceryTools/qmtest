##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

"""Subscriber function checking dependencies if a removal is performed
on an object having dependencies. It raises an exception if it's the
case.

$Id: dependency.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.app import zapi
from zope.i18nmessageid import Message
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.dependable.interfaces import IDependable, DependencyError

exception_msg = _("""
Removal of object (${object}) which has dependents (${dependents})
is not possible !

You must deactivate this object before trying to remove it.
""")

def CheckDependency(event):
    object = event.object
    dependency = IDependable(object, None)
    if dependency is not None:
        dependents = dependency.dependents()
        if dependents:
            mapping = {
                "object": zapi.getPath(object),
                "dependents": ", ".join(dependents)
                }
            raise DependencyError(Message(exception_msg, mapping=mapping))

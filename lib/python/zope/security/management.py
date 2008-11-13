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
"""Default 'ISecurityManagement' and 'IInteractionManagement' implementation

$Id: management.py 78815 2007-08-14 17:52:16Z jim $
"""


import zope.interface
import zope.thread

import zope.security.interfaces

from zope.security.checker import CheckerPublic
from zope.security._definitions import thread_local, system_user
from zope.security.simplepolicies import ParanoidSecurityPolicy

_defaultPolicy = ParanoidSecurityPolicy

zope.interface.moduleProvides(
    zope.security.interfaces.ISecurityManagement,
    zope.security.interfaces.IInteractionManagement)

def _clear():
    global _defaultPolicy
    _defaultPolicy = ParanoidSecurityPolicy

# XXX This code is used to support automated testing. However, it shouldn't be
# here and needs to be refactored. The empty addCleanUp-method is a temporary
# workaround to fix packages that depend on zope.security but don't have a
# need for zope.testing.
try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    def addCleanUp(arg):
        pass

addCleanUp(_clear)

#
#   ISecurityManagement implementation
#

def getSecurityPolicy():
    """Get the system default security policy."""
    return _defaultPolicy

def setSecurityPolicy(aSecurityPolicy):
    """Set the system default security policy, and return the previous
    value.

    This method should only be called by system startup code.
    It should never, for example, be called during a web request.
    """
    global _defaultPolicy

    last, _defaultPolicy = _defaultPolicy, aSecurityPolicy

    return last


#
#   IInteractionManagement implementation
#

def queryInteraction():
    return getattr(thread_local, 'interaction', None)

def getInteraction():
    """Get the current interaction."""
    try:
        return thread_local.interaction
    except AttributeError:
        raise zope.security.interfaces.NoInteraction

def newInteraction(*participations):
    """Start a new interaction."""

    if queryInteraction() is not None:
        raise AssertionError("newInteraction called"
                             " while another interaction is active.")

    interaction = getSecurityPolicy()(*participations)

    thread_local.interaction = interaction

def endInteraction():
    """End the current interaction."""

    try:
        thread_local.previous_interaction = thread_local.interaction
    except AttributeError:
        # if someone does a restore later, it should be restored to not having
        # an interaction.  If there was a previous interaction from a previous
        # call to endInteraction, it should be removed.
        try:
            del thread_local.previous_interaction
        except AttributeError:
            pass
    else:
        del thread_local.interaction

def restoreInteraction():
    try:
        previous = thread_local.previous_interaction
    except AttributeError:
        try:
            del thread_local.interaction
        except AttributeError:
            pass
    else:
        thread_local.interaction = previous

def checkPermission(permission, object, interaction=None):
    """Return whether security policy allows permission on object.

    Arguments:
    permission -- A permission name
    object -- The object being accessed according to the permission
    interaction -- An interaction, which provides access to information
        such as authenticated principals.  If it is None, the current
        interaction is used.

    checkPermission is guaranteed to return True if permission is
    CheckerPublic or None.
    """
    if permission is CheckerPublic or permission is None:
        return True
    if interaction is None:
        interaction = thread_local.interaction
    return interaction.checkPermission(permission, object)

addCleanUp(endInteraction)

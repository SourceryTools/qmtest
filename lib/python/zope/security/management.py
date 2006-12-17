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

$Id: management.py 40098 2005-11-14 19:14:00Z poster $
"""
# Special system user that has all permissions
# zope.security.simplepolicies needs it
system_user = object()

import traceback

from zope.interface import moduleProvides
from zope.security.interfaces import ISecurityManagement
from zope.security.interfaces import IInteractionManagement
from zope.security.interfaces import NoInteraction
from zope.testing.cleanup import addCleanUp
import zope.thread

thread_local = zope.thread.local()

moduleProvides(ISecurityManagement, IInteractionManagement)


def _clear():
    global _defaultPolicy
    _defaultPolicy = ParanoidSecurityPolicy

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
        raise NoInteraction

def newInteraction(*participations):
    """Start a new interaction."""
    
    
    if queryInteraction() is not None:
        stack = queryInteraction()._newInteraction_called_from
        raise AssertionError("newInteraction called"
                             " while another interaction is active:\n%s"
                             % "".join(traceback.format_list(stack)))

    interaction = getSecurityPolicy()(*participations)

    interaction._newInteraction_called_from = traceback.extract_stack()
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


# circular imports are not fun

from zope.security.checker import CheckerPublic
from zope.security.simplepolicies import ParanoidSecurityPolicy
_defaultPolicy = ParanoidSecurityPolicy

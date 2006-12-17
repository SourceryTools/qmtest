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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Register protection information for some standard low-level types

$Id: _protections.py 67630 2006-04-27 00:54:03Z jim $
"""

def protect():
    # Add message id types to the basic types, so their setting cannot be
    # overridden, once set. `protect()` was not guranteed to run after
    # zope.security.checker._clear, so that sometimes the proxies were not set.
    # This is not the ideal solution, but it is effective.

    # Make sure the message id gets never proxied.  This is not a
    # security hole because Messages are immutable.
    import zope.security.checker
    from zope.security.checker import NoProxy
    from zope.i18nmessageid import Message
    zope.security.checker.BasicTypes[Message] = NoProxy

    # add __parent__ and __name__ to always available names
    for name in ['__name__', '__parent__']:
        if name not in zope.security.checker._available_by_default:
            zope.security.checker._available_by_default.append(name)

##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''API module to set the security policy


$Id: SecurityManager.py 40218 2005-11-18 14:39:19Z andreasjung $'''

from AccessControl import ImplPython as _ImplPython
from AccessControl.SimpleObjectPolicies import _noroles


def setSecurityPolicy(aSecurityPolicy):
    """Set the system default security policy.

    This method should only be caused by system startup code. It should
    never, for example, be called during a web request.
    """
    last = _ImplPython._defaultPolicy
    _ImplPython._defaultPolicy = aSecurityPolicy
    return last


# AccessControl.Implementation inserts SecurityManager.

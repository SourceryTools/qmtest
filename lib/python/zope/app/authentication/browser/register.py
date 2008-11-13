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
"""Improved registration UI for registering pluggable authentication utilities

$Id: register.py 73548 2007-03-25 09:05:22Z dobe $
"""

from zope.app.authentication.i18n import ZopeMessageFactory as _
import zope.app.component.browser.registration
import zope.app.security.interfaces

class AddAuthenticationRegistration(
    zope.app.component.browser.registration.AddUtilityRegistration,
    ):
    label = _("Register a pluggable authentication utility")
    name = ''
    provided = zope.app.security.interfaces.IAuthentication

##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Features that will be deprecated in Zope 3.5

$Id: back35.py 73631 2007-03-26 14:43:17Z dobe $
"""

from zope.traversing.api import traverse
from zope.component.service import IService
from zope.app.component.site import UtilityRegistration
from zope.app.component.back35 import ActiveStatus

def addService(servicemanager, name, service, suffix=''):
    """Add a service to a service manager

    This utility is useful for tests that need to set up services.
    """
    default = traverse(servicemanager, 'default')
    default[name+suffix] = service
    registration = UtilityRegistration(name, IService, service, default)
    key = default.registrationManager.addRegistration(registration)
    traverse(default.registrationManager, key).status = ActiveStatus
    return default[name+suffix]

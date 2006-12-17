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
"""Application Control

$Id: applicationcontrol.py 67630 2006-04-27 00:54:03Z jim $"""
__docformat__ = 'restructuredtext'

import time
import zope.interface
import zope.traversing.interfaces
from zope.location import Location
from zope.security.checker import ProxyFactory, NamesChecker
from zope.app.applicationcontrol.interfaces import IApplicationControl

class ApplicationControl(Location):

    zope.interface.implements(IApplicationControl)

    def __init__(self):
        self.start_time = time.time()

    def getStartTime(self):
        return self.start_time


applicationControllerRoot = Location()
zope.interface.directlyProvides(
    applicationControllerRoot,
    zope.traversing.interfaces.IContainmentRoot,
    )
applicationControllerRoot = ProxyFactory(applicationControllerRoot,
                                         NamesChecker("__class__"))

applicationController = ApplicationControl()
applicationController.__parent__ = applicationControllerRoot
applicationController.__name__ = '++etc++process'

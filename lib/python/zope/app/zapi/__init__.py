##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Collection of many common api functions

Makes imports easier

$Id: __init__.py 67819 2006-05-02 09:01:18Z philikon $
"""
from zope.interface import moduleProvides
from zope.app.zapi.interfaces import IZAPI
moduleProvides(IZAPI)
__all__ = tuple(IZAPI)

from zope.component import *
from zope.security.proxy import isinstance
from zope.traversing.api import *
from zope.traversing.browser.absoluteurl import absoluteURL
from zope.exceptions.interfaces import UserError
from zope.app.publisher.browser import getDefaultViewName
from zope.app.publisher.browser import queryDefaultViewName
from zope.app.interface import queryType

name = getName

def principals():
    from zope.app.security.interfaces import IAuthentication
    return getUtility(IAuthentication)

# BBB 2006/04/27 -- to be removed after 12 months
import zope.deferredimport
zope.deferredimport.deprecated(
    "This object was deprecated long ago.  Only import is allowed now "
    "and will be disallows in Zope 3.5.",
    getGlobalServices = "zope.component.back35:deprecated",
    getGlobalService = "zope.component.back35:deprecated",
    getService = "zope.component.back35:deprecated",
    getServiceDefinitions = "zope.component.back35:deprecated",
    getView = "zope.component.back35:deprecated",
    queryView = "zope.component.back35:deprecated",
    getMultiView = "zope.component.back35:deprecated",
    queryMultiView = "zope.component.back35:deprecated",
    getViewProviding = "zope.component.back35:deprecated",
    queryViewProviding = "zope.component.back35:deprecated",
    getResource = "zope.component.back35:deprecated",
    queryResource = "zope.component.back35:deprecated",
    )

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
"""An adapter from IPrincipal to the ILoggingInfo.

$Id: principallogging.py 26551 2004-07-15 07:06:37Z srichter $
"""
from zope.interface import implements
from zope.publisher.interfaces.logginginfo import ILoggingInfo

class PrincipalLogging(object):

    implements(ILoggingInfo)

    def __init__(self, principal):
        self.principal = principal

    def getLogMessage(self):
        return str(self.principal.id)

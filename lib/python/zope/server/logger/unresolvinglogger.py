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
"""Unresolving Logger

$Id: unresolvinglogger.py 26559 2004-07-15 21:22:32Z srichter $
"""
from zope.server.interfaces.logger import IRequestLogger
from zope.interface import implements

class UnresolvingLogger(object):
    """Just in case you don't want to resolve"""

    implements(IRequestLogger)

    def __init__(self, logger):
        self.logger = logger

    def logRequest(self, ip, message):
        'See IRequestLogger'
        self.logger.logMessage('%s%s' % (ip, message))

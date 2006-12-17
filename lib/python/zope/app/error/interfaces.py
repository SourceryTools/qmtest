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
"""Error Reporting Utility interfaces

$Id: interfaces.py 28629 2004-12-15 23:52:41Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface

class IErrorReportingUtility(Interface):
    """Error Reporting Utility"""

    def raising(info, request=None):
        """Logs an exception."""


class ILocalErrorReportingUtility(Interface):
    """Local Error Reporting Utility

    This interface contains additional management functions.
    """

    def getProperties():
        """Gets the properties as dictionary.

        keep_entries, copy_to_logfile, ignored_exceptions
        """

    def setProperties(keep_entries, copy_to_zlog=0, ignored_exceptions=(),
                      RESPONSE=None):
        """Sets the properties

        keep_entries, copy_to_logfile, ignored_exceptions
        """

    def getLogEntries():
        """Returns the entries in the log, most recent first."""

    def getLogEntryById(id):
        """Return LogEntry by ID"""

###############################################################################
# BBB: 12/14/2004

IErrorReportingService = IErrorReportingUtility
ILocalErrorReportingService = ILocalErrorReportingUtility

###############################################################################

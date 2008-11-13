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
"""Error Reporting Utility

This is a port of the Zope 2 error reporting object

$Id: error.py 79914 2007-09-24 21:29:57Z rogerineichen $
"""
__docformat__ = 'restructuredtext'

import zope.deferredimport
import zope.deprecation
zope.deprecation.moved(
    'zope.error.error',
    "Zope 3.6",
    )
zope.deferredimport.deprecated(
    "It has moved to zope.error.error  This reference will be gone "
    "in Zope 3.6",
    printedreplace = 'zope.error.error:printedreplace',
    )
zope.deferredimport.deprecated(
    "It has moved to zope.error.error  This reference will be gone "
    "in Zope 3.6",
    getFormattedException = 'zope.error.error:getFormattedException',
    )
zope.deferredimport.deprecated(
    "It has moved to zope.error.error  This reference will be gone "
    "in Zope 3.6",
    ErrorReportingUtility = 'zope.error.error:ErrorReportingUtility',
    )
zope.deferredimport.deprecated(
    "It has moved to zope.error.error.  This reference will be gone "
    "in Zope 3.6",
    RootErrorReportingUtility = 'zope.error.error:RootErrorReportingUtility',
    )
zope.deferredimport.deprecated(
    "It has moved to zope.error.error  This reference will be gone "
    "in Zope 3.6",
    globalErrorReportingUtility = 'zope.error.error:globalErrorReportingUtility',
    )

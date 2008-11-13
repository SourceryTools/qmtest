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

$Id: interfaces.py 79914 2007-09-24 21:29:57Z rogerineichen $
"""
__docformat__ = 'restructuredtext'
import zope.deferredimport
import zope.deprecation
zope.deprecation.moved(
    'zope.error.error',
    "Zope 3.6",
    )

zope.deferredimport.deprecated(
    "IErrorReportingUtility has moved to zope.error.interfaces",
    IErrorReportingUtility = 'zope.error.interfaces:IErrorReportingUtility',
    )

zope.deferredimport.deprecated(
    "ILocalErrorReportingUtility has moved to zope.error.interfaces",
    ILocalErrorReportingUtility = 'zope.error.interfaces:ILocalErrorReportingUtility',
    )

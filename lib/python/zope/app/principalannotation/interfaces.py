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
"""Utility for storing `IAnnotations` for principals.

$Id: interfaces.py 70213 2006-09-17 15:31:01Z flox $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface


class IPrincipalAnnotationUtility(Interface):
    """Stores `IAnnotations` for `IPrinicipals`."""

    def getAnnotations(principal):
        """Return object implementing `IAnnotations` for the given
        `IPrinicipal`.

        If there is no `IAnnotations` it will be created and then returned.
        """

    def getAnnotationsById(principalId):
        """Return object implementing `IAnnotations` for the given
        `prinicipalId`.

        If there is no `IAnnotations` it will be created and then returned.
        """

    def hasAnnotations(principal):
        """Return boolean indicating if given `IPrincipal` has
        `IAnnotations`."""

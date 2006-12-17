##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Interface Documentation Module Interfaces

$Id: interfaces.py 39064 2005-10-11 18:40:10Z philikon $
"""

__docformat__ = "reStructuredText"

import zope.interface
import zope.schema

from zope.app.i18n import ZopeMessageFactory as _


class IInterfaceDetailsPreferences(zope.interface.Interface):
    __doc__ = _("""
    Preferences for API Docs' Interface Details Screen

    It is possible to hide and show various sections of the interface details'
    screen. The following preferences allow you to choose the sections to be
    shown by default.
    """)

    showSpecificRequiredAdapters = zope.schema.Bool(
        title=_("Specific Required Interface Adapters"),
        description=_("Show specific required interface adapters"),
        required=False,
        default=True)

    showExtendedRequiredAdapters = zope.schema.Bool(
        title=_("Extended Required Interface Adapters"),
        description=_("Show extended required interface adapters"),
        required=False,
        default=True)

    showGenericRequiredAdapters = zope.schema.Bool(
        title=_("Generic Required Interface Adapters"),
        description=_("Show generic required interface adapters"),
        required=False,
        default=False)

    showBrowserViews = zope.schema.Bool(
        title=_("Browser Views"),
        description=_("Show browser views"),
        required=False,
        default=True)

    showSpecificBrowserViews = zope.schema.Bool(
        title=_("Specific Browser Views"),
        description=_("Show specific browser views"),
        required=False,
        default=True)

    showExtendedBrowserViews = zope.schema.Bool(
        title=_("Extended Browser Views"),
        description=_("Show extended browser views"),
        required=False,
        default=False)

    showGenericBrowserViews = zope.schema.Bool(
        title=_("Generic Browser Views"),
        description=_("Show generic browser views"),
        required=False,
        default=False)

    showXMLRPCViews = zope.schema.Bool(
        title=_("XML-RPC Views"),
        description=_("Show XML-RPC views"),
        required=False,
        default=False)

    showSpecificXMLRPCViews = zope.schema.Bool(
        title=_("Specific XML-RPC Views"),
        description=_("Show specific XML-RPC views"),
        required=False,
        default=True)

    showExtendedXMLRPCViews = zope.schema.Bool(
        title=_("Extended XML-RPC Views"),
        description=_("Show extended XML-RPC views"),
        required=False,
        default=False)

    showGenericXMLRPCViews = zope.schema.Bool(
        title=_("Generic XML-RPC Views"),
        description=_("Show generic XML-RPC views"),
        required=False,
        default=False)

    showHTTPViews = zope.schema.Bool(
        title=_("Generic HTTP Views"),
        description=_("Show generic HTTP views"),
        required=False,
        default=False)

    showSpecificHTTPViews = zope.schema.Bool(
        title=_("Specific HTTP Views"),
        description=_("Show specific HTTP views"),
        required=False,
        default=True)

    showExtendedHTTPViews = zope.schema.Bool(
        title=_("Extended HTTP Views"),
        description=_("Show extended HTTP views"),
        required=False,
        default=False)

    showGenericHTTPViews = zope.schema.Bool(
        title=_("Generic HTTP Views"),
        description=_("Show generic HTTP views"),
        required=False,
        default=False)

    showFTPViews = zope.schema.Bool(
        title=_("FTP Views"),
        description=_("Show FTP views"),
        required=False,
        default=False)

    showSpecificFTPViews = zope.schema.Bool(
        title=_("Specific FTP Views"),
        description=_("Show specific FTP views"),
        required=False,
        default=True)

    showExtendedFTPViews = zope.schema.Bool(
        title=_("Extended FTP Views"),
        description=_("Show extended FTP views"),
        required=False,
        default=False)

    showGenericFTPViews = zope.schema.Bool(
        title=_("Generic FTP Views"),
        description=_("Show generic FTP views"),
        required=False,
        default=False)

    showOtherViews = zope.schema.Bool(
        title=_("Other Views"),
        description=_("Show other (unidentified) views"),
        required=False,
        default=False)

    showSpecificOtherViews = zope.schema.Bool(
        title=_("Specific Other Views"),
        description=_("Show specific other views"),
        required=False,
        default=True)

    showExtendedOtherViews = zope.schema.Bool(
        title=_("Extended Other Views"),
        description=_("Show extended other views"),
        required=False,
        default=False)

    showGenericOtherViews = zope.schema.Bool(
        title=_("Generic Other Views"),
        description=_("Show generic other views"),
        required=False,
        default=False)

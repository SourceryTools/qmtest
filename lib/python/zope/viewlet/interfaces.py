##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Viewlet interfaces

$Id: interfaces.py 74236 2007-04-18 09:27:22Z dobe $
"""
__docformat__ = 'restructuredtext'

import zope.interface
from zope.contentprovider.interfaces import IContentProvider
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

class IViewlet(IContentProvider):
    """A content provider that is managed by another content provider, known
    as viewlet manager.

    Note that you *cannot* call viewlets directly as a provider, i.e. through
    the TALES ``provider`` expression, since it always has to know its manager.
    """

    manager = zope.interface.Attribute(
        """The Viewlet Manager

        The viewlet manager for which the viewlet is registered. The viewlet
        manager will contain any additional data that was provided by the
        view, for example the TAL namespace attributes.
        """)


class IViewletManager(IContentProvider,
                      zope.interface.common.mapping.IReadMapping):
    """A component that provides access to the content providers.

    The viewlet manager's resposibilities are:

      (1) Aggregation of all viewlets registered for the manager.

      (2) Apply a set of filters to determine the availability of the
          viewlets.

      (3) Sort the viewlets based on some implemented policy.

      (4) Provide an environment in which the viewlets are rendered.

      (5) Render itself containing the HTML content of the viewlets.
    """

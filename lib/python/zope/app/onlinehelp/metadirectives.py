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
"""Schemas for the ``help`` ZCML namespace

$Id: metadirectives.py 41587 2006-02-10 09:10:18Z hdima $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.schema import BytesLine, TextLine
from zope.configuration.fields import GlobalInterface, GlobalObject
from zope.configuration.fields import Path, MessageID, Tokens


class IOnlineHelpTopicDirective(Interface):
    """Register an online topic.

    Optionally you can register a topic for a component and view.
    """

    id = BytesLine(
        title=u"Topic Id",
        description=u"Id of the topic as it will appear in the URL.",
        required=True)

    title = MessageID(
        title=u"Title",
        description=u"Provides a title for the online Help Topic.",
        required=True)

    parent = BytesLine(
        title=u"Parent Topic",
        description=u"Id of the parent topic.",
        default="",
        required=False)

    for_ = GlobalInterface(
        title=u"Object Interface",
        description=u"Interface for which this Help Topic is registered.",
        default=None,
        required=False)

    view = BytesLine(
        title=u"View Name",
        description=u"The view name for which this Help Topic is registered.",
        default="",
        required=False)

    doc_path = Path(
        title=u"Path to File",
        description=u"Path to the file that contains the Help Topic content.",
        required=True)

    class_ = GlobalObject(
        title=u"Factory",
        description=u"""
        The factory is the topic class used for initializeing the topic""",
        required=False,
        )

    resources = Tokens(
        title=u"A list of resources.",
        description=u"""
        A list of resources which shall be used for the Help Topic.
        The resources must be located in the same directory as
        the Help Topic definition.
        """,
        value_type=TextLine(),
        required=False
        )

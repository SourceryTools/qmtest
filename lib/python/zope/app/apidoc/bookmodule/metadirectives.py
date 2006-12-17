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
"""Schema for the ``apidoc:bookchapter`` directive

$Id: metadirectives.py 28450 2004-11-13 21:05:19Z shane $
"""
__docformat__ = 'restructuredtext'

from zope.configuration.fields import Path, MessageID, Tokens
from zope.interface import Interface
from zope.schema import BytesLine, TextLine

class IBookChapterDirective(Interface):
    """Register a new Book Chapter"""

    id = BytesLine(
        title=u"Topic Id",
        description=u"Id of the chapter as it will appear in the URL.",
        required=True)

    title = MessageID(
        title=u"Title",
        description=u"Provides a title for the chapter.",
        required=True)

    doc_path = Path(
        title=u"Path to File",
        description=u"Path to the file that contains the chapter content.",
        required=False)

    parent = BytesLine(
        title=u"Parent Chapter",
        description=u"Id of the parent chapter.",
        default="",
        required=False)

    resources = Tokens(
        title=u"A list of resources.",
        description=u"""
        A list of resources which shall be user for the chapter. The
        resources must be located in the same directory as the chapter.
        """,
        value_type=TextLine(),
        required=False
        )

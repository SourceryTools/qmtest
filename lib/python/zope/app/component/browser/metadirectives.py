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
"""`tool` directive for `browser` namespace

$Id: metadirectives.py 69358 2006-08-05 17:54:32Z flox $
"""
import zope.configuration.fields
from zope.interface import Interface

    
class IUtilityToolDirective(Interface):
    """ *BBB: DEPRECATED*

    Tools are deprecated and no-longer used.
    The tool directive will go away in Zope 3.5.

    (Directive for creating new utility-based tools.)
    """

    folder = zope.configuration.fields.PythonIdentifier(
        title=u"Destination Folder",
        description=u"""Destination Folder in which the tool instances are
                        placed.""",
        required=False,
        default=u"tools")
    
    title = zope.configuration.fields.MessageID(
        title=u"Title",
        description=u"""The title of the tool.""",
        required=False
        )

    description = zope.configuration.fields.MessageID(
        title=u"Description",
        description=u"Narrative description of what the tool represents.",
        required=False
        )

    interface = zope.configuration.fields.GlobalInterface(
        title=u"Interface",
        description=u"Interface used to filter out the available entries in a \
                      tool",
        required=True)

    unique = zope.configuration.fields.Bool(
        title=u"Unique",
        description=u"Specifies whether the tool is unique to a site manager.",
        required=False,
        default=False)

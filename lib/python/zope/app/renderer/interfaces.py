##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Renderer Interface Declarations

The source renderer takes a special type of string, an ISource, and is able to
produce 

$Id: interfaces.py 25177 2004-06-02 13:17:31Z jim $
"""
from zope.interface import Interface

class ISource(Interface):
    """Simple base interface for all possible Wiki Page Source types."""

class ISourceRenderer(Interface):
    """Object implementing this interface are responsible for rendering an
    ISource objects to an output format.

    This is the base class for all possible output types."""

    def __init__(self, source):
        """Initialize the renderer.

        The source argument is the source code that needs to be converted.
        """

    def render():
        """Renders the source into another format."""

class IHTMLRenderer(ISourceRenderer):
    """Renders an ISource object to HTML."""

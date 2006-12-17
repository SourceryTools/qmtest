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
"""Function Views

$Id: browser.py 29143 2005-02-14 22:43:16Z srichter $
"""
__docformat__ = 'restructuredtext'
from zope.app.apidoc.utilities import renderText

class TextFileDetails(object):
    """Represents the details of the text file."""

    def renderedContent(self):
        """Render the file content to HTML."""
        if self.context.path.endswith('.stx'):
            format = 'zope.source.stx'
        else:
            format = 'zope.source.rest'
        return renderText(self.context.getContent(), format=format)

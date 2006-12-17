##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: zptpage.py 28610 2004-12-09 20:56:05Z jim $
"""

from zope.interface import implements
from zope.app.zptpage.interfaces import IZPTPage
from zope.index.text.interfaces import ISearchableText
import re

tag = re.compile(r"<[^>]+>")

class SearchableText:

    __used_for__ = IZPTPage
    implements(ISearchableText)

    def __init__(self, page):
        self.page = page

    def getSearchableText(self):
        text = self.page.getSource()
        if isinstance(text, str):
            text = unicode(self.page.source, 'utf-8')
        # else:
        #   text was already Unicode, which happens, but unclear how it
        #   gets converted to Unicode since the ZPTPage stores UTF-8 as
        #   an 8-bit string.

        if self.page.content_type.startswith('text/html'):
            text = tag.sub('', text)

        return [text]

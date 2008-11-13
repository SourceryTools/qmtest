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
"""URL quoting for ZPT

$Id: urlquote.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import urllib
from zope.interface import implements
from zope.traversing.interfaces import IPathAdapter

class URLQuote(object):
    r"""An adapter for URL quoting.

    It quotes unicode strings according to the recommendation in RFC 2718.
    Before the unicode string gets quoted, it gets encoded with UTF-8.

        >>> quoter = URLQuote(u'Roki\u0161kis')
        >>> quoter.quote()
        'Roki%C5%A1kis'
        
        >>> quoter.quote_plus()
        'Roki%C5%A1kis'

    And when unquoting, it assumes the unquoted string is encoded with
    UTF-8, and tries to convert it to unicode.

        >>> quoter = URLQuote('Roki%C5%A1kis')
        >>> quoter.unquote()
        u'Roki\u0161kis'
        
        >>> quoter.unquote_plus()
        u'Roki\u0161kis'

    If the unquoted string can't be converted to unicode, the unquoted
    string is returned.

        >>> quoter = URLQuote('S%F6derk%F6ping')
        >>> quoter.unquote()
        'S\xf6derk\xf6ping'

        >>> quoter.unquote_plus()
        'S\xf6derk\xf6ping'
    """

    __used_for__ = basestring
    implements(IPathAdapter)

    def __init__(self, context):
        if not isinstance(context, basestring):
            context = str(context)
        elif isinstance(context, unicode):
            context = context.encode('utf-8')
        self.context = context

    def quote(self):
        """Return the object's URL quote representation."""
        return urllib.quote(self.context)

    def quote_plus(self):
        """Return the object's URL quote_plus representation."""
        return urllib.quote_plus(self.context)

    def unquote(self):
        """Return the object's URL unquote representation."""
        unquoted = urllib.unquote(self.context)
        try:
            return unicode(unquoted, 'utf-8')
        except UnicodeDecodeError:
            return unquoted

    def unquote_plus(self):
        """Return the object's URL unquote_plus representation."""
        unquoted = urllib.unquote_plus(self.context)
        try:
            return unicode(unquoted, 'utf-8')
        except UnicodeDecodeError:
            return unquoted


##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Error related things.

$Id: errors.py 70826 2006-10-20 03:41:16Z baijum $
"""
__docformat__ = 'restructuredtext'

from cgi import escape

from zope.component import adapts
from zope.interface import implements
from zope.interface import Invalid
from zope.i18n import Message
from zope.i18n import translate

from zope.app.form.browser.interfaces import IWidgetInputErrorView
from zope.publisher.interfaces.browser import IBrowserRequest


class InvalidErrorView(object):

    """Display a validation error as a snippet of text."""

    implements(IWidgetInputErrorView)
    adapts(Invalid, IBrowserRequest)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def snippet(self):
        """Convert a widget input error to an html snippet

        >>> from zope.interface.exceptions import Invalid
        >>> error = Invalid("You made an error!")
        >>> InvalidErrorView(error, None).snippet()
        u'<span class="error">You made an error!</span>'
        """
        msg = self.context.args[0]
        if isinstance(msg, Message):
            msg = translate(msg, context=self.request)
        return u'<span class="error">%s</span>' % escape(msg)

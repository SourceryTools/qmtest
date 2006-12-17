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
"""Form-related exception views

$Id: exception.py 29459 2005-03-14 10:45:38Z hdima $
"""
__docformat__ = 'restructuredtext'

from cgi import escape

from zope.interface import implements
from zope.i18n import translate

from zope.app.form.interfaces import IWidgetInputError
from zope.app.form.browser.interfaces import IWidgetInputErrorView

class WidgetInputErrorView(object):
    """Display an input error as a snippet of text."""
    implements(IWidgetInputErrorView)

    __used_for__ = IWidgetInputError

    def __init__(self, context, request):
        self.context, self.request = context, request

    def snippet(self):
        """Convert a widget input error to an html snippet

        >>> from zope.app.form.interfaces import WidgetInputError
        >>> class TooSmallError(object):
        ...     def doc(self):
        ...         return "Foo input < 1"
        >>> err = WidgetInputError("foo", "Foo", TooSmallError())
        >>> view = WidgetInputErrorView(err, None)
        >>> view.snippet()
        u'<span class="error">Foo input &lt; 1</span>'

        The only method that IWidgetInputError promises to implement is
        `doc()`. Therefore, other implementations of the interface should also
        work.

        >>> from zope.app.form.interfaces import ConversionError
        >>> err = ConversionError('Could not convert to float.')
        >>> view = WidgetInputErrorView(err, None)
        >>> view.snippet()
        u'<span class="error">Could not convert to float.</span>'
        """
        message = self.context.doc()
        translated = translate(message, context=self.request, default=message)
        return u'<span class="error">%s</span>' % escape(translated)

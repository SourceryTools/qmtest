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
"""Generic Text Widgets tests

$Id: test_widgetdocs.py 27082 2004-08-12 20:03:58Z srichter $
"""
import unittest
from zope.interface.verify import verifyClass
from zope.interface.exceptions import DoesNotImplement
from zope.publisher.browser import TestRequest
from zope.schema import TextLine
from zope.testing.doctestunit import DocTestSuite

from zope.app.form.browser.widget import DisplayWidget, UnicodeDisplayWidget


def test_implemented_interfaces():
    """Make sure that the display widget implements the correct interfaces.

    Like all browser-used widgets, DisplayWidget must implement
    `IBrowserWidget`.

    >>> from zope.app.form.browser.interfaces import IBrowserWidget
    >>> verifyClass(IBrowserWidget, DisplayWidget)
    True

    But unlike most other widgets in this package, the display widget is *not*
    an `IInputWidget`.

    >>> from zope.app.form.interfaces import IInputWidget
    >>> try:
    ...     verifyClass(IInputWidget, DisplayWidget)    
    ... except DoesNotImplement:
    ...     'not implemented'
    'not implemented'
    """

def test_not_required():
    """Make sure that display widgets are not required

    >>> field = TextLine(title = u'Title',
    ...                  __name__ = u'title',
    ...                  default = u'<My Title>')
    >>> widget = DisplayWidget(field, TestRequest())
    >>> widget.required
    False
    
    """

def test_value_escaping():
    """Make sure that the returned values are correctly escaped.

    First we need to create a field that is the context of the display widget.
    >>> field = TextLine(title = u'Title',
    ...                  __name__ = u'title',
    ...                  default = u'<My Title>')

    >>> field = field.bind(None)

    Now we are ready to instantiate our widget.

    >>> widget = DisplayWidget(field, TestRequest())

    If no data was specified in the widget, the field's default value will be
    chosen.

    >>> widget()
    u'&lt;My Title&gt;'

    Now let's set a value and make sure that, when output, it is also
    correctly escaped.

    >>> widget.setRenderedValue(u'<Another Title>')
    >>> widget()
    u'&lt;Another Title&gt;'

    When the value is the missing_value, the empty string should be
    displayed::

    >>> field = TextLine(title = u'Title',
    ...                  __name__ = u'title',
    ...                  required = False)

    >>> field = field.bind(None)
    >>> widget = DisplayWidget(field, TestRequest())
    >>> widget.setRenderedValue(field.missing_value)

    >>> widget()
    ''

    If there's no default for the field and the value is missing on
    the bound object, the empty string should still be displayed::

    >>> field = TextLine(title=u'Title',
    ...                  __name__=u'title',
    ...                  required=False)

    >>> class Thing:
    ...    title = field.missing_value

    >>> field = field.bind(Thing())
    >>> widget = DisplayWidget(field, TestRequest())

    >>> widget()
    ''

    """


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite())
    suite.addTest(DocTestSuite(
        extraglobs={"DisplayWidget": UnicodeDisplayWidget}))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

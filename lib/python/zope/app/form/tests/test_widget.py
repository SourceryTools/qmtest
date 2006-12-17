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
"""Generic Widget Tests

$Id: test_widget.py 68730 2006-06-18 05:35:59Z ctheune $
"""
from unittest import TestSuite, main, makeSuite
from zope.testing.doctestunit import DocTestSuite

from zope.interface.verify import verifyClass, verifyObject
from zope.component.interfaces import IViewFactory
from zope.publisher.browser import TestRequest
from zope.schema import Text

from zope.app.form import Widget
from zope.app.form import CustomWidgetFactory
from zope.app.form.interfaces import IWidget
from zope.app.testing.placelesssetup import setUp, tearDown

class TestContext(object):
    __name__ = 'Test'
    title = 'My Test Context'
    description = 'A test context.'

class FooWidget(Widget):
    pass

context = TestContext()
request = TestRequest()

class TestWidget(object):
    """Tests basic widget characteristics.

    Widget implements IWidget:

        >>> verifyClass(IWidget, Widget)
        True
        >>> widget = Widget(context, request)
        >>> verifyObject(IWidget, widget)
        True

    The default values for widget are:

        >>> widget.name
        'field.Test'
        >>> widget.label
        'My Test Context'
        >>> widget.hint
        'A test context.'
        >>> widget.visible
        True

    In the last example, the widget name consists of a prefix, a dot, and the
    field name. You can change the prefix used by the widget as follows:

        >>> widget.setPrefix('newprefix')
        >>> widget.name
        'newprefix.Test'

    To configure a widget, call setRenderedValue with a value that the
    widget should display:

        >>> widget.setRenderedValue('Render Me')

    The way a widget renders a value depends on the type of widget. E.g. a
    browser widget will render the specified value in HTML.
    """

class TestInputWidget(object):
    """Tests the input widget mixin.

    InputWidget is a simple mixin that provides default implementations for
    some of the IInputWidget methods. Because the implementation of widgets
    across UI frameworks is so different, most of the input widget methods
    must be handled by UI specific classes.

    To test the default methods, we must create a basic input widget
    that provides a getInputValue method:

        >>> from zope.app.form import InputWidget
        >>> from zope.app.form.interfaces import WidgetInputError
        >>> class TestInputWidget(InputWidget):
        ...     def getInputValue(self):
        ...         if self.context.required:
        ...             raise WidgetInputError('', '', None)
        ...         else:
        ...             return 'Foo Bar'

    All widgets rely on a field and a request:

        >>> from zope.schema import Field
        >>> field = Field()
        >>> from zope.interface import Interface
        >>> class ITestRequest(Interface):
        ...     pass
        >>> from zope.app.component.tests.views import Request
        >>> widget = TestInputWidget(field, Request(ITestRequest))

    The default implementation of hasValidInput relies on
    getInputValue to perform the validation of the current widget input.
    In this simple example, the widget will always raise an error when its
    field is read only:

        >>> field.readonly = True
        >>> widget.getInputValue()
        Traceback (most recent call last):
        WidgetInputError: ('', '', None)

    A call to hasValidInput returns False instead of raising an error:

        >>> widget.hasValidInput()
        False

    By changing the field's required attribute, getInputValue returns a
    simple string:

        >>> field.required = False
        >>> widget.getInputValue()
        'Foo Bar'

    and hasValidInput returns True:

        >>> widget.hasValidInput()
        True
    """

class TestCustomWidgetFactory(object):
    """Tests the custom widget factory.

    Custom widgets can be created using a custom widget factory. Factories
    are used to assign attribute values to widgets they create.

    The custom widget factory can be used for three widget types:

        -   Regular widgets
        -   Sequence widgets
        -   Vocabulary widgets

    Test regular widget:

        >>> factory = CustomWidgetFactory(FooWidget, bar='baz')
        >>> widget = factory(context, request)
        >>> isinstance(widget, FooWidget)
        True
        >>> widget.bar
        'baz'

    Test sequence widget:

        >>> from zope.schema import TextLine, List
        >>> from zope.app.form.browser import ListSequenceWidget
        >>> value_type = TextLine(__name__=u'bar')
        >>> field = List( __name__=u'foo', value_type=value_type )

        >>> factory = CustomWidgetFactory(ListSequenceWidget, 
        ...     subwidget=CustomWidgetFactory(FooWidget, bar='baz'))

        >>> widget = factory(field, request)
        >>> widget.context.value_type is value_type
        True
        >>> isinstance(widget, ListSequenceWidget)
        True

        >>> isinstance(widget.subwidget, CustomWidgetFactory)
        True
        >>> subwidget = widget.subwidget(context, request)
        >>> isinstance(subwidget, FooWidget)
        True
        >>> subwidget.bar
        'baz'

    Test vocabulary widget:

        >>> from zope.schema import Choice
        >>> from zope.app.form.browser import RadioWidget
        >>> field = Choice( __name__=u'foo', values=['1', '2', '3'] )
        >>> bound = field.bind(context)

        >>> factory = CustomWidgetFactory(RadioWidget, 
        ...      orientation = 'vertical')

        >>> widget = factory(bound, request)
        >>> [term.value for term in widget.context.vocabulary]
        ['1', '2', '3']

        >>> isinstance(widget, RadioWidget)
        True
        >>> widget.orientation
        'vertical'

    """


# BBB: Gone in 3.3 (does not satify IViewFactory)
class TestCustomSequenceWidgetFactory(object):
    """Tests the custom sequence widget factory.

    Custom widgets can be created using a custom widget factory. Factories
    are used to assign attribute values to widgets they create. The custom
    sequence widget factory can be used for a list or tuple of objects:

        >>> from zope.schema import TextLine, List
        >>> from zope.app.form.browser import ListSequenceWidget
        
        
        >>> value_type = TextLine(__name__=u'bar')
        >>> field = List( __name__=u'foo', value_type=value_type )

        >>> ow = CustomWidgetFactory(FooWidget, bar='baz')
        
        >>> import zope.deprecation
        >>> zope.deprecation.__show__.off()
        >>> from zope.app.form import CustomSequenceWidgetFactory
        >>> zope.deprecation.__show__.on()
        >>> sw = CustomSequenceWidgetFactory(ListSequenceWidget, subwidget=ow)
        >>> widget = sw(field, TextLine(), request)
        >>> isinstance(widget, ListSequenceWidget)
        True
        >>> isinstance(widget.subwidget, CustomWidgetFactory)
        True
        >>> widget.subwidget is ow
        True
        >>> widget.context.value_type is value_type
        True
    """

def test_suite():
    return TestSuite((
        DocTestSuite(setUp=setUp, tearDown=tearDown),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

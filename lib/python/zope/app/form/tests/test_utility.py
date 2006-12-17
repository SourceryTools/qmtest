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
"""Form Utilities Tests

$Id: test_utility.py 69217 2006-07-20 03:56:26Z baijum $
"""

from zope.testing import doctest
import zope.security.checker
from zope.interface import Interface, implements
from zope.component.interfaces import IViewFactory, ComponentLookupError
from zope.publisher.browser import TestRequest, BrowserView
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.schema import Field, Int, accessors
from zope.schema.interfaces import IField, IInt

from zope.app.testing import ztapi, placelesssetup
from zope.app.form import Widget
from zope.app.form.interfaces import IWidget, IInputWidget, IDisplayWidget
from zope.app.form.interfaces import ConversionError, InputErrors, WidgetsError
from zope.app.form.utility import no_value, setUpWidget, setUpWidgets
from zope.app.form.utility import setUpEditWidgets, setUpDisplayWidgets
from zope.app.form.utility import getWidgetsData, viewHasInput
from zope.app.form.utility import applyWidgetsChanges
from zope.app.form.tests import utils

request = TestRequest()

class IFoo(IField):
    pass
    
class Foo(Field):
    implements(IFoo)
    
class IBar(IField):
    pass
    
class Bar(Field):
    implements(IBar)

class IBaz(IInt):
    pass

class Baz(Int):
    implements(IBaz)
    
class IContent(Interface):
    foo = Foo()
    bar = Bar()

    
class Content(object):
    implements(IContent)
    __Security_checker__ = utils.SchemaChecker(IContent)
    foo = 'Foo'

class IFooWidget(IWidget):
    pass

class IBarWidget(IWidget):
    pass

class FooWidget(Widget):
    implements(IFooWidget)
    def getPrefix(self): return self._prefix  # exposes _prefix for testing
    def getRenderedValue(self): return self._data # exposes _data for testing
    def renderedValueSet(self): return self._renderedValueSet() # for testing
    
class BarWidget(Widget):
    implements(IBarWidget)
    def getRenderedValue(self): return self._data # exposes _data for testing
    def renderedValueSet(self): return self._renderedValueSet() # for testing

class BazWidget(Widget):
    def getRenderedValue(self): return self._data # exposes _data for testing
    def renderedValueSet(self): return self._renderedValueSet() # for testing

class IExtendedContent(IContent):
    getBaz, setBaz = accessors(Baz())
    getAnotherBaz, setAnotherBaz = accessors(Baz())
    shazam = Foo()

class ExtendedContent(Content):
    implements(IExtendedContent)
    _baz = _anotherbaz = shazam = None
    def getBaz(self): return self._baz
    def setBaz(self, value): self._baz = value
    def getAnotherBaz(self): return self._anotherbaz
    def setAnotherBaz(self, value): self._anotherbaz = value

extended_checker = utils.DummyChecker(
        {'foo':True, 'bar': True, 'getBaz': True, 'setBaz': True, 
         'getAnotherBaz': True, 'setAnotherBaz': False, 'shazam': False},
        {'foo':True, 'bar': False, 'shazam': True})

def setUp():
    """Setup for tests."""
    placelesssetup.setUp()
    ztapi.browserView(IFoo, '', FooWidget, providing=IFooWidget)
    ztapi.browserView(IBar, '', BarWidget, providing=IBarWidget)
    
def tearDown():
    placelesssetup.tearDown()
    
def assertRaises(exceptionType, callable, *args):
    try:
        callable(*args)
        return False
    except Exception, e:
        return isinstance(e, exceptionType)
       
class TestSetUpWidget(object):
    
    def test_typical(self):
        """Documents and tests the typical uses of setUpWidget.
        
        >>> setUp()
          
        setUpWidget ensures that the appropriate widget exists as an
        attribute of a view. There are four required arguments to the
        function:
        
            >>> view = BrowserView(Content(), request)
            >>> name = 'foo'
            >>> field = IContent['foo']
            >>> typeView = IFooWidget
            
        setUpWidget will add the appropriate widget as attribute to view
        named 'foo_widget'.
        
            >>> hasattr(view, 'foo_widget')
            False
            >>> setUpWidget(view, name, field, typeView)
            >>> hasattr(view, 'foo_widget')
            True
            >>> IFooWidget.providedBy(view.foo_widget)
            True
            
        If the view already has an attribute with that name, it attempts to
        use the existing value to create a widget. Two types are supported:
           
            - IViewFactory
            - IWidget
           
        If the existing attribute value implements IViewFactory, it is used
        to create a widget:
           
            >>> widget = FooWidget(IContent['foo'], request)
            >>> class Factory(object):
            ...     implements(IViewFactory)
            ...     def __call__(self, request, context):
            ...         return widget
            >>> setattr(view, 'foo_widget', Factory())
            >>> view.foo_widget is widget
            False
            >>> setUpWidget(view, name, field, typeView)
            >>> view.foo_widget is widget
            True
            
        If the existing attribute value implements IWidget, it is used without
        modification:
           
            >>> setattr(view, 'foo_widget', widget)
            >>> IWidget.providedBy(widget)
            True
            >>> setUpWidget(view, name, field, typeView)
            >>> view.foo_widget is widget
            True

        We now have to cleanup, so that these tests can be run in a loop. We
        modified the 'IContent' interface saying that 'foo' is not mandatory,
        so we have to change that back.

            >>> IContent['foo'].required = True

        >>> tearDown()
        """
        
    def test_validation(self):
        """Documents and tests validation performed by setUpWidget.
        
        >>> setUp()
            
        setUpWidget ensures that the the view has an attribute that implements
        IWidget. If setUpWidget cannot configure a widget, it raises a
        TypeError. 
        
        E.g., if a view already has a widget attribute of the name 
        <field_name> + '_widget' that does not implement IViewFactory or
        IWidget, setUpWidget raises a TypeError: 
        
            >>> view = BrowserView(Content(), request)
            >>> setattr(view, 'foo_widget', 'not a widget')
            >>> assertRaises(TypeError, setUpWidget,
            ...              view, 'foo', IContent['foo'], IFooWidget)
            True
            
        Similarly, if a view has a widget attribute that implements 
        IViewFactory, the object created by the factory must implement IWidget.
        
            >>> class Factory(object):
            ...     implements(IViewFactory)
            ...     def __call__(self, request, context):
            ...         return 'not a widget'
            >>> setattr(view, 'foo_widget', Factory())
            >>> assertRaises(TypeError, setUpWidget,
            ...              view, 'foo', IContent['foo'], IFooWidget)
            True
            
        >>> tearDown()
        """
        
    def test_context(self):
        """Documents and tests the role of context in setUpWidget.
        
        >>> setUp()
        
        setUpWidget configures a widget by associating it to a bound field,
        which is a copy of a schema field that is bound to an object. The
        object the field is bound to can be explicitly specified in the
        setUpWidget 'context' argument.
        
        By default, the context used by setUpWidget is the view context:
            
            >>> context = Content()
            >>> view = BrowserView(context, request)
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget)
            >>> view.foo_widget.context.context is context
            True
            
        Alternatively, you can specify a context explicitly:
            
            >>> view = BrowserView(context, request)
            >>> altContext = Content()
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget,
            ...             context=altContext)
            >>> view.foo_widget.context.context is context
            False
            >>> view.foo_widget.context.context is altContext
            True
                    
        >>> tearDown()
        """
        
    def test_widgetLookup(self):
        """Documents and tests how widgets are looked up by type.
        
        >>> setUp()
        
        If the view does not already have a widget configured for the
        specified field name, setUpWidget will look up a widget using
        an interface specified for the widgetType argument.
        
        Widgets are typically looked up for IInputWidget and IDisplayWidget
        types. To illustrate this, we'll create two widgets, one for editing
        and another for displaying IFoo attributes. Each widget is registered
        as a view providing the appropriate widget type.
        
            >>> class EditFooWidget(Widget):
            ...     implements(IInputWidget)
            ...     def hasInput(self):
            ...         return False
            >>> ztapi.browserViewProviding(IFoo, EditFooWidget, IInputWidget)
            >>> class DisplayFooWidget(Widget):
            ...     implements(IDisplayWidget)            
            >>> ztapi.browserViewProviding(IFoo, DisplayFooWidget, 
            ...                            IDisplayWidget)
            
        A call to setUpWidget will lookup the widgets based on the specified 
        type.
            
            >>> view = BrowserView(Content(), request)
            >>> setUpWidget(view, 'foo', IContent['foo'], IInputWidget)
            >>> IInputWidget.providedBy(view.foo_widget)
            True
            >>> delattr(view, 'foo_widget')
            >>> setUpWidget(view, 'foo', IContent['foo'], IDisplayWidget)
            >>> IDisplayWidget.providedBy(view.foo_widget)
            True
            
        A ComponentError is raised if a widget is not registered for the
        specified type:
            
            >>> class IUnregisteredWidget(IWidget):
            ...     pass
            >>> delattr(view, 'foo_widget')
            >>> assertRaises(ComponentLookupError, setUpWidget,
            ...              view, 'foo', IContent['foo'], IUnregisteredWidget)
            True

        >>> tearDown()
        """
        
    def test_prefix(self):
        """Documents and tests the specification of widget prefixes.
        
        >>> setUp()
        
        Widgets support a prefix that can be used to group related widgets
        on a view. To specify the prefix for a widget, specify in the call to
        setUpWidget:
            
            >>> view = BrowserView(Content(), request)
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget,
            ...             prefix='mygroup')
            >>> view.foo_widget.getPrefix()
            'mygroup.'
        
        >>> tearDown()
        """
        
    def test_value(self):
        """Documents and tests values and setUpWidget.
        
        >>> setUp()
        
        setUpWidget configures the widget with the value specified in the
        'value' argument:
            
            >>> view = BrowserView(Content(), request)
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget, 
            ...             value='Explicit Widget Value')
            >>> view.foo_widget.renderedValueSet()
            True
            >>> view.foo_widget.getRenderedValue()
            'Explicit Widget Value'
            
        The utility module provides a marker object 'no_value' that can be
        used as setUpWidget's 'value' argument to indicate that a value 
        doesn't exist for the bound field. This may seem a bit unusual since
        None is typically used for this purpose. However, None is a valid
        value for many fields and does not indicate 'no value'.
        
        When no_value is specified in a call to setUpWidget, the effected
        widget is not configured with a value:
        
            >>> delattr(view, 'foo_widget')
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget,
            ...             value=no_value)
            >>> view.foo_widget.renderedValueSet()
            False
            
        This is the also default behavior when the value argument is omitted:
            
            >>> delattr(view, 'foo_widget')
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget)
            >>> view.foo_widget.renderedValueSet()
            False
            
        Note that when None is specified for 'value', the widget is configured
        with None:
            
            >>> delattr(view, 'foo_widget')
            >>> setUpWidget(view, 'foo', IContent['foo'], IFooWidget,
            ...             value=None)
            >>> view.foo_widget.renderedValueSet()
            True
            >>> view.foo_widget.getRenderedValue() is None
            True
            
        >>> tearDown()
        """
        
    def test_stickyValues(self):
        """Documents and tests setUpWidget's handling of sticky values.
        
        >>> setUp()
        
        setUpWidget supports the concept of 'sticky values'. A sticky value
        is a value displayed by a widget that should persist across multiple
        across multiple object edit sessions. Sticky values ensure that invalid
        user is available for the user to modify rather than being replaced 
        by some other value.
        
        setUpWidget inferst that a widget has a sticky value if:
            
            - The widget implements IInputWidget
            - The widget returns True for its hasInput method
            
        To illustrate, we'll create and register an edit widget for foo that 
        has input:
            
            >>> class EditFooWidget(Widget):
            ...     implements(IInputWidget)
            ...     _data = "Original Value"
            ...     def hasInput(self): return True
            ...     def getRenderedValue(self): return self._data
            >>> ztapi.browserView(IFoo, '', EditFooWidget, 
            ...                   providing=IInputWidget)
            
        Specifying a value to setUpWidget would typically cause that value
        to be set for the widget:
        
            >>> view = BrowserView(Content(), request)
            >>> setUpWidget(view, 'foo', IContent['foo'], IInputWidget,
            ...     value="A New Value")
            
        However, because EditFooWidget has input (i.e. has a 'sticky' value), 
        setUpWidget will not overwrite its value:
            
            >>> view.foo_widget._data
            'Original Value'
            
        You can use setUpWidget's 'ignoreStickyValues' argument to override
        this behavior and force the widget's value to be overwritten with
        the 'value' argument:
            
            >>> delattr(view, 'foo_widget')
            >>> setUpWidget(view, 'foo', IContent['foo'], IInputWidget,
            ...             value="A New Value", ignoreStickyValues=True)
            >>> view.foo_widget.getRenderedValue()
            'A New Value'
        
        >>> tearDown()
        """

class TestSetUpWidgets(object):
    
    def test_typical(self):
        """Tests the typical use of setUpWidgets.
        
        >>> setUp()
        
        The simplest use of setUpWidget configures a view with widgets of a
        particular type for a schema:
        
            >>> view = BrowserView(Content(), request)
            >>> setUpWidgets(view, IContent, IWidget)
            
        The view now has two widgets, one for each field in the specified
        schema:
            
            >>> IWidget.providedBy(view.foo_widget)
            True
            >>> IWidget.providedBy(view.bar_widget)
            True
            
        Because we did not provide initial values, the widget values are not
        configured:
            
            >>> view.foo_widget.renderedValueSet()
            False
            >>> view.bar_widget.renderedValueSet()
            False
            
        To specify initial values for the widgets, we can use the 'initial'
        argument:
            
            >>> view = BrowserView(Content(), request)
            >>> initial = {'foo': 'Value of Foo', 'bar': 'Value of Bar'}
            >>> setUpWidgets(view, IContent, IWidget, initial=initial)
            >>> view.foo_widget.getRenderedValue()
            'Value of Foo'
            >>> view.bar_widget.getRenderedValue()
            'Value of Bar'
        
        >>> tearDown()
        """        
        
    def test_names(self):
        """Documents and tests the use of names in setUpWidgets.
        
        >>> setUp()
        
        The names argument can be used to configure a specific set of widgets
        for a view:
            
            >>> view = BrowserView(Content(), request)
            >>> IContent.names()
            ['foo', 'bar']
            >>> setUpWidgets(view, IContent, IWidget, names=('bar',))
            >>> hasattr(view, 'foo_widget')
            False
            >>> hasattr(view, 'bar_widget')
            True
        
        >>> tearDown()
        """
        
    def test_delegation(self):
        """Tests setUpWidgets' use of setUpWidget.
        
        >>> setUp()
        
        setUpWidgets delegates several of its arguments to multiple calls to
        setUpWidget - one call for each widget being configured. The arguments
        passed directly through to calls to setUpWidget are:
            
            view
            viewType
            prefix
            ignoreStickyValues
            context

        To illustrate this, we'll replace setUpWidget in the utility module 
        and capture arguments passed to it when setUpWidgets is called.
        
            >>> def setUpWidget(view, name, field, viewType, value=None, 
            ...                 prefix=None, ignoreStickyValues=False, 
            ...                 context=None):
            ...     print "view: %s" % view.__class__
            ...     print "name: %s" % name
            ...     print "field: %s" % field.__class__
            ...     print "viewType: %s" % viewType.__class__
            ...     if value is no_value:
            ...         print "value: not specified"
            ...     else:
            ...         print "value: %s" % value
            ...     print "prefix %s" % prefix
            ...     print "ignoreStickyValues: %s" % ignoreStickyValues
            ...     print "context: %s" % context
            ...     print '---'
            >>> import zope.app.form.utility
            >>> setUpWidgetsSave = zope.app.form.utility.setUpWidget
            >>> zope.app.form.utility.setUpWidget = setUpWidget
            
        When we call setUpWidgets, we should see that setUpWidget is called 
        for each field in the specified schema:
            
            >>> view = BrowserView(Content(), request)
            >>> setUpWidgets(view, IContent, IWidget, 'prefix', True,
            ...              initial={ "bar":"Bar" },
            ...              context="Alt Context")
            view: <class 'zope.publisher.browser.BrowserView'>
            name: foo
            field: <class 'zope.app.form.tests.test_utility.Foo'>
            viewType: <class 'zope.interface.interface.InterfaceClass'>
            value: not specified
            prefix prefix
            ignoreStickyValues: True
            context: Alt Context
            ---
            view: <class 'zope.publisher.browser.BrowserView'>
            name: bar
            field: <class 'zope.app.form.tests.test_utility.Bar'>
            viewType: <class 'zope.interface.interface.InterfaceClass'>
            value: Bar
            prefix prefix
            ignoreStickyValues: True
            context: Alt Context
            ---
            >>> zope.app.form.utility.setUpWidget = setUpWidgetsSave
     
        >>> tearDown()
        """

    def test_forbiddenAttributes(self):
        """Tests that forbidden attributes cause an error in widget setup.

        >>> setUp()

        If an attribute cannot be read from a source object because it's
        forbidden, the ForbiddenAttribute error is allowed to pass through
        to the caller.

        We'll create a field that raises a ForbiddenError itself to simulate
        what would happen when a proxied object's attribute is accessed without
        the required permission.

            >>> class AlwaysForbidden(Field):
            ...     def get(self, source):
            ...         raise ForbiddenAttribute(source, self.__name__)

        We'll also create a schema using this field:

            >>> class IMySchema(Interface):
            ...     tryme = AlwaysForbidden()

        When we use setUpEditWidgets to configure a view with IMySchema:

            >>> view = BrowserView('some context', TestRequest())
            >>> setUpEditWidgets(view, IMySchema)
            Traceback (most recent call last):
            ForbiddenAttribute: ('some context', 'tryme')

        The same applies to setUpDisplayWidgets:

            >>> setUpDisplayWidgets(view, IMySchema)
            Traceback (most recent call last):
            ForbiddenAttribute: ('some context', 'tryme')

        >>> tearDown()
        """
        
class TestFormSetUp(object):
    
    def test_setUpEditWidgets(self):
        """Documents and tests setUpEditWidgets.
        
        >>> setUp()
        
        setUpEditWidgets configures a view to collect field values from a
        user. The function looks up widgets of type IInputWidget for the 
        specified schema.
        
        We'll first create and register widgets for the schema fields for
        which we want input:
            
            >>> class InputWidget(Widget):
            ...     implements(IInputWidget)
            ...     def hasInput(self):
            ...         return False
            ...     def getRenderedValue(self): return self._data
            >>> ztapi.browserViewProviding(IFoo, InputWidget, IInputWidget)
            >>> ztapi.browserViewProviding(IBar, InputWidget, IInputWidget)

        Next we'll configure a view with a context object:
            
            >>> context = Content()
            >>> context.foo = 'abc'
            >>> context.bar = 'def'
            >>> view = BrowserView(context, request)
            
        A call to setUpEditWidgets with the view:
            
            >>> setUpEditWidgets(view, IContent)
            ['foo', 'bar']
            
        configures the view with widgets that accept input for the context 
        field values:
            
            >>> isinstance(view.foo_widget, InputWidget)
            True
            >>> view.foo_widget.getRenderedValue()
            'abc'
            >>> isinstance(view.bar_widget, InputWidget)
            True
            >>> view.bar_widget.getRenderedValue()
            'def'
            
        setUpEditWidgets provides a 'source' argument that provides an
        alternate source of values to be edited:
            
            >>> view = BrowserView(context, request)
            >>> source = Content()
            >>> source.foo = 'abc2'
            >>> source.bar = 'def2'
            >>> setUpEditWidgets(view, IContent, source=source)
            ['foo', 'bar']
            >>> view.foo_widget.getRenderedValue()
            'abc2'
            >>> view.bar_widget.getRenderedValue()
            'def2'
            
        If a field is read only, setUpEditWidgets will use a display widget
        (IDisplayWidget) intead of an input widget to display the field value.
        
            >>> class DisplayWidget(Widget):
            ...     implements(IDisplayWidget)
            >>> ztapi.browserViewProviding(IFoo, DisplayWidget, IDisplayWidget)
            >>> save = IContent['foo'].readonly  # save readonly value
            >>> IContent['foo'].readonly = True
            >>> delattr(view, 'foo_widget')
            >>> setUpEditWidgets(view, IContent)
            ['foo', 'bar']
            >>> isinstance(view.foo_widget, DisplayWidget)
            True
            >>> IContent['foo'].readonly = save  # restore readonly value
        
        By default, setUpEditWidgets raises Unauthorized if it is asked to
        set up a field to which the user does not have permission to
        access or to change.  In the definition of the ExtendedContent
        interface, notice the __Security_checker__ attribute, which stubs
        out a checker that allows the user to view the bar attribute,
        but not set it, and call getAnotherBaz but not setAnotherBaz.
        
            >>> view.context = context = zope.security.checker.Proxy(
            ...     ExtendedContent(), extended_checker)
            >>> setUpEditWidgets(view, IExtendedContent, names=['bar'])
            ... # can' write to bar
            Traceback (most recent call last):
            ...
            Unauthorized: bar
            >>> setUpEditWidgets(
            ... view, IExtendedContent, names=['getAnotherBaz'])
            ... # can't access the setter, setAnotherBaz
            Traceback (most recent call last):
            ...
            Unauthorized: setAnotherBaz
            >>> setUpEditWidgets(
            ... view, IExtendedContent, names=['shazam'])
            ... # can't even access shazam
            Traceback (most recent call last):
            ...
            Unauthorized
        
        Two optional flags can change this behavior.  degradeDisplay=True 
        causes the form machinery to skip fields silently that the user may
        not access.  In this case, the return value of setUpEditWidgets--
        a list of the field names set up--will be different that the names
        provided to the function.
        
            >>> delattr(view, 'foo_widget')
            >>> delattr(view, 'bar_widget')
            >>> ztapi.browserViewProviding(IBaz, InputWidget, IInputWidget)
            >>> setUpEditWidgets(
            ...     view, IExtendedContent, names=['foo', 'shazam', 'getBaz'],
            ...     degradeDisplay=True)
            ['foo', 'getBaz']
            >>> IInputWidget.providedBy(view.foo_widget)
            True
            >>> IInputWidget.providedBy(view.getBaz_widget)
            True
            >>> view.shazam_widget
            Traceback (most recent call last):
            ...
            AttributeError: 'BrowserView' object has no attribute 'shazam_widget'
        
        Similarly, degradeInput=True causes the function to degrade to
        display widgets for any fields that the current user cannot change,
        but can see.
        
            >>> delattr(view, 'foo_widget')
            >>> delattr(view, 'getBaz_widget')
            >>> ztapi.browserViewProviding(IBar, DisplayWidget, IDisplayWidget)
            >>> ztapi.browserViewProviding(IBaz, DisplayWidget, IDisplayWidget)
            >>> setUpEditWidgets(
            ...     view, IExtendedContent, 
            ...     names=['foo', 'bar', 'getBaz', 'getAnotherBaz'],
            ...     degradeInput=True)
            ['foo', 'bar', 'getBaz', 'getAnotherBaz']
            >>> IInputWidget.providedBy(view.foo_widget)
            True
            >>> IDisplayWidget.providedBy(view.bar_widget)
            True
            >>> IInputWidget.providedBy(view.getBaz_widget)
            True
            >>> IDisplayWidget.providedBy(view.getAnotherBaz_widget)
            True
        
        Note that if the user cannot view the current value then they cannot
        view the input widget.  The two flags can then, of course, be used 
        together.
        
            >>> delattr(view, 'foo_widget')
            >>> delattr(view, 'bar_widget')
            >>> delattr(view, 'getBaz_widget')
            >>> delattr(view, 'getAnotherBaz_widget')
            >>> setUpEditWidgets(
            ...     view, IExtendedContent, 
            ...     names=['foo', 'bar', 'shazam', 'getBaz', 'getAnotherBaz'],
            ...     degradeInput=True)
            Traceback (most recent call last):
            ...
            Unauthorized
            >>> setUpEditWidgets(
            ...     view, IExtendedContent, 
            ...     names=['foo', 'bar', 'shazam', 'getBaz', 'getAnotherBaz'],
            ...     degradeInput=True, degradeDisplay=True)
            ['foo', 'bar', 'getBaz', 'getAnotherBaz']
            >>> IInputWidget.providedBy(view.foo_widget)
            True
            >>> IDisplayWidget.providedBy(view.bar_widget)
            True
            >>> IInputWidget.providedBy(view.getBaz_widget)
            True
            >>> IDisplayWidget.providedBy(view.getAnotherBaz_widget)
            True
            >>> view.shazam_widget
            Traceback (most recent call last):
            ...
            AttributeError: 'BrowserView' object has no attribute 'shazam_widget'
        
        >>> tearDown()
        """
        
    def test_setUpDisplayWidgets(self):
        """Documents and tests setUpDisplayWidgets.
        
        >>> setUp()
        
        setUpDisplayWidgets configures a view for use as a display only form.
        The function looks up widgets of type IDisplayWidget for the specified
        schema.
        
        We'll first create and register widgets for the schema fields
        we want to edit:
            
            >>> class DisplayWidget(Widget):
            ...     implements(IDisplayWidget)
            ...     def getRenderedValue(self): return self._data
            >>> ztapi.browserViewProviding(IFoo, DisplayWidget, IDisplayWidget)
            >>> ztapi.browserViewProviding(IBar, DisplayWidget, IDisplayWidget)

        Next we'll configure a view with a context object:
            
            >>> context = Content()
            >>> context.foo = 'abc'
            >>> context.bar = 'def'
            >>> view = BrowserView(context, request)
            
        A call to setUpDisplayWidgets with the view:
            
            >>> setUpDisplayWidgets(view, IContent)
            ['foo', 'bar']
            
        configures the view with widgets that display the context fields:
            
            >>> isinstance(view.foo_widget, DisplayWidget)
            True
            >>> view.foo_widget.getRenderedValue()
            'abc'
            >>> isinstance(view.bar_widget, DisplayWidget)
            True
            >>> view.bar_widget.getRenderedValue()
            'def'
            
        Like setUpEditWidgets, setUpDisplayWidgets accepts a 'source'
        argument that provides an alternate source of values to be edited:
            
            >>> view = BrowserView(context, request)
            >>> source = Content()
            >>> source.foo = 'abc2'
            >>> source.bar = 'def2'
            >>> setUpDisplayWidgets(view, IContent, source=source)
            ['foo', 'bar']
            >>> view.foo_widget.getRenderedValue()
            'abc2'
            >>> view.bar_widget.getRenderedValue()
            'def2'
        
        Also like setUpEditWidgets, the degradeDisplay flag allows widgets
        to silently disappear if they are unavailable.
        
            >>> view.context = context = zope.security.checker.Proxy(
            ...     ExtendedContent(), extended_checker)
            >>> delattr(view, 'foo_widget')
            >>> delattr(view, 'bar_widget')
            >>> ztapi.browserViewProviding(IBaz, DisplayWidget, IDisplayWidget)
            >>> setUpDisplayWidgets(
            ...     view, IExtendedContent, 
            ...     names=['foo', 'bar', 'shazam', 'getBaz', 'getAnotherBaz'])
            Traceback (most recent call last):
            ...
            Unauthorized
            >>> setUpDisplayWidgets(
            ...     view, IExtendedContent, 
            ...     names=['foo', 'bar', 'shazam', 'getBaz', 'getAnotherBaz'],
            ...     degradeDisplay=True)
            ['foo', 'bar', 'getBaz', 'getAnotherBaz']
            >>> IDisplayWidget.providedBy(view.foo_widget)
            True
            >>> IDisplayWidget.providedBy(view.bar_widget)
            True
            >>> IDisplayWidget.providedBy(view.getBaz_widget)
            True
            >>> IDisplayWidget.providedBy(view.getAnotherBaz_widget)
            True
            >>> view.shazam_widget
            Traceback (most recent call last):
            ...
            AttributeError: 'BrowserView' object has no attribute 'shazam_widget'
        
        >>> tearDown()
        """
        
class TestForms(object):
    
    def test_viewHasInput(self):
        """Tests viewHasInput.
        
        >>> setUp()
        
        viewHasInput returns True if any of the widgets for a set of fields
        have user input.
        
        This method is typically invoked on a view that has been configured
        with one setUpEditWidgets.
        
            >>> class InputWidget(Widget):
            ...     implements(IInputWidget)
            ...     input = None
            ...     def hasInput(self):
            ...         return self.input is not None
            >>> ztapi.browserViewProviding(IFoo, InputWidget, IInputWidget)
            >>> ztapi.browserViewProviding(IBar, InputWidget, IInputWidget)
            >>> view = BrowserView(Content(), request)
            >>> setUpEditWidgets(view, IContent)
            ['foo', 'bar']
            
        Because InputWidget is configured to not have input by default, the
        view does not have input:
            
            >>> viewHasInput(view, IContent)
            False
            
        But if we specify input for at least one widget:
            
            >>> view.foo_widget.input = 'Some Value'
            >>> viewHasInput(view, IContent)
            True
            
        >>> tearDown()
        """
        
    def test_applyWidgetsChanges(self):
        """Documents and tests applyWidgetsChanges.
        
        >>> setUp()
        
        applyWidgetsChanges updates the view context, or an optional alternate
        context, with widget values. This is typically called when a form
        is submitted.
        
        We'll first create a simple edit widget that can be used to update
        an object:
        
            >>> class InputWidget(Widget):
            ...     implements(IInputWidget)           
            ...     input = None
            ...     valid = True
            ...     def hasInput(self):
            ...         return input is not None
            ...     def applyChanges(self, object):
            ...         if not self.valid:
            ...             raise ConversionError('invalid input')
            ...         field = self.context
            ...         field.set(object, self.input)
            ...         return True
            >>> ztapi.browserViewProviding(IFoo, InputWidget, IInputWidget)
            >>> ztapi.browserViewProviding(IBar, InputWidget, IInputWidget)
            
        Before calling applyWidgetsUpdate, we need to configure a context and
        a view with edit widgets:
            
            >>> context = Content()
            >>> view = BrowserView(context, request)
            >>> setUpEditWidgets(
            ...     view, IContent, context=context, names=('foo',))
            ['foo']
            
        We now specify new widget input and apply the changes: 

            >>> view.foo_widget.input = 'The quick brown fox...'
            >>> context.foo
            'Foo'
            >>> applyWidgetsChanges(view, IContent, names=('foo',))
            True
            >>> context.foo
            'The quick brown fox...'
            
        By default, applyWidgetsChanges applies the new widget values to the
        view context. Alternatively, we can provide a 'target' argument to
        be updated:
            
            >>> target = Content()
            >>> target.foo
            'Foo'
            >>> applyWidgetsChanges(view, IContent, target=target, 
            ...                     names=('foo',))
            True
            >>> target.foo
            'The quick brown fox...'
            
        applyWidgetsChanges is typically used in conjunction with one of the
        setUp utility functions. If applyWidgetsChanges is called using a
        view that was not previously configured with a setUp function, or
        was not otherwise configured with widgets for each of the applicable
        fields, an AttributeError will be raised:
            
            >>> view = BrowserView(context, request)
            >>> applyWidgetsChanges(view, IContent, names=('foo',))
            Traceback (most recent call last):
            AttributeError: 'BrowserView' object has no attribute 'foo_widget'

        When applyWidgetsChanges is called with multiple form
        fields, some with valid data and some with invalid data, 
        *changes may be applied*.  For instance, below see that context.foo
        changes from 'Foo' to 'a' even though trying to change context.bar
        fails.  Generally, ZODB transactional behavior is expected to
        correct this sort of problem.

            >>> context = Content()
            >>> view = BrowserView(context, request)
            >>> setUpEditWidgets(view, IContent, names=('foo', 'bar'))
            ['foo', 'bar']
            >>> view.foo_widget.input = 'a'
            >>> view.bar_widget.input = 'b'
            >>> view.bar_widget.valid = False
            >>> context.foo
            'Foo'
            >>> getattr(context, 'bar', 'not really')
            'not really'
            >>> applyWidgetsChanges(view, IContent, names=('foo', 'bar'))
            Traceback (most recent call last):
            WidgetsError: ConversionError: ('invalid input', None)
            >>> context.foo
            'a'
            >>> getattr(context, 'bar', 'not really')
            'not really'

        >>> tearDown()
        """
        
class TestGetWidgetsData(object):
    
    def test_typical(self):
        """Documents and tests the typical use of getWidgetsData.
        
        >>> setUp()
        
        getWidgetsData retrieves the current values from widgets on a view.
        For this test, we'll create a simple edit widget and register it
        for the schema field types:
            
            >>> class InputWidget(Widget):
            ...     implements(IInputWidget)
            ...     input = None
            ...     def hasInput(self):
            ...         return self.input is not None
            ...     def getInputValue(self):
            ...         return self.input
            >>> ztapi.browserViewProviding(IFoo, InputWidget, IInputWidget)
            >>> ztapi.browserViewProviding(IBar, InputWidget, IInputWidget)

        We use setUpEditWidgets to configure a view with widgets for the
        IContent schema:
        
            >>> view = BrowserView(Content(), request)
            >>> setUpEditWidgets(view, IContent)
            ['foo', 'bar']
            
        The simplest form of getWidgetsData requires a view and a schema:
            
            >>> try:
            ...     result = getWidgetsData(view, IContent)
            ... except Exception, e:
            ...     print 'getWidgetsData failed'
            ...     e
            getWidgetsData failed
            MissingInputError: ('foo', u'', 'the field is required')
            MissingInputError: ('bar', u'', 'the field is required')
            
        We see that getWidgetsData raises a MissingInputError if a required
        field does not have input from a widget.:
            
            >>> view.foo_widget.input = 'Input for foo'
            >>> view.bar_widget.input = 'Input for bar'
            >>> result = getWidgetsData(view, IContent)
            
        The result of getWidgetsData is a map of field names to widget values.
        
            >>> keys = result.keys(); keys.sort(); keys
            ['bar', 'foo']
            >>> result['foo']
            'Input for foo'
            >>> result['bar']
            'Input for bar'
            
        If a field is not required, however:
            
            >>> IContent['foo'].required = False
            
        we can omit input for its widget:
            
            >>> view.foo_widget.input = None
            >>> result = getWidgetsData(view, IContent)
            >>> 'foo' in result
            False
            
        Note that when a widget indicates that is does not have input, its
        results are omitted from getWidgetsData's return value. Users of
        getWidgetsData should explicitly check for field values before
        accessing them:
            
            >>> for name in IContent:
            ...     if name in result:
            ...         print (name, result[name])
            ('bar', 'Input for bar')
            
        You can also specify an optional 'names' argument (a tuple) to 
        request a subset of the schema fields:
            
            >>> result = getWidgetsData(view, IContent, names=('bar',))
            >>> result.keys()
            ['bar']
            
        >>> tearDown()
        """
        
    def test_widgetsErrorException(self):
        """Documents and tests WidgetsError.
        
        WidgetsError wraps one or more errors, which are specified as a
        sequence in the 'errors' argument:
        
            >>> error = WidgetsError(('foo',))
            >>> error
            str: foo
            
        WidgetsError also provides a 'widgetsData' attribute, which is a
        map of valid field values, keyed by field name, that were obtained
        in the same read operation that generated the errors:
            
            >>> error = WidgetsError(('foo',), widgetsData={'bar': 'Bar'})
            >>> error.widgetsData
            {'bar': 'Bar'}
            
        The most typical use of this error is when reading a set of widget
        values -- the read operation can generate more than one error, as well
        as a set of successfully read values:
            
            >>> values = {'foo': 'Foo'}
            >>> errors = []
            >>> widgetsData = {}
            >>> for name in ('foo', 'bar'):  # some list of values to read
            ...     try:
            ...         widgetsData[name] = values[name]  # read operation
            ...     except Exception, e:
            ...         errors.append(e)    # capture all errors
            >>> if errors:
            ...     widgetsError = WidgetsError(errors, widgetsData)
            ...     raise widgetsError
            Traceback (most recent call last):
            WidgetsError: KeyError: 'bar'
            
        The handler of error can access all of the widget error as well as
        the widget values read:
            
            >>> for error in widgetsError:
            ...     error.__class__.__name__
            'KeyError'
            >>> widgetsError.widgetsData
            {'foo': 'Foo'}
        """
            
def test_suite():
    return doctest.DocTestSuite()

if __name__=='__main__':
    main(defaultTest='test_suite')

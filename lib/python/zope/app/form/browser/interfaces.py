##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Form and Widget Interfaces

$Id: interfaces.py 30317 2005-05-09 18:15:54Z benji_york $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.schema import TextLine, Bool
from zope.app.form.interfaces import IWidget, IInputWidget


class IBrowserWidget(IWidget):
    """A widget for use in a web browser UI."""

    def __call__():
        """Render the widget."""

    def hidden():
        """Render the widget as a hidden field."""

    def error():
        """Render the validation error for the widget, or return
        an empty string if no error"""
        
        
class ISimpleInputWidget(IBrowserWidget, IInputWidget):
    """A widget that uses a single HTML element to collect user input."""
    
    tag = TextLine(
        title=u'Tag',
        description=u'The widget HTML element.')
        
    type = TextLine(
        title=u'Type',
        description=u'The element type attribute',
        required=False)
        
    cssClass = TextLine(
        title=u'CSS Class',
        description=u'The element class attribute.',
        required=False)
        
    extra = TextLine(
        title=u'Extra',
        description=u'The element extra attribute.',
        required=False)
        
        
class ITextBrowserWidget(ISimpleInputWidget):
    
    convert_missing_value = Bool(
        title=u'Translate Input Value',
        description=
            u'If True, an empty string is converted to field.missing_value.',
        default=True)
    

class IFormCollaborationView(Interface):
    """Views that collaborate to create a single form.

    When a form is applied, the changes in the form need to
    be applied to individual views, which update objects as
    necessary.
    """

    def __call__():
        """Render the view as a part of a larger form.

        Form input elements should be included, prefixed with the
        prefix given to setPrefix.

        `form` and `submit` elements should not be included. They
        will be provided for the larger form.
        """

    def setPrefix(prefix):
        """Set the `prefix` used for names of input elements

        Element names should begin with the given `prefix`,
        followed by a dot.
        """

    def update():
        """Update the form with data from the request."""


class IAddFormCustomization(Interface):
    """API for add form customization.

    Classes supplied when defining add forms may need to override some
    of these methods.

    In particular, when the context of an add form is not an `IAdding`,
    a subclass needs to override `nextURL` and one of `add` or
    `createAndAdd`.

    To see how all this fits together, here's pseudo code for the
    update() method of the form:

    def update(self):
        data = <get data from widgets> # a dict
        self.createAndAdd(data)
        self.request.response.redirect(self.nextURL())

    def createAndAdd(self, data):
        content = <create the content from the data>
        content = self.add(content) 
        <set after-add attributes on content>
    """

    def createAndAdd(data):
        """Create a new object from the given data and the resulting object.

        The data argument is a dictionary with values supplied by the form.

        If any user errors occur, they should be collected into a list
        and raised as a ``WidgetsError``.

        (For the default implementation, see pseudo-code in class docs.)
        """

    def add(content):
        """Add the given content.

        This method is overridden when the context of the add form is
        not an `IAdding`.  In this case, the class that customizes the
        form must take over adding the object.

        The default implementation returns `self.context.add(content)`,
        i.e. it delegates to the `IAdding` view.
        """

    def nextURL():
        """Return the URL to be displayed after the add operation.

        This can be relative to the view's context.

        The default implementation returns `self.context.nextURL()`,
        i.e. it delegates to the `IAdding` view.
        """

class IWidgetInputErrorView(Interface):
    """Display an input error as a snippet of text."""

    def snippet():
        """Convert a widget input error to an html snippet."""


class ITerms(Interface):

    def getTerm(value):
        """Return an ITitledTokenizedTerm object for the given value
        
        LookupError is raised if the value isn't in the source
        """
        
    def getValue(token):
        """Return a value for a given identifier token
        
        LookupError is raised if there isn't a value in the source.
        """

class ISourceQueryView(Interface):
    """View support for querying non-iterable sources
    """

    def render(name):
        """Return a rendering of the search form elements

        The query view should use `name` as the prefix for its widgets.
        """

    def results(name):
        """Return the results of the query

        The query view should use `name` as the prefix for its widgets.

        The value returned is an iterable.

        None may be returned to indicate that there are no results.
        """

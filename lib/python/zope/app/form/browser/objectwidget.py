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
"""Browser widgets for text-like data

$Id: objectwidget.py 67953 2006-05-03 23:49:36Z stainsby $
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements
from zope.schema import getFieldNamesInOrder

from zope.app import zapi
from zope.app.form.interfaces import IInputWidget
from zope.app.form import InputWidget
from zope.app.form.browser.widget import BrowserWidget
from zope.app.form.utility import setUpWidgets, applyWidgetsChanges
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.form.browser.interfaces import IWidgetInputErrorView


class ObjectWidgetView:

    template = ViewPageTemplateFile('objectwidget.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return self.template()


class ObjectWidget(BrowserWidget, InputWidget):
    """A widget over an Interface that contains Fields.

    ``factory``

      factory used to create content that this widget (field) represents

    ``*_widget``

      Optional CustomWidgets used to generate widgets for the fields in this
      widget
    """

    implements(IInputWidget)

    _object = None      # the object value (from setRenderedValue & request)
    _request_parsed = False

    def __init__(self, context, request, factory, **kw):
        super(ObjectWidget, self).__init__(context, request)

        # define view that renders the widget
        self.view = ObjectWidgetView(self, request)

        # factory used to create content that this widget (field)
        # represents
        self.factory = factory

        # handle foo_widget specs being passed in
        self.names = getFieldNamesInOrder(self.context.schema)
        for k, v in kw.items():
            if k.endswith('_widget'):
                setattr(self, k, v)

        # set up my subwidgets
        self._setUpEditWidgets()

    def setPrefix(self, prefix):
        super(ObjectWidget, self).setPrefix(prefix)
        self._setUpEditWidgets()

    def _setUpEditWidgets(self):
        # subwidgets need a new name
        setUpWidgets(self, self.context.schema, IInputWidget,
                         prefix=self.name, names=self.names,
                         context=self.context)

    def __call__(self):
        return self.view()

    def legendTitle(self):
        return self.context.title or self.context.__name__

    def getSubWidget(self, name):
        return getattr(self, '%s_widget' % name)

    def subwidgets(self):
        return [self.getSubWidget(name) for name in self.names]

    def hidden(self):
        """Render the object as hidden fields."""
        result = []
        for name in self.names:
            result.append(getSubwidget(name).hidden())
        return "".join(result)

    def error(self):
        if self._error:
            errormessages = []
            keys = self._error.keys(); keys.sort()
            for key in keys:
                errormessages.append(str(key) + ': ')
                errormessages.append( zapi.getMultiAdapter((self._error[key], self.request),
                                        IWidgetInputErrorView).snippet())
                errormessages.append(str(key) + ', ')
            return ''.join(errormessages[0:-1])
        return ""

    def getInputValue(self):
        """Return converted and validated widget data.

        The value for this field will be represented as an `ObjectStorage`
        instance which holds the subfield values as attributes. It will
        need to be converted by higher-level code into some more useful
        object (note that the default EditView calls `applyChanges`, which
        does this).
        """

        errors = []
        content = self.factory()
        for name in self.names:
            try:
                setattr(content, name, self.getSubWidget(name).getInputValue())
            except Exception, e:
                errors.append(e)
                if self._error is None:
                    self._error = {}
                
                if name not in self._error:
                    self._error[name] = e

        if errors:
            raise errors[0]

        return content


    def applyChanges(self, content):
        field = self.context

        # create our new object value
        value = field.query(content, None)
        if value is None:
            # TODO: ObjectCreatedEvent here would be nice
            value = self.factory()

        # apply sub changes, see if there *are* any changes
        # TODO: ObjectModifiedEvent here would be nice
        changes = applyWidgetsChanges(self, field.schema, target=value,
                                      names=self.names)

        # if there's changes, then store the new value on the content
        if changes:
            field.set(content, value)
        # TODO: If value implements ILocation, set name to field name and
        # parent to content

        return changes

    def hasInput(self):
        """Is there input data for the field

        Return ``True`` if there is data and ``False`` otherwise.
        """
        for name in self.names:
            if self.getSubWidget(name).hasInput():
                return True
        return False

    def setRenderedValue(self, value):
        """Set the default data for the widget.

        The given value should be used even if the user has entered
        data.
        """
        # re-call setupwidgets with the content
        self._setUpEditWidgets()
        for name in self.names:
            self.getSubWidget(name).setRenderedValue(getattr(value, name, None))

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
"""Generic Widget base classes

$Id: __init__.py 71638 2006-12-20 23:34:35Z jacobholm $
"""
__docformat__ = 'restructuredtext'

from zope.app.form.interfaces import IWidget, InputErrors
from zope.cachedescriptors.property import readproperty
from zope.component.interfaces import IViewFactory
from zope.deprecation import deprecated
from zope.interface import implements
from zope.i18n import translate
from zope.schema.interfaces import IChoice, ICollection

class Widget(object):
    """Mixin class providing functionality common across widget types."""

    implements(IWidget)

    _prefix = 'field.'
    _data_marker = object()
    _data = _data_marker

    visible = True

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.name = self._prefix + context.__name__

    @readproperty
    def label(self):
        """The widget label.

        This read-write attribute defaults to the title of the context.
        """
        return self.context.title

    @readproperty
    def hint(self):
        """A hint regarding the use of the widget.

        This read-write attribute defaults to the description of the context.
        """
        return self.context.description

    def _translate(self, text):
        return translate(text, context=self.request, default=text)

    def _renderedValueSet(self):
        """Returns ``True`` if the the widget's rendered value has been set.

        This is a convenience method that widgets can use to check whether
        or not `setRenderedValue` was called.
        """
        return self._data is not self._data_marker

    def setPrefix(self, prefix):
        if prefix and not prefix.endswith("."):
            prefix += '.'
        self._prefix = prefix
        self.name = prefix + self.context.__name__

    def setRenderedValue(self, value):
        self._data = value


class InputWidget(Widget):
    """Mixin class providing some default input widget methods."""

    def hasValidInput(self):
        try:
            self.getInputValue()
            return True
        except InputErrors:
            return False

    def applyChanges(self, content):
        field = self.context
        value = self.getInputValue()
        if field.query(content, self) != value:
            field.set(content, value)
            return True
        else:
            return False


class CustomWidgetFactory(object):
    """Custom Widget Factory."""
    implements(IViewFactory)

    def __init__(self, widget_factory, *args, **kw):
        self._widget_factory = widget_factory
        self.args = args
        self.kw = kw

    def _create(self, args):
        instance = self._widget_factory(*args)
        for name, value in self.kw.items():
            setattr(instance, name, value)
        return instance

    def __call__(self, context, request):
        # Sequence widget factory
        if ICollection.providedBy(context):
            args = (context, context.value_type, request) + self.args

        # Vocabulary widget factory
        elif IChoice.providedBy(context):
            args = (context, context.vocabulary, request) + self.args

        # Regular widget factory
        else:
            args = (context, request) + self.args

        return self._create(args)

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
"""Support for display-only pages based on schema.

$Id: schemadisplay.py 67630 2006-04-27 00:54:03Z jim $
"""
__docformat__ = 'restructuredtext'

import zope.component
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.browser import BrowserView
from zope.schema import getFieldNamesInOrder
from zope.security.checker import defineChecker, NamesChecker

from zope.app.form.utility import setUpDisplayWidgets
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.pagetemplate.simpleviewclass import SimpleViewClass

class DisplayView(BrowserView):
    """Simple display-view base class.

    Subclasses should provide a `schema` attribute defining the schema
    to be displayed.
    """

    errors = ()
    update_status = ''
    label = ''

    # Fall-back field names computes from schema
    fieldNames = property(lambda self: getFieldNamesInOrder(self.schema))

    def __init__(self, context, request):
        super(DisplayView, self).__init__(context, request)
        self._setUpWidgets()

    def _setUpWidgets(self):
        self.adapted = self.schema(self.context)
        setUpDisplayWidgets(self, self.schema, source=self.adapted,
                            names=self.fieldNames)

    def setPrefix(self, prefix):
        for widget in self.widgets():
            widget.setPrefix(prefix)

    def widgets(self):
        return [getattr(self, name+'_widget')
                for name in self.fieldNames]


def DisplayViewFactory(name, schema, label, permission, layer,
                       template, default_template, bases, for_, fields,
                       fulledit_path=None, fulledit_label=None):
    class_ = SimpleViewClass(template, used_for=schema, bases=bases,
                             name=name)
    class_.schema = schema
    class_.label = label
    class_.fieldNames = fields
    class_.fulledit_path = fulledit_path
    if fulledit_path and (fulledit_label is None):
        fulledit_label = "Full display"
    class_.fulledit_label = fulledit_label
    class_.generated_form = ViewPageTemplateFile(default_template)
    defineChecker(class_,
                  NamesChecker(("__call__", "__getitem__", "browserDefault"),
                               permission))

    if layer is None:
        layer = IDefaultBrowserLayer

    sm = zope.component.getGlobalSiteManager()
    sm.registerAdapter(class_, (for_, layer), Interface, name)

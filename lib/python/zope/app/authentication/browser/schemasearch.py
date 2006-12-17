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
"""Search interface for queriables.

$Id: schemasearch.py 39064 2005-10-11 18:40:10Z philikon $
"""
__docformat__ = "reStructuredText"

from zope.interface import implements
from zope.i18n import translate
from zope.schema import getFieldsInOrder
from zope.app.zapi import getName, getPath
from zope.app.form.utility import setUpWidgets, getWidgetsData
from zope.app.form.interfaces import IInputWidget
from zope.app.form.browser.interfaces import ISourceQueryView
from zope.app.i18n import ZopeMessageFactory as _


search_label = _('search-button', 'Search')
source_label = _(u"Source path")
source_title = _(u"Path to the source utility")

class QuerySchemaSearchView(object):
    implements(ISourceQueryView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def render(self, name):
        schema = self.context.schema
        sourcename = getName(self.context)
        sourcepath = getPath(self.context)
        setUpWidgets(self, schema, IInputWidget, prefix=name+'.field')
        html = []

        # add sub title for source search field
        html.append('<h4>%s</h4>' % sourcename)

        # start row for path display field
        html.append('<div class="row">')

        # for each source add path of source
        html.append('  <div class="label">')
        label = translate(source_label, context=self.request)
        title = translate(source_title, context=self.request)
        html.append('    <label for="%s" title="%s">' % (sourcename, title))
        html.append('      %s' % label)
        html.append('    </label>')
        html.append('  </div>')
        html.append('  <div class="field">')
        html.append('      %s' % sourcepath)
        html.append('  </div>')
        html.append('</div>')

        # start row for search fields
        html.append('<div class="row">')

        for field_name, field in getFieldsInOrder(schema):
            widget = getattr(self, field_name+'_widget')

            # for each field add label...
            html.append('  <div class="label">')
            html.append('    <label for="%s" title="%s">'
                        % (widget.name, widget.hint))
            html.append('      %s' % widget.label)
            html.append('    </label>')
            html.append('  </div>')

            # ...and field widget
            html.append('  <div class="field">')
            html.append('    %s' % widget())

            if widget.error():
                html.append('    <div class="error">')
                html.append('      %s' % widget.error())
                html.append('    </div>')
            html.append('  </div>')
        # end row
        html.append('</div>')

        # add search button for search fields
        html.append('<div class="row">')
        html.append('  <div class="field">')
        html.append('    <input type="submit" name="%s" value="%s" />'
                     % (name+'.search',
                        translate(search_label, context=self.request)))
        html.append('  </div>')
        html.append('</div>')

        return '\n'.join(html)

    def results(self, name):
        if not (name+'.search' in self.request):
            return None
        schema = self.context.schema
        setUpWidgets(self, schema, IInputWidget, prefix=name+'.field')
        data = getWidgetsData(self, schema)
        return self.context.search(data)

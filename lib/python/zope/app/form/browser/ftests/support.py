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
"""Support Functions for Widget Functional Tests

$Id: support.py 37569 2005-07-29 21:10:06Z poster $
"""
import re
from zope.configuration import xmlconfig

def registerEditForm(schema, widgets={}):
    """Registers an edit form for the specified schema.
    
    widgets is a mapping of field name to dict. The dict for each field must
    contain a 'class' item, which is the widget class, and any additional
    widget attributes (e.g. text field size, rows, cols, etc.)
    """
    widgetsXml = []
    for field in widgets:
        widgetsXml.append('<widget field="%s"' % field)
        for attr in widgets[field]:
            widgetsXml.append(' %s="%s"' % (attr, widgets[field][attr]))
        widgetsXml.append(' />')
    xmlconfig.string("""
        <configure xmlns="http://namespaces.zope.org/browser">
          <include package="zope.app.form.browser" file="meta.zcml" />
          <editform
            name="edit.html"
            schema="%s"
            permission="zope.View">
            %s
          </editform>
        </configure>
        """ % (schema.__identifier__, ''.join(widgetsXml)))


def defineSecurity(class_, schema):
    class_ = '%s.%s' % (class_.__module__, class_.__name__)
    schema = schema.__identifier__
    xmlconfig.string("""
        <configure xmlns="http://namespaces.zope.org/zope">
          <include package="zope.app.component" file="meta.zcml" />
          <class class="%s">
            <require
              permission="zope.Public"
              interface="%s"
              set_schema="%s" />
          </class>
        </configure>
        """ % (class_, schema, schema))


def defineWidgetView(field_interface, widget_class, view_type):
    field_interface = field_interface.__identifier__
    widget_class = '%s.%s' % (widget_class.__module__, widget_class.__name__)
    view_type = '%s.%s' % (view_type.__module__, view_type.__name__)
    xmlconfig.string("""
        <configure xmlns="http://namespaces.zope.org/zope">
          <include package="zope.app.component" file="meta.zcml" />
          <view
            for="%s"
            type="zope.publisher.interfaces.browser.IBrowserRequest"
            factory="%s"
            provides="%s"
            permission="zope.Public"
            />
        </configure>
        """ % (field_interface, widget_class, view_type))


def patternExists(pattern, source, flags=0):
    return re.search(pattern, source, flags) is not None


def validationErrorExists(field, error_msg, source):
    regex = re.compile(r'%s.*?name="field.(\w+)(?:\.[\w\.]+)?"' % (error_msg,),
                       re.DOTALL)
    # compile it first because Python 2.3 doesn't allow flags in findall
    return field in regex.findall(source)


def missingInputErrorExists(field, source):
    return validationErrorExists(field, 'Required input is missing.', source)


def invalidValueErrorExists(field, source):
    # assumes this error is displayed for select elements
    return patternExists(
        'Invalid value.*name="field.%s".*</select>' % field,
        source, re.DOTALL)


def updatedMsgExists(source):
    return patternExists('<p>Updated .*</p>', source)

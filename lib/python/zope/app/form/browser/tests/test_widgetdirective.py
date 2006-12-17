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
"""Tests for the <widget> subdirective for the generated form pages.

$Id$
"""
import unittest

import zope.interface
import zope.configuration.xmlconfig
import zope.publisher.browser
import zope.schema

import zope.app.container.interfaces
import zope.app.form.browser.interfaces
import zope.app.form.interfaces
from zope.app.form.tests import utils
import zope.app.testing.placelesssetup

from zope.app import zapi

__docformat__ = "reStructuredText"


class IContent(zope.interface.Interface):

    field = zope.schema.TextLine(
        title=u"Field",
        description=u"Sample input field",
        required=False,
        )


class Content(object):

    zope.interface.implements(IContent)
    __Security_checker__ = utils.SchemaChecker(IContent)

    __parent__ = None
    __name__ = "sample-content"

    field = None


class Adding(object):

    zope.interface.implements(
        zope.app.container.interfaces.IAdding)

    def add(self, content):
        self.content = content


class WidgetDirectiveTestCase(zope.app.testing.placelesssetup.PlacelessSetup,
                              unittest.TestCase):

    def setUp(self):
        super(WidgetDirectiveTestCase, self).setUp()
        zope.configuration.xmlconfig.file("widgetDirectives.zcml",
                                          zope.app.form.browser.tests)

    def get_widget(self, name, context):
        request = zope.publisher.browser.TestRequest()
        view = zapi.getMultiAdapter((context, request), name=name)
        return view.field_widget

    def test_addform_widget_without_class(self):
        w = self.get_widget("add.html", Adding())
        self.assert_(zope.app.form.interfaces.IInputWidget.providedBy(w))
        self.assertEqual(w.extraAttr, "42")

    def test_editform_widget_without_class(self):
        w = self.get_widget("edit.html", Content())
        self.assert_(zope.app.form.interfaces.IInputWidget.providedBy(w))
        self.assertEqual(w.extraAttr, "84")

    def test_subeditform_widget_without_class(self):
        w = self.get_widget("subedit.html", Content())
        self.assert_(zope.app.form.interfaces.IInputWidget.providedBy(w))
        self.assertEqual(w.extraAttr, "168")


def test_suite():
    return unittest.makeSuite(WidgetDirectiveTestCase)

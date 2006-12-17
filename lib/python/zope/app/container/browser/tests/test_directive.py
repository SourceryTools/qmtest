##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""'containerView' directive test

$Id: test_directive.py 67630 2006-04-27 00:54:03Z jim $
"""
import re
import pprint
import cStringIO

import unittest
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.testing.doctestunit import DocTestSuite
from zope.app.container.browser.metaconfigure import containerViews

atre = re.compile(' at [0-9a-fA-Fx]+')

class Context(object):
    actions = ()
    info = ''
    
    def action(self, discriminator, callable, args):
        self.actions += ((discriminator, callable, args), )
        self.info = 'info'

    def __repr__(self):
        stream = cStringIO.StringIO()
        pprinter = pprint.PrettyPrinter(stream=stream, width=60)
        pprinter.pprint(self.actions)
        r = stream.getvalue()
        return (''.join(atre.split(r))).strip()

class I(Interface):
    pass


class ITestLayer(IBrowserRequest):
    pass


def test_containerViews():
    """
    >>> from zope.app.publisher.browser.menumeta import menus
    >>> from zope.interface.interface import InterfaceClass
    >>> zmi_views = InterfaceClass('zmi_views', __module__='zope.app.menus')
    >>> menus.zmi_views = zmi_views
    >>> zmi_actions = InterfaceClass('zmi_actions', __module__='zope.app.menus')
    >>> menus.zmi_actions = zmi_actions

    >>> context = Context()
    >>> containerViews(context, for_=I, contents='zope.ManageContent',
    ...                add='zope.ManageContent', index='zope.View')
    >>> context
    ((('adapter',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.app.menus.zmi_views>,
       u'Contents'),
      <function handler>,
      ('registerAdapter',
       <zope.app.publisher.browser.menumeta.MenuItemFactory object>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.app.menus.zmi_views>,
       u'Contents',
       '')),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.app.menus.zmi_views>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>,
       'contents.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.Contents'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.interface.Interface>,
       'contents.html',
       'info')),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>,
       'index.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.Contents'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.interface.Interface>,
       'index.html',
       'info')),
     (('adapter',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.app.menus.zmi_actions>,
       u'Add'),
      <function handler>,
      ('registerAdapter',
       <zope.app.publisher.browser.menumeta.MenuItemFactory object>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.app.menus.zmi_actions>,
       u'Add',
       'info')),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.app.menus.zmi_actions>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.interface.Interface>)),
     (('view',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       '+',
       <InterfaceClass zope.interface.Interface>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.+'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.interface.Interface>,
       '+',
       'info')))
    """

def test_containerViews_layer():
    """
    >>> from zope.app.publisher.browser.menumeta import menus
    >>> from zope.interface.interface import InterfaceClass
    >>> zmi_views = InterfaceClass('zmi_views', __module__='zope.app.menus')
    >>> menus.zmi_views = zmi_views
    >>> zmi_actions = InterfaceClass('zmi_actions', __module__='zope.app.menus')
    >>> menus.zmi_actions = zmi_actions

    >>> context = Context()
    >>> containerViews(context, for_=I, contents='zope.ManageContent',
    ...                add='zope.ManageContent', index='zope.View', layer=ITestLayer)
    >>> context
    ((('adapter',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.app.menus.zmi_views>,
       u'Contents'),
      <function handler>,
      ('registerAdapter',
       <zope.app.publisher.browser.menumeta.MenuItemFactory object>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.app.menus.zmi_views>,
       u'Contents',
       '')),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.app.menus.zmi_views>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>,
       'contents.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.Contents'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.interface.Interface>,
       'contents.html',
       'info')),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>,
       'index.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.Contents'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.interface.Interface>,
       'index.html',
       'info')),
     (('adapter',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.app.menus.zmi_actions>,
       u'Add'),
      <function handler>,
      ('registerAdapter',
       <zope.app.publisher.browser.menumeta.MenuItemFactory object>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.app.menus.zmi_actions>,
       u'Add',
       'info')),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.app.menus.zmi_actions>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>)),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.app.container.browser.tests.test_directive.I>)),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.interface.Interface>)),
     (('view',
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       '+',
       <InterfaceClass zope.interface.Interface>),
      <function handler>,
      ('registerAdapter',
       <class 'zope.app.publisher.browser.viewmeta.+'>,
       (<InterfaceClass zope.app.container.browser.tests.test_directive.I>,
        <InterfaceClass zope.app.container.browser.tests.test_directive.ITestLayer>),
       <InterfaceClass zope.interface.Interface>,
       '+',
       'info')))
    """


def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main()

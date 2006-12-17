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
"""Adding implementation tests

$Id: test_adding.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest

import zope.interface
import zope.security.checker
from zope.component.interfaces import IFactory
from zope.component.interfaces import ComponentLookupError
from zope.interface import implements, Interface, directlyProvides
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import BrowserView
from zope.security.interfaces import ForbiddenAttribute
from zope.testing.doctestunit import DocTestSuite
from zope.exceptions.interfaces import UserError
from zope.traversing.browser import AbsoluteURL
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.traversing.interfaces import IContainmentRoot

from zope.app import zapi
from zope.app.testing import ztapi
from zope.app.testing.placelesssetup import PlacelessSetup, setUp, tearDown
from zope.app.publisher.interfaces.browser import AddMenu
from zope.app.publisher.interfaces.browser import IMenuItemType, IBrowserMenu
from zope.app.publisher.browser.menu import BrowserMenuItem, BrowserMenu
from zope.app.container.interfaces import IAdding
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.interfaces import IContainerNamesContainer
from zope.app.container.interfaces import INameChooser
from zope.app.container.interfaces import IContainer
from zope.app.container.contained import contained
from zope.app.container.browser.adding import Adding
from zope.app.container.sample import SampleContainer


class Root(object):
    implements(IContainmentRoot)

class Container(SampleContainer):
    pass

class CreationView(BrowserView):

    def action(self):
        return 'been there, done that'


class Content(object):
    pass

class Factory(object):

    implements(IFactory)

    title = ''
    description = ''

    def getInterfaces(self):
        return ()

    def __call__(self):
        return Content()


class AbsoluteURL(BrowserView):

    def __str__(self):
        if IContainmentRoot.providedBy(self.context):
            return ''
        name = self.context.__name__
        url = zapi.absoluteURL(zapi.getParent(self.context), self.request)
        url += '/' + name
        return url

    __call__ = __str__

def defineMenuItem(menuItemType, for_, action, title=u'', extra=None):
    newclass = type(title, (BrowserMenuItem,),
                    {'title':title, 'action':action,
                     '_for': for_, 'extra':extra})
    zope.interface.classImplements(newclass, menuItemType)
    ztapi.provideAdapter((for_, IBrowserRequest), menuItemType, newclass, title)

def registerAddMenu():
  ztapi.provideUtility(IMenuItemType, AddMenu, 'zope.app.container.add')
  ztapi.provideUtility(IBrowserMenu,
                       BrowserMenu('zope.app.container.add', u'', u''),
                       'zope.app.container.add')


class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()

    def test(self):
        container = Container()
        request = TestRequest()
        adding = Adding(container, request)
        ztapi.browserView(IAdding, "Thing", CreationView)
        self.assertEqual(adding.contentName, None)
        view = adding.publishTraverse(request, 'Thing=foo')
        self.assertEqual(view.action(), 'been there, done that')
        self.assertEqual(adding.contentName, 'foo')

        o = object()
        result = adding.add(o)

        # Check the state of the container and result
        self.assertEqual(container["foo"], o)
        self.assertEqual(result, o)

    def testNoNameGiven(self):
        container = Container()
        request = TestRequest()
        adding = Adding(container, request)
        ztapi.browserView(IAdding, "Thing", CreationView)

        self.assertEqual(adding.contentName, None)
        view = adding.publishTraverse(request, 'Thing=')
        self.assertEqual(adding.contentName, '')

    def testAction(self):
        # make a private factory
        ztapi.provideUtility(IFactory, Factory(), 'fooprivate')

        factory = Factory()
        factory.__Security_checker__ = zope.security.checker.NamesChecker(
            ['__call__'])
        ztapi.provideUtility(IFactory, factory, 'foo')

        container = Container()
        adding = Adding(container, TestRequest())
        adding.nextURL = lambda: '.'
        adding.nameAllowed = lambda: True

        # we can't use a private factory:
        self.assertRaises(ForbiddenAttribute,
                          adding.action, type_name='fooprivate', id='bar')

        # typical add - id is provided by user
        adding.action(type_name='foo', id='bar')
        self.assert_('bar' in container)

        # missing type_name
        self.assertRaises(UserError, adding.action, id='bar')

        # missing id
        self.assertRaises(UserError, adding.action, type_name='foo')

        # bad type_name
        self.assertRaises(ComponentLookupError, adding.action,
            type_name='***', id='bar')

        # alternative add - id is provided internally instead of from user
        adding.nameAllowed = lambda: False
        adding.contentName = 'baz'
        adding.action(type_name='foo')
        self.assert_('baz' in container)

        # alternative add w/missing contentName
        # Note: Passing is None as object name might be okay, if the container
        #       is able to hand out ids itself. Let's not require a content
        #       name to be specified!
        # For the container, (or really, the chooser, to choose, we have to
        # marke the container as a ContainerNamesContainer
        directlyProvides(container, IContainerNamesContainer)
        adding.contentName = None
        adding.action(type_name='foo')
        self.assert_('Content' in container)


    def test_action(self):
        container = Container()
        container = contained(container, Root(), "container")
        request = TestRequest()
        adding = Adding(container, request)
        adding.__name__ = '+'
        ztapi.browserView(IAdding, "Thing", CreationView)
        ztapi.browserView(Interface, "absolute_url", AbsoluteURL)
        ztapi.browserView(None, '', AbsoluteURL, providing=IAbsoluteURL)
        self.assertRaises(UserError, adding.action, '', 'foo')
        adding.action('Thing', 'foo')
        self.assertEqual(adding.request.response.getHeader('location'),
                         '/container/+/Thing=foo')
        adding.action('Thing/screen1', 'foo')
        self.assertEqual(adding.request.response.getHeader('location'),
                         '/container/+/Thing/screen1=foo')

    def test_publishTraverse_factory(self):
        factory = Factory()
        ztapi.provideUtility(IFactory, factory, 'foo')
        container = Container()
        request = TestRequest()
        adding = Adding(container, request)
        self.assert_(adding.publishTraverse(request, 'foo') is factory)


def test_constraint_driven_addingInfo():
    """
    >>> setUp()
    >>> registerAddMenu()

    >>> class TestMenu(zope.interface.Interface):
    ...     pass
    >>> zope.interface.directlyProvides(TestMenu, IMenuItemType)

    >>> ztapi.provideUtility(IMenuItemType, TestMenu, 'TestMenu')
    >>> ztapi.provideUtility(IBrowserMenu, BrowserMenu('TestMenu', u'', u''),
    ...                      'TestMenu')

    >>> defineMenuItem(TestMenu, IAdding, '', 'item1')
    >>> defineMenuItem(TestMenu, IAdding, '', 'item2')

    >>> defineMenuItem(AddMenu, IAdding, '', 'item3', extra={'factory': 'f1'})
    >>> defineMenuItem(AddMenu, IAdding, '', 'item4', extra={'factory': 'f2'})

    >>> class F1(object):
    ...     pass

    >>> class F2(object):
    ...     pass

    >>> def pre(container, name, object):
    ...     if not isinstance(object, F1):
    ...         raise zope.interface.Invalid()
    >>> def prefactory(container, name, factory):
    ...     if factory._callable is not F1:
    ...         raise zope.interface.Invalid()
    >>> pre.factory = prefactory


    >>> class IContainer(zope.interface.Interface):
    ...     def __setitem__(name, object):
    ...         pass
    ...     __setitem__.precondition = pre


    >>> class Container(object):
    ...     zope.interface.implements(IContainer)

    >>> from zope.component.factory import Factory
    >>> ztapi.provideUtility(IFactory, Factory(F1), 'f1')
    >>> ztapi.provideUtility(IFactory, Factory(F2), 'f2')

    >>> from zope.app.container.browser.adding import Adding
    >>> adding = Adding(Container(), TestRequest())
    >>> items = adding.addingInfo()
    >>> len(items)
    1
    >>> items[0]['title']
    'item3'
    
    >>> adding.menu_id = 'TestMenu'
    >>> items = adding.addingInfo()
    >>> len(items)
    3
    >>> items[0]['title']
    'item1'
    >>> items[1]['title']
    'item2'
    >>> items[2]['title']
    'item3'
    >>> tearDown()    
    """

def test_constraint_driven_add():
    """
    >>> setUp()
    >>> from zope.app.container.sample import SampleContainer
    >>> from zope.app.container.browser.adding import Adding

    >>> class F1(object):
    ...     pass

    >>> class F2(object):
    ...     pass

    >>> def pre(container, name, object):
    ...     "a mock item constraint "
    ...     if not isinstance(object, F1):
    ...         raise zope.interface.Invalid('not a valid child')
    
    >>> class ITestContainer(zope.interface.Interface):
    ...     def __setitem__(name, object):
    ...         pass
    ...     __setitem__.precondition = pre

    >>> class Container(SampleContainer):
    ...     zope.interface.implements(ITestContainer)

    >>> adding = Adding(Container(), TestRequest())
    >>> c = adding.add(F1())
    
    This test should fail, because the container only
    accepts instances of F1

    >>> adding.add(F2())
    Traceback (most recent call last):
    ...
    Invalid: not a valid child

    >>> class ValidContainer(SampleContainer):
    ...     zope.interface.implements(ITestContainer)

    >>> def constr(container):
    ...     "a mock container constraint"
    ...     if not isinstance(container, ValidContainer):
    ...         raise zope.interface.Invalid('not a valid container')
    ...     return True

    >>> class I2(zope.interface.Interface):
    ...     __parent__ = zope.schema.Field(constraint = constr)

    >>> zope.interface.classImplements(F1, I2)

    This adding now fails, because the Container is not a valid
    parent for F1

    >>> c = adding.add(F1())
    Traceback (most recent call last):
    ...
    Invalid: not a valid container

    >>> adding = Adding(ValidContainer(), TestRequest())
    >>> c = adding.add(F1())

    >>> tearDown()
    """


def test_nameAllowed():
    """
    Test for nameAllowed in adding.py

    >>> setUp()
    >>> from zope.app.container.browser.adding import Adding
    >>> from zope.app.container.interfaces import IContainerNamesContainer

    Class implements IContainerNamesContainer

    >>> class FakeContainer(object):
    ...    zope.interface.implements(IContainerNamesContainer)

    nameAllowed returns False if the class imlements
    IContainerNamesContainer

    >>> adding = Adding(FakeContainer(),TestRequest())
    >>> adding.nameAllowed()
    False

    Fake class without IContainerNamesContainer

    >>> class Fake(object):
    ...    pass

    nameAllowed returns True if the class
    doesn't imlement IContainerNamesContainer

    >>> adding = Adding(Fake(),TestRequest())
    >>> adding.nameAllowed()
    True

    """



def test_chooseName():
    """If user don't enter name, pick one

    >>> class MyContainer(object):
    ...    args = {}
    ...    zope.interface.implements(INameChooser, IContainer)
    ...    def chooseName(self, name, object):
    ...        self.args["choose"] = name, object
    ...        return 'pickone'
    ...    def checkName(self, name, object):
    ...        self.args["check"] = name, object
    ...    def __setitem__(self, name, object):
    ...        setattr(self, name, object)
    ...        self.name = name
    ...    def __getitem__(self, key):
    ...        return getattr(self, key)

    >>> request = TestRequest()
    >>> mycontainer = MyContainer()
    >>> adding = Adding(mycontainer, request)
    >>> o = object()
    >>> add_obj = adding.add(o)
    >>> mycontainer.name
    'pickone'
    >>> add_obj is o
    True

    Make sure right arguments passed to INameChooser adapter:

    >>> name, obj = mycontainer.args["choose"]
    >>> name
    ''
    >>> obj is o
    True
    >>> name, obj = mycontainer.args["check"]
    >>> name
    'pickone'
    >>> obj is o
    True
    """



def test_SingleMenuItem_and_CustomAddView_NonICNC():
    """
    This tests the condition if the content has Custom Add views and
    the container contains only a single content object

    >>> setUp()
    >>> registerAddMenu()
    >>> defineMenuItem(AddMenu, IAdding, '', 'item3', extra={'factory': 'f1'})

    >>> class F1(object):
    ...     pass

    >>> class F2(object):
    ...     pass

    >>> def pre(container, name, object):
    ...     if not isinstance(object, F1):
    ...         raise zope.interface.Invalid()
    >>> def prefactory(container, name, factory):
    ...     if factory._callable is not F1:
    ...         raise zope.interface.Invalid()
    >>> pre.factory = prefactory


    >>> class IContainer(zope.interface.Interface):
    ...     def __setitem__(name, object):
    ...         pass
    ...     __setitem__.precondition = pre


    >>> class Container(object):
    ...     zope.interface.implements(IContainer)

    >>> from zope.component.factory import Factory
    >>> ztapi.provideUtility(IFactory, Factory(F1), 'f1')
    >>> ztapi.provideUtility(IFactory, Factory(F2), 'f2')

    >>> from zope.app.container.browser.adding import Adding
    >>> adding = Adding(Container(), TestRequest())
    >>> items = adding.addingInfo()
    >>> len(items)
    1

    isSingleMenuItem returns True if there is only one content class
    inside the Container

    >>> adding.isSingleMenuItem()
    True

    hasCustomAddView will return False as the content does not have
    a custom Add View

    >>> adding.hasCustomAddView()
    True
    
    >>> tearDown()    
    """

def test_SingleMenuItem_and_NoCustomAddView_NonICNC():
    """

    This function checks the case where there is a single content object
    and there is non custom add view . Also the container does not
    implement IContainerNamesContainer

    >>> setUp()
    >>> registerAddMenu()
    >>> defineMenuItem(AddMenu, None, '', 'item3', extra={'factory': ''})
    >>> class F1(object):
    ...     pass

    >>> class F2(object):
    ...     pass

    >>> def pre(container, name, object):
    ...     if not isinstance(object, F1):
    ...         raise zope.interface.Invalid()
    >>> def prefactory(container, name, factory):
    ...     if factory._callable is not F1:
    ...         raise zope.interface.Invalid()
    >>> pre.factory = prefactory


    >>> class IContainer(zope.interface.Interface):
    ...     def __setitem__(name, object):
    ...         pass
    ...     __setitem__.precondition = pre


    >>> class Container(object):
    ...     zope.interface.implements(IContainer)

    >>> from zope.component.factory import Factory
    >>> ztapi.provideUtility(IFactory, Factory(F1), 'f1')
    >>> ztapi.provideUtility(IFactory, Factory(F2), 'f2')
    
    >>> from zope.app.container.browser.adding import Adding
    >>> adding = Adding(Container(), TestRequest())
    >>> items = adding.addingInfo()
    >>> len(items)
    1

    The isSingleMenuItem will return True if there is one single content
    that can be added inside the Container

    >>> adding.isSingleMenuItem()
    True

    hasCustomAddView will return False as the content does not have
    a custom Add View

    >>> adding.hasCustomAddView()
    False
    
    >>> tearDown()
    """

def test_isSingleMenuItem_with_ICNC():
    """
    This test checks for whether there is a single content that can be added
    and the container uses IContainerNamesContaienr

    >>> setUp()
    >>> registerAddMenu()
    >>> defineMenuItem(AddMenu, None, '', 'item3', extra={'factory': ''})
    
    >>> class F1(object):
    ...     pass

    >>> class F2(object):
    ...     pass

    >>> def pre(container, name, object):
    ...     if not isinstance(object, F1):
    ...         raise zope.interface.Invalid()
    >>> def prefactory(container, name, factory):
    ...     if factory._callable is not F1:
    ...         raise zope.interface.Invalid()
    >>> pre.factory = prefactory


    >>> class IContainer(zope.interface.Interface):
    ...     def __setitem__(name, object):
    ...         pass
    ...     __setitem__.precondition = pre


    >>> class Container(object):
    ...     zope.interface.implements(IContainer, IContainerNamesContainer)

    >>> from zope.app.container.browser.adding import Adding
    >>> adding = Adding(Container(), TestRequest())
    >>> items = adding.addingInfo()
    >>> len(items)
    1
    >>> adding.isSingleMenuItem()
    True
    >>> adding.hasCustomAddView()
    False
    
    >>> tearDown()
    
    """

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        DocTestSuite(),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

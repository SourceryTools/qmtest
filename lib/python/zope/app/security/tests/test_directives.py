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
"""Directives Tests

$Id: test_directives.py 67630 2006-04-27 00:54:03Z jim $
"""
import unittest
from pprint import PrettyPrinter

import zope.security.zcml
from zope.interface import Interface, Attribute
from zope.testing import doctest
from zope.component import provideUtility
from zope.component.testing import setUp, tearDown, PlacelessSetup
from zope.configuration import xmlconfig
from zope.security.checker import moduleChecker
from zope.security.permission import Permission
from zope.security.interfaces import IPermission

from zope.app.security import metaconfigure

def pprint(ob, width=70):
    PrettyPrinter(width=width).pprint(ob)

class I1(Interface):
    def x(): pass
    y = Attribute("Y")

class I2(I1):
    def a(): pass
    b = Attribute("B")

test_perm = 'zope.app.security.metaconfigure.test'
test_bad_perm = 'zope.app.security.metaconfigure.bad'

def test_protectModule():
    """
    >>> from zope.app.security.tests import test_directives

    Initially, there's no checker defined for the module:

    >>> moduleChecker(test_directives)
        
    >>> perm = Permission(test_perm, '')
    >>> provideUtility(perm, IPermission, test_perm)
    >>> metaconfigure.protectModule(test_directives, 'foo', test_perm)

    Now, the checker should exist and have an access dictionary with the
    name and permission:

    >>> checker = moduleChecker(test_directives)
    >>> cdict = checker.get_permissions
    >>> pprint(cdict)
    {'foo': 'zope.app.security.metaconfigure.test'}
    
    If we define additional names, they will be added to the dict:

    >>> metaconfigure.protectModule(test_directives, 'bar', test_perm)
    >>> metaconfigure.protectModule(test_directives, 'baz', test_perm)
    >>> pprint(cdict)
    {'bar': 'zope.app.security.metaconfigure.test',
     'baz': 'zope.app.security.metaconfigure.test',
     'foo': 'zope.app.security.metaconfigure.test'}
        
    """

def test_allow():
    """

    The allow directive creates actions for each named defined
    directly, or via interface:

    >>> class Context(object):
    ...     def __init__(self):
    ...         self.actions = []
    ...
    ...     def action(self, discriminator, callable, args):
    ...         self.actions.append(
    ...             {'discriminator': discriminator,
    ...              'callable': int(callable is metaconfigure.protectModule),
    ...              'args': args})
    ...
    ...     module='testmodule'

    >>> context = Context()
    >>> metaconfigure.allow(context, attributes=['foo', 'bar'],
    ...                     interface=[I1, I2])

    >>> context.actions.sort(
    ...    lambda a, b: cmp(a['discriminator'], b['discriminator']))
    >>> pprint(context.actions)
    [{'args': ('testmodule', 'a', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'a')},
     {'args': ('testmodule', 'b', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'b')},
     {'args': ('testmodule', 'bar', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'bar')},
     {'args': ('testmodule', 'foo', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'foo')},
     {'args': ('testmodule', 'x', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'x')},
     {'args': ('testmodule', 'y', 'zope.Public'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'y')}]

    """

def test_require():
    """

    The allow directive creates actions for each named defined
    directly, or via interface:

    >>> class Context(object):
    ...     def __init__(self):
    ...         self.actions = []
    ...
    ...     def action(self, discriminator, callable, args):
    ...         self.actions.append(
    ...             {'discriminator': discriminator,
    ...              'callable': int(callable is metaconfigure.protectModule),
    ...              'args': args})
    ...
    ...     module='testmodule'

    >>> context = Context()
    >>> metaconfigure.require(context, attributes=['foo', 'bar'],
    ...                       interface=[I1, I2], permission='p')

    >>> context.actions.sort(
    ...    lambda a, b: cmp(a['discriminator'], b['discriminator']))
    >>> pprint(context.actions)
    [{'args': ('testmodule', 'a', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'a')},
     {'args': ('testmodule', 'b', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'b')},
     {'args': ('testmodule', 'bar', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'bar')},
     {'args': ('testmodule', 'foo', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'foo')},
     {'args': ('testmodule', 'x', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'x')},
     {'args': ('testmodule', 'y', 'p'),
      'callable': 1,
      'discriminator': ('http://namespaces.zope.org/zope:module',
                        'testmodule',
                        'y')}]
    
    """

class IDummy(Interface):

    perm = zope.security.zcml.Permission(title=u'')

perms = []

def dummy(context_, perm):
    global perms
    perms.append(perm)


class DirectivesTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(DirectivesTest, self).setUp()
        from zope.app.security import tests
        
        self.context = xmlconfig.file("redefineperms.zcml", tests)

    def tearDown(self):
        global perms
        perms.remove('zope.Security')

    def testRedefinePermission(self):
        self.assertEqual(perms, ['zope.Security'])

def setUpAuth(test=None):
    setUp(test)
    from zope.app.authentication.placelesssetup import PlacelessSetup
    PlacelessSetup().setUp()

def zcml(s):
    context = xmlconfig.file('meta.zcml', package=zope.app.security)
    xmlconfig.string(s, context)

def reset():
    tearDown()
    setUpAuth()

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(setUp=setUp, tearDown=tearDown),
        doctest.DocTestSuite('zope.security.zcml'),
        unittest.makeSuite(DirectivesTest),
        doctest.DocFileSuite(
            '../globalprincipals.txt',
            globs={'zcml': zcml, 'reset': reset},
            setUp=setUpAuth, tearDown=tearDown,
            )
        ))

if __name__ == '__main__': unittest.main()

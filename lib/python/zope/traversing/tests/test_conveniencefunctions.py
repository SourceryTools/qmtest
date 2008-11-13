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
"""Test traversal convenience functions.

$Id: test_conveniencefunctions.py 66547 2006-04-05 15:01:06Z philikon $
"""
from unittest import TestCase, main, makeSuite

import zope.component
from zope.interface import directlyProvides
from zope.location.traversing import LocationPhysicallyLocatable
from zope.security.proxy import Proxy
from zope.security.checker import selectChecker
from zope.traversing.adapters import Traverser, DefaultTraversable
from zope.traversing.adapters import RootPhysicallyLocatable
from zope.traversing.interfaces import ITraverser, ITraversable
from zope.traversing.interfaces import IContainmentRoot, TraversalError
from zope.traversing.interfaces import IPhysicallyLocatable

from zope.app.component.testing import PlacefulSetup
from zope.app.container.contained import contained

class C(object):
    __parent__ = None
    __name__ = None
    def __init__(self, name):
        self.name = name

def _proxied(*args):
    return Proxy(args, selectChecker(args))


class Test(PlacefulSetup, TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)
        # Build up a wrapper chain
        root = C('root')
        directlyProvides(root, IContainmentRoot)
        folder = C('folder')
        item = C('item')

        self.root = root  # root is not usually wrapped
        self.folder = contained(folder, self.root,   name='folder')
        self.item =   contained(item,   self.folder, name='item')
        self.unwrapped_item = item
        self.broken_chain_folder = contained(folder, None)
        self.broken_chain_item = contained(item,
                                    self.broken_chain_folder,
                                    name='item'
                                    )
        root.folder = folder
        folder.item = item

        self.tr = Traverser(root)
        zope.component.provideAdapter(Traverser, (None,), ITraverser)
        zope.component.provideAdapter(DefaultTraversable, (None,), ITraversable)
        zope.component.provideAdapter(LocationPhysicallyLocatable, (None,),
                                      IPhysicallyLocatable)
        zope.component.provideAdapter(RootPhysicallyLocatable,
                                      (IContainmentRoot,), IPhysicallyLocatable)

    def testTraverse(self):
        from zope.traversing.api import traverse
        self.assertEqual(
            traverse(self.item, '/folder/item'),
            self.tr.traverse('/folder/item')
            )

    def testTraverseFromUnwrapped(self):
        from zope.traversing.api import traverse
        self.assertRaises(
            TypeError,
            traverse,
            self.unwrapped_item, '/folder/item'
            )

    def testTraverseName(self):
        from zope.traversing.api import traverseName
        self.assertEqual(
            traverseName(self.folder, 'item'),
            self.tr.traverse('/folder/item')
            )
        self.assertEqual(
            traverseName(self.item, '.'),
            self.tr.traverse('/folder/item')
            )
        self.assertEqual(
            traverseName(self.item, '..'),
            self.tr.traverse('/folder')
            )

        # TODO test that ++names++ and @@names work too

    def testTraverseNameBadValue(self):
        from zope.traversing.api import traverseName
        self.assertRaises(
            TraversalError,
            traverseName,
            self.folder, '../root'
            )
        self.assertRaises(
            TraversalError,
            traverseName,
            self.folder, '/root'
            )
        self.assertRaises(
            TraversalError,
            traverseName,
            self.folder, './item'
            )

    def testGetName(self):
        from zope.traversing.api import getName
        self.assertEqual(
            getName(self.item),
            'item'
            )

    def testGetParent(self):
        from zope.traversing.api import getParent
        self.assertEqual(
            getParent(self.item),
            self.folder
            )

    def testGetParentFromRoot(self):
        from zope.traversing.api import getParent
        self.assertEqual(
            getParent(self.root),
            None
            )

    def testGetParentBrokenChain(self):
        from zope.traversing.api import getParent
        self.assertRaises(
            TypeError,
            getParent,
            self.broken_chain_folder
            )

    def testGetParentFromUnwrapped(self):
        from zope.traversing.api import getParent
        self.assertRaises(
            TypeError,
            getParent,
            self.unwrapped_item
            )

    def testGetParents(self):
        from zope.traversing.api import getParents
        self.assertEqual(
            getParents(self.item),
            [self.folder, self.root]
            )

    def testGetParentsBrokenChain(self):
        from zope.traversing.api import getParents
        self.assertRaises(
            TypeError,
            getParents,
            self.broken_chain_item
            )

    def testGetParentFromUnwrapped(self):
        from zope.traversing.api import getParent
        self.assertRaises(
            TypeError,
            getParent,
            self.unwrapped_item
            )

    def testGetPath(self):
        from zope.traversing.api import getPath
        self.assertEqual(
            getPath(self.item),
            u'/folder/item'
            )

    def testGetPathOfRoot(self):
        from zope.traversing.api import getPath
        self.assertEqual(
            getPath(self.root),
            u'/',
            )

    def testGetNameOfRoot(self):
        from zope.traversing.api import getName
        self.assertEqual(
            getName(self.root),
            u'',
            )

    def testGetRoot(self):
        from zope.traversing.api import getRoot
        self.assertEqual(
            getRoot(self.item),
            self.root
            )

    def testCanonicalPath(self):

        _bad_locations = (
            (ValueError, '\xa323'),
            (ValueError, ''),
            (ValueError, '//'),
            (ValueError, '/foo//bar'),

            # regarding the next two errors:
            # having a trailing slash on a location is undefined.
            # we might want to give it a particular meaning for zope3 later
            # for now, it is an invalid location identifier
            (ValueError, '/foo/bar/'),
            (ValueError, 'foo/bar/'),

            (IndexError, '/a/../..'),
            (ValueError, '/a//v'),
            )

        # sequence of N-tuples:
        #   (loc_returned_as_string, input, input, ...)
        # The string and tuple are tested as input as well as being the
        # specification for output.

        _good_locations = (
            # location returned as string
            ( u'/xx/yy/zz',
                # arguments to try in addition to the above
                '/xx/yy/zz',
                '/xx/./yy/ww/../zz',
            ),
            ( u'/xx/yy/zz',
                '/xx/yy/zz',
            ),
            ( u'/xx',
                '/xx',
            ),
            ( u'/',
                '/',
            ),
        )

        from zope.traversing.api import canonicalPath

        for error_type, value in _bad_locations:
            self.assertRaises(error_type, canonicalPath, value)

        for spec in _good_locations:
            correct_answer = spec[0]
            for argument in spec:
                self.assertEqual(canonicalPath(argument), correct_answer,
                                 "failure on %s" % argument)


    def test_normalizePath(self):

        _bad_locations = (
            (ValueError, '//'),
            (ValueError, '/foo//bar'),
            (IndexError, '/a/../..'),
            (IndexError, '/a/./../..'),
            )

        # sequence of N-tuples:
        #   (loc_returned_as_string, input, input, ...)
        # The string and tuple are tested as input as well as being the
        # specification for output.

        _good_locations = (
            # location returned as string
            ( '/xx/yy/zz',
              # arguments to try in addition to the above
              '/xx/yy/zz',
              '/xx/./yy/ww/../zz',
              '/xx/./yy/ww/./../zz',
            ),
            ( 'xx/yy/zz',
              # arguments to try in addition to the above
              'xx/yy/zz',
              'xx/./yy/ww/../zz',
              'xx/./yy/ww/./../zz',
            ),
            ( '/xx/yy/zz',
              '/xx/yy/zz',
            ),
            ( '/xx',
              '/xx',
            ),
            ( '/',
              '/',
            ),
        )


        from zope.traversing.api import _normalizePath

        for error_type, value in _bad_locations:
            self.assertRaises(error_type, _normalizePath, value)

        for spec in _good_locations:
            correct_answer = spec[0]
            for argument in spec:
                self.assertEqual(_normalizePath(argument), correct_answer,
                                 "failure on %s" % argument)

    def test_joinPath_slashes(self):
        from zope.traversing.api import joinPath
        path = u'/'
        args = ('/test', 'bla', '/foo', 'bar')
        self.assertRaises(ValueError, joinPath, path, *args)

        args = ('/test', 'bla', 'foo/', '/bar')
        self.assertRaises(ValueError, joinPath, path, *args)

    def test_joinPath(self):
        from zope.traversing.api import joinPath
        path = u'/bla'
        args = ('foo', 'bar', 'baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'/bla/foo/bar/baz/bone')

        path = u'bla'
        args = ('foo', 'bar', 'baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'bla/foo/bar/baz/bone')

        path = u'bla'
        args = ('foo', 'bar/baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'bla/foo/bar/baz/bone')

        path = u'bla/'
        args = ('foo', 'bar', 'baz', 'bone')
        self.assertRaises(ValueError, joinPath, path, *args)

    def test_joinPath_normalize(self):
        from zope.traversing.api import joinPath
        path = u'/bla'
        args = ('foo', 'bar', '..', 'baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'/bla/foo/baz/bone')

        path = u'bla'
        args = ('foo', 'bar', '.', 'baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'bla/foo/bar/baz/bone')

        path = u'/'
        args = ('foo', 'bar', '.', 'baz', 'bone')
        self.assertEqual(joinPath(path, *args), u'/foo/bar/baz/bone')


def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')

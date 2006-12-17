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
"""Object Mover Tests

$Id: test_objectmover.py 67630 2006-04-27 00:54:03Z jim $
"""
from unittest import TestCase, TestSuite, main, makeSuite

import zope.component
from zope.testing import doctest
from zope.traversing.api import traverse
from zope.component.eventtesting import getEvents, clearEvents
from zope.copypastemove import ObjectMover
from zope.copypastemove.interfaces import IObjectMover

from zope.app.component.testing import PlacefulSetup
from zope.app.testing import setup
from zope.app.folder import Folder

class File(object):
    pass

def test_move_events():
    """
    Prepare the setup::

      >>> root = setup.placefulSetUp(site=True)
      >>> zope.component.provideAdapter(ObjectMover, (None,), IObjectMover)

    Prepare some objects::

      >>> folder = Folder()
      >>> root[u'foo'] = File()
      >>> root[u'folder'] = folder
      >>> list(folder.keys())
      []
      >>> foo = traverse(root, 'foo') # wrap in ContainedProxy

    Now move it::

      >>> clearEvents()
      >>> mover = IObjectMover(foo)
      >>> mover.moveableTo(folder)
      True
      >>> mover.moveTo(folder, u'bar')
      u'bar'

    Check that the move has been done::

      >>> list(root.keys())
      [u'folder']
      >>> list(folder.keys())
      [u'bar']

    Check what events have been sent::

      >>> events = getEvents()
      >>> [event.__class__.__name__ for event in events]
      ['ObjectMovedEvent', 'ContainerModifiedEvent', 'ContainerModifiedEvent']

    Verify that the ObjectMovedEvent includes the correct data::

      >>> events[0].oldName, events[0].newName
      (u'foo', u'bar')
      >>> events[0].oldParent is root
      True
      >>> events[0].newParent is folder
      True

    Let's look the other events:

      >>> events[1].object is folder
      True
      >>> events[2].object is root
      True

    Finally, tear down::

      >>> setup.placefulTearDown()
    """


class ObjectMoverTest(PlacefulSetup, TestCase):

    def setUp(self):
        PlacefulSetup.setUp(self)
        PlacefulSetup.buildFolders(self)
        zope.component.provideAdapter(ObjectMover, (None,), )
 
    def test_movetosame(self):
        # Should be a noop, because "moving" to same location
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        mover.moveTo(container, 'file1')
        self.failUnless('file1' in container)
        self.assertEquals(len(container), 3)

    def test_movetosamewithnewname(self):
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        mover.moveTo(container, 'file2')
        self.failIf('file1' in container)
        self.failUnless('file2' in container)

    def test_movetoother(self):
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        target = traverse(root, 'folder2')
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        mover.moveTo(target, 'file1')
        self.failIf('file1' in container)
        self.failUnless('file1' in target)

    def test_movetootherwithnewname(self):
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        target = traverse(root, 'folder2')
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        mover.moveTo(target, 'file2')
        self.failIf('file1' in container)
        self.failUnless('file2' in target)

    def test_movetootherwithnamecollision(self):
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        target = traverse(root, 'folder2')
        target['file1'] = File()
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        mover.moveTo(target, 'file1')
        self.failIf('file1' in container)
        self.failUnless('file1' in target)
        self.failUnless('file1-2' in target)

    def test_moveable(self):
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        self.failUnless(mover.moveable())

    def test_moveableTo(self):
        #  A file should be moveable to a folder that has an
        #  object with the same id.
        root = self.rootFolder
        container = traverse(root, 'folder1')
        container['file1'] = File()
        file = traverse(root, 'folder1/file1')
        mover = IObjectMover(file)
        self.failUnless(mover.moveableTo(container, 'file1'))

    def test_movefoldertosibling(self):
        root = self.rootFolder
        target = traverse(root, '/folder2')
        source = traverse(root, '/folder1/folder1_1')
        mover = IObjectMover(source)
        mover.moveTo(target)
        self.failUnless('folder1_1' in target)

    def test_movefoldertosame(self):
        # Should be a noop, because "moving" to same location
        root = self.rootFolder
        target = traverse(root, '/folder1')
        source = traverse(root, '/folder1/folder1_1')
        mover = IObjectMover(source)
        mover.moveTo(target)
        self.failUnless('folder1_1' in target)
        self.assertEquals(len(target), 2)

    def test_movefoldertosame2(self):
        # Should be a noop, because "moving" to same location
        root = self.rootFolder
        target = traverse(root, '/folder1/folder1_1')
        source = traverse(root, '/folder1/folder1_1/folder1_1_1')
        mover = IObjectMover(source)
        mover.moveTo(target)
        self.failUnless('folder1_1_1' in target)
        self.assertEquals(len(target), 2)

    def test_movefolderfromroot(self):
        root = self.rootFolder
        target = traverse(root, '/folder2')
        source = traverse(root, '/folder1')
        mover = IObjectMover(source)
        mover.moveTo(target)
        self.failUnless('folder1' in target)

    def test_movefolderfromroot2(self):
        root = self.rootFolder
        target = traverse(root, '/folder2/folder2_1/folder2_1_1')
        source = traverse(root, '/folder1')
        mover = IObjectMover(source)
        mover.moveTo(target)
        self.failUnless('folder1' in target)

        
def test_suite():
    return TestSuite((
        makeSuite(ObjectMoverTest),
        doctest.DocTestSuite(),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

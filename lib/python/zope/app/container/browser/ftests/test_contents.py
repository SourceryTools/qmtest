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
"""Functional tests for the Container's 'Contents' view

$Id: test_contents.py 67630 2006-04-27 00:54:03Z jim $
"""

import unittest

from persistent import Persistent
import transaction
from zope import copypastemove
from zope.interface import implements, Interface
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.dublincore.interfaces import IZopeDublinCore

from zope.app.container.interfaces import IReadContainer, IContained
from zope.app.testing import ztapi
from zope.app.testing.functional import BrowserTestCase
from zope.app.testing.functional import FunctionalDocFileSuite


class IImmovable(Interface):
    """Marker interface for immovable objects."""

class IUncopyable(Interface):
    """Marker interface for uncopyable objects."""

class File(Persistent):
    implements(IAttributeAnnotatable)

class ImmovableFile(File):
    implements(IImmovable)

class UncopyableFile(File):
    implements(IUncopyable)

class ObjectNonCopier(copypastemove.ObjectCopier):

    def copyable(self):
        return False

class ObjectNonMover(copypastemove.ObjectMover):

    def moveable(self):
        return False

class ReadOnlyContainer(Persistent):
    implements(IReadContainer, IContained)
    __parent__ = __name__ = None

    def __init__(self): self.data = {}
    def keys(self): return self.data.keys()
    def __getitem__(self, key): return self.data[key]
    def get(self, key, default=None): return self.data.get(key, default)
    def __iter__(self): return iter(self.data)
    def values(self): return self.data.values()
    def __len__(self): return len(self.data)
    def items(self): return self.data.items()
    def __contains__(self, key): return key in self.data
    def has_key(self, key): return self.data.has_key(key)


class Test(BrowserTestCase):

    def test_inplace_add(self):
        root = self.getRootFolder()
        self.assert_('foo' not in root)
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'type_name': u'zope.app.content.File'})
        body = ' '.join(response.getBody().split())
        self.assert_(body.find('type="hidden" name="type_name"') >= 0)
        self.assert_(body.find('input name="new_value"') >= 0)
        self.assert_(body.find('type="submit" name="container_cancel_button"')
                     >= 0)
        self.assert_(body.find('type="submit" name="container_rename_button"')
                     < 0)

        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'type_name': u'zope.app.content.File',
                                      'new_value': 'foo'})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')

        root._p_jar.sync()
        self.assert_('foo' in root)

    def test_inplace_rename_multiple(self):
        root = self.getRootFolder()
        root['foo'] = File()
        self.assert_('foo' in root)
        transaction.commit()

        # Check that we don't change mode if there are no items selected
        
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'container_rename_button': u''})
        body = ' '.join(response.getBody().split())
        self.assert_(body.find('input name="new_value:list"') < 0)
        self.assert_(body.find('type="submit" name="container_cancel_button"')
                     < 0)
        self.assert_(body.find('type="submit" name="container_rename_button"')
                     >= 0)
        self.assert_(body.find('div class="page_error"')
                     >= 0)


        # Check normal multiple select

        
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'container_rename_button': u'',
                                      'ids': ['foo']})
        body = ' '.join(response.getBody().split())
        self.assert_(body.find('input name="new_value:list"') >= 0)
        self.assert_(body.find('type="submit" name="container_cancel_button"')
                     >= 0)
        self.assert_(body.find('type="submit" name="container_rename_button"')
                     < 0)

        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'rename_ids': ['foo'],
                                      'new_value': ['bar']})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')

        root._p_jar.sync()
        self.assert_('foo' not in root)
        self.assert_('bar' in root)


    def test_inplace_rename_single(self):
        root = self.getRootFolder()
        root['foo'] = File()
        self.assert_('foo' in root)
        transaction.commit()
        
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'rename_ids': ['foo']})
        body = ' '.join(response.getBody().split())
        self.assert_(body.find('input name="new_value:list"') >= 0)
        self.assert_(body.find('type="submit" name="container_cancel_button"')
                     >= 0)
        self.assert_(body.find('type="submit" name="container_rename_button"')
                     < 0)

        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'rename_ids': ['foo'],
                                      'new_value': ['bar']})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')

        root._p_jar.sync()
        self.assert_('foo' not in root)
        self.assert_('bar' in root)

    def test_inplace_change_title(self):
        root = self.getRootFolder()
        root['foo'] = File()
        transaction.commit()
        self.assert_('foo' in root)
        dc = IZopeDublinCore(root['foo'])
        self.assert_(dc.title == '')

        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'retitle_id': u'foo'})
        body = ' '.join(response.getBody().split())
        self.assert_(body.find('type="hidden" name="retitle_id"') >= 0)
        self.assert_(body.find('input name="new_value"') >= 0)
        self.assert_(body.find('type="submit" name="container_cancel_button"')
                     >= 0)
        self.assert_(body.find('type="submit" name="container_rename_button"')
                     < 0)

        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'retitle_id': u'foo',
                                      'new_value': u'test title'})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')

        root._p_jar.sync()
        self.assert_('foo' in root)
        dc = IZopeDublinCore(root['foo'])
        self.assert_(dc.title == 'test title')


    def test_pasteable_for_deleted_clipboard_item(self):
        """Tests Paste button visibility when copied item is deleted."""

        root = self.getRootFolder()
        root['foo'] = File()    # item to be copied/deleted
        root['bar'] = File()    # ensures that there's always an item in
                                # the collection view
        transaction.commit()

        # confirm foo in contents, Copy button visible, Paste not visible
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<a href="foo/@@SelectedManagementView.html">foo</a>') != -1)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_copy_button"') != -1)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') == -1)

        # copy foo - confirm Paste visible
        response = self.publish('/@@contents.html', basic='mgr:mgrpw', form={
            'ids' : ('foo',),
            'container_copy_button' : '' })
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
            'http://localhost/@@contents.html')
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') != -1)

        # delete foo -> nothing valid to paste -> Paste should not be visible
        del root['foo']
        transaction.commit()
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') == -1)      


    def test_paste_for_deleted_clipboard_item(self):
        """Tests paste operation when one of two copied items is deleted."""

        root = self.getRootFolder()
        root['foo'] = File()
        root['bar'] = File()
        transaction.commit()

        # confirm foo/bar in contents, Copy button visible, Paste not visible
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<a href="foo/@@SelectedManagementView.html">foo</a>') != -1)
        self.assert_(response.getBody().find(
            '<a href="bar/@@SelectedManagementView.html">bar</a>') != -1)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_copy_button"') != -1)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') == -1)

        # copy foo and bar - confirm Paste visible
        response = self.publish('/@@contents.html', basic='mgr:mgrpw', form={
            'ids' : ('foo', 'bar'),
            'container_copy_button' : '' })
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
            'http://localhost/@@contents.html')
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') != -1)

        # delete only foo -> bar still available -> Paste should be visible
        del root['foo']
        transaction.commit()
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        self.assert_(response.getBody().find(
            '<input type="submit" name="container_paste_button"') != -1)

        # paste clipboard contents - only bar should be copied
        response = self.publish('/@@contents.html', basic='mgr:mgrpw', form={
            'container_paste_button' : '' })
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
            'http://localhost/@@contents.html')
        response = self.publish('/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)
        root._p_jar.sync()
        self.assertEqual(tuple(root.keys()), ('bar', 'bar-2'))

    def test_readonly_display(self):
        root = self.getRootFolder()
        root['foo'] = ReadOnlyContainer()
        transaction.commit()
        response = self.publish('/foo/@@contents.html', basic='mgr:mgrpw')
        self.assertEqual(response.getStatus(), 200)

    def test_uncopyable_object(self):
        ztapi.provideAdapter(IUncopyable,
                             copypastemove.interfaces.IObjectCopier,
                             ObjectNonCopier)
        root = self.getRootFolder()
        root['uncopyable'] = UncopyableFile()
        transaction.commit()
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'ids': [u'uncopyable'],
                                      'container_copy_button': u'Copy'})
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_("cannot be copied" in body)

    def test_unmoveable_object(self):
        ztapi.provideAdapter(IImmovable,
                             copypastemove.interfaces.IObjectMover,
                             ObjectNonMover)
        root = self.getRootFolder()
        root['immovable'] = ImmovableFile()
        transaction.commit()
        response = self.publish('/@@contents.html',
                                basic='mgr:mgrpw',
                                form={'ids': [u'immovable'],
                                      'container_cut_button': u'Cut'})
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        self.assert_("cannot be moved" in body)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    suite.addTest(FunctionalDocFileSuite("index.txt"))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

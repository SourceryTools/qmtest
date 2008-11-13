##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test browser pages

$Id: test_pages.py 75880 2007-05-22 14:58:12Z tseaver $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_ViewAcquisitionWrapping():
    """
      >>> import Products.Five.browser.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)

      >>> from Products.Five.tests.testing import simplecontent as sc
      >>> sc.manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

      >>> view = self.folder.unrestrictedTraverse('testoid/eagle.txt')
      >>> view is not None
      True
      >>> from Products.Five.browser.tests.pages import SimpleView
      >>> isinstance(view, SimpleView)
      True
      >>> view()
      u'The eagle has landed'

    This sucks, but we know it

      >>> from Acquisition import aq_parent, aq_base
      >>> aq_parent(view.context) is view
      True

    This is the right way to get the context parent

      >>> view.context.aq_inner.aq_parent is not view
      True
      >>> view.context.aq_inner.aq_parent is self.folder
      True

    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_view_with_unwrapped_context():
    """
    It may be desirable when writing tests for views themselves to
    provide dummy contexts which are not wrapped.

    >>> import Products.Five.browser.tests
    >>> from Products.Five import zcml
    >>> zcml.load_config("configure.zcml", Products.Five)
    >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)
    >>> from Products.Five.tests.testing import simplecontent as sc
    >>> from zope.interface import Interface
    >>> from zope.interface import implements
    >>> from zope.component import queryMultiAdapter
    >>> class Unwrapped:
    ...     implements(sc.ISimpleContent)
    >>> unwrapped = Unwrapped()

    Simple views should work fine without having their contexts wrapped:

    >>> eagle = queryMultiAdapter((unwrapped, self.app.REQUEST),
    ...                            Interface, 'eagle.txt')
    >>> eagle is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(eagle, SimpleView)
    True
    >>> eagle()
    u'The eagle has landed'

    We also want to be able to render the file-based ZPT without requiring
    that the context be wrapped:

    >>> falcon = queryMultiAdapter((unwrapped, self.app.REQUEST),
    ...                            Interface, 'falcon.html')
    >>> falcon is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(falcon, SimpleView)
    True
    >>> print falcon()
    <p>The falcon has taken flight</p>

    Clean up:

    >>> from zope.app.testing.placelesssetup import tearDown
    >>> tearDown()
    """

def test_suite():
    import unittest
    from Testing.ZopeTestCase import installProduct, ZopeDocTestSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    installProduct('PythonScripts')  # for Five.tests.testing.restricted
    return unittest.TestSuite((
        ZopeDocTestSuite(),
        ZopeDocFileSuite('pages.txt', package='Products.Five.browser.tests'),
        FunctionalDocFileSuite('pages_ftest.txt',
                               package='Products.Five.browser.tests')
        ))
    return suite

if __name__ == '__main__':
    framework()

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
"""Broken-object tests

$Id: tests.py 28984 2005-01-30 19:13:23Z gintautasm $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite

def test_annotations():
    """Broken objects may have attribute annotations

    If they do, we can access them::

      >>> from zope.app.broken.broken import Broken
      >>> b = Broken()
      >>> b.__setstate__({'__annotations__': {'foo.bar': 42}})
      >>> b['foo.bar']
      42
      >>> b.get('foo.bar')
      42

      Missing keys are handled as expected:

      >>> b['foo.baz']
      Traceback (most recent call last):
      ...
      KeyError: 'foo.baz'

      >>> b.get('foo.baz')

      It is an error to modify annotations:

      >>> b['foo.baz'] = []
      Traceback (most recent call last):
      ...
      BrokenModified: Can't modify broken objects

      >>> del b['foo.bar']
      Traceback (most recent call last):
      ...
      BrokenModified: Can't modify broken objects

    If there are no annotation data, then, obviously, there are no annotations:

      >>> b = Broken()
      >>> b['foo.bar']
      Traceback (most recent call last):
      ...
      KeyError: 'foo.bar'

      >>> b.get('foo.bar')

      >>> b['foo.bar'] = []
      Traceback (most recent call last):
      ...
      BrokenModified: Can't modify broken objects

      >>> del b['foo.bar']
      Traceback (most recent call last):
      ...
      BrokenModified: Can't modify broken objects


    Cleanup:

      >>> import ZODB.broken
      >>> ZODB.broken.broken_cache.clear()

    """

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        DocTestSuite('zope.app.broken.broken'),
        ))

if __name__ == '__main__': unittest.main()

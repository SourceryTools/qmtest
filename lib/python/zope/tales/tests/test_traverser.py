"""
Tests for zope.tales.expressions.simpleTraverse

$Id: test_traverser.py 40270 2005-11-20 13:23:13Z shh $
"""

from unittest import TestCase, TestSuite, makeSuite, main
from zope.tales.expressions import simpleTraverse


class AttrTraversable(object):
    """Traversable by attribute access"""
    attr = 'foo'

class ItemTraversable(object):
    """Traversable by item access"""
    def __getitem__(self, name):
        if name == 'attr':
            return 'foo'
        raise KeyError, name

class AllTraversable(AttrTraversable, ItemTraversable):
    """Traversable by attribute and item access"""
    pass


_marker = object()

def getitem(ob, name, default=_marker):
    """Helper a la getattr(ob, name, default)."""
    try:
        item = ob[name]
    except KeyError:
        if default is not _marker:
            return default
        raise KeyError, name
    else:
        return item


class TraverserTests(TestCase):

    def testGetItem(self):
        # getitem helper should behave like __getitem__
        ob = {'attr': 'foo'}
        self.assertEqual(getitem(ob, 'attr', None), 'foo')
        self.assertEqual(getitem(ob, 'attr'), 'foo')
        self.assertEqual(getitem(ob, 'missing_attr', None), None)
        self.assertRaises(KeyError, getitem, ob, 'missing_attr')
        self.assertRaises(TypeError, getitem, object(), 'attr')

    def testAttrTraversable(self):
        # An object without __getitem__ should raise AttributeError
        # for missing attribute.
        ob = AttrTraversable()
        self.assertEqual(getattr(ob, 'attr', None), 'foo')
        self.assertRaises(AttributeError, getattr, ob, 'missing_attr')

    def testItemTraversable(self):
        # An object with __getitem__ (but without attr) should raise
        # KeyError for missing attribute.
        ob = ItemTraversable()
        self.assertEqual(getitem(ob, 'attr', None), 'foo')
        self.assertRaises(KeyError, getitem, ob, 'missing_attr')

    def testAllTraversable(self):
        # An object with attr and __getitem__ should raise either
        # exception, depending on method of access.
        ob = AllTraversable()
        self.assertEqual(getattr(ob, 'attr', None), 'foo')
        self.assertRaises(AttributeError, getattr, ob, 'missing_attr')
        self.assertEqual(getitem(ob, 'attr', None), 'foo')
        self.assertRaises(KeyError, getitem, ob, 'missing_attr')

    def testTraverseEmptyPath(self):
        # simpleTraverse should return the original object if the path is emtpy
        ob = object()
        self.assertEqual(simpleTraverse(ob, [], None), ob)

    def testTraverseByAttr(self):
        # simpleTraverse should find attr through attribute access
        ob = AttrTraversable()
        self.assertEqual(simpleTraverse(ob, ['attr'], None), 'foo')

    def testTraverseByMissingAttr(self):
        # simpleTraverse should raise AttributeError
        ob = AttrTraversable()
        # Here lurks the bug (unexpected NamError raised)
        self.assertRaises(AttributeError, simpleTraverse, ob, ['missing_attr'], None)

    def testTraverseByItem(self):
        # simpleTraverse should find attr through item access
        ob = ItemTraversable()
        self.assertEqual(simpleTraverse(ob, ['attr'], None), 'foo')

    def testTraverseByMissingItem(self):
        # simpleTraverse should raise KeyError
        ob = ItemTraversable()
        self.assertRaises(KeyError, simpleTraverse, ob, ['missing_attr'], None)

    def testTraverseByAll(self):
        # simpleTraverse should find attr through attribute access
        ob = AllTraversable()
        self.assertEqual(simpleTraverse(ob, ['attr'], None), 'foo')

    def testTraverseByMissingAll(self):
        # simpleTraverse should raise KeyError (because ob implements __getitem__)
        ob = AllTraversable()
        self.assertRaises(KeyError, simpleTraverse, ob, ['missing_attr'], None)


def test_suite():
    return TestSuite((
        makeSuite(TraverserTests),
    ))


if __name__ == '__main__':
    main(defaultTest='test_suite')


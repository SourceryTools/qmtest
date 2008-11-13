import unittest
import zope.testing

def test_suite():
    return unittest.TestSuite((
        zope.testing.doctest.DocFileSuite('minmax.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

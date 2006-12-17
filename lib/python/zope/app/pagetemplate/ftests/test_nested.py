"""Test that nested macro references do the right thing.
"""
__docformat__ = "reStructuredText"

import zope.app.testing.functional


def test_suite():
    return zope.app.testing.functional.FunctionalDocFileSuite(
        "test_nested.txt")

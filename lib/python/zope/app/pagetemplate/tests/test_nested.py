"""Test that nested macro references do the right thing.
"""
__docformat__ = "reStructuredText"

import zope.app.testing.functional
from zope.app.pagetemplate.testing import PageTemplateLayer

def test_suite():
    suite = zope.app.testing.functional.FunctionalDocFileSuite(
        "test_nested.txt")
    suite.layer = PageTemplateLayer
    return suite

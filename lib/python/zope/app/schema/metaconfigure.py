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
"""ZCML special vocabulary directive handlers

$Id: metaconfigure.py 67630 2006-04-27 00:54:03Z jim $
"""
import warnings
from zope.interface import directlyProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.component.zcml import utility

class FactoryKeywordPasser(object):
    """Helper that passes additional keywords to the actual factory."""

    def __init__(self, factory, kwargs):
        self.factory = factory
        self.kwargs = kwargs

    def __call__(self, object):
        return self.factory(object, **self.kwargs)


# BBB 2006/02/24, to be removed after 12 months
def vocabulary(_context, name, factory, **kw):
    try:
        dottedname = factory.__module__ + "." + factory.__name__
    except AttributeError:
        dottedname = '...'
    warnings.warn_explicit(
        "The 'vocabulary' directive has been deprecated and will be "
        "removed in Zope 3.5.  Use the 'utility' directive instead to "
        "register the class as a named utility:\n"
        '  <utility\n'
        '      provides="zope.schema.interfaces.IVocabularyFactory"\n'
        '      component="%s"\n'
        '      name="%s"\n'
        '      />' % (dottedname, name),
        DeprecationWarning, _context.info.file, _context.info.line)
    if kw:
        factory = FactoryKeywordPasser(factory, kw)
    directlyProvides(factory, IVocabularyFactory)
    utility(_context, IVocabularyFactory, factory, name=name)

##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Vocabulary for the Source Type Registry

$Id: vocabulary.py 67630 2006-04-27 00:54:03Z jim $
"""
import zope.component
from zope.interface import alsoProvides
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IVocabularyFactory
from zope.app.renderer.interfaces import ISource

def SourceTypeVocabulary(context):
    return SimpleVocabulary(
        [SimpleTerm(name, title=factory.title) for name, factory in 
         zope.component.getFactoriesFor(ISource)])

alsoProvides(SourceTypeVocabulary, IVocabularyFactory)
